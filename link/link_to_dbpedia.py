#!/usr/bin/env python3

import re
import sys
import csv
import json
import pysolr
import gensim
import itertools
import logging

import networkx as nx

from nltk.corpus import stopwords
from optparse import OptionParser
from gensim.similarities import WmdSimilarity
from gensim.corpora.wikicorpus import tokenize
from pyjarowinkler.distance import get_jaro_distance

stopwords = stopwords.words('english')

def similarity( t1, t2 ):
		return get_jaro_distance(t1, t2)

def find_optimal_match(  nameparts1, nameparts2, sim_thresh = 0 ):
	graph = nx.Graph()
	graph.add_nodes_from(["1_{}".format(i) for i in nameparts1], bipartite=0)
	graph.add_nodes_from(["2_{}".format(i) for i in nameparts2], bipartite=1)

	for i in nameparts1:
		edges = [ ("1_{}".format(i), "2_{}".format(j), similarity(i, j)) for j in nameparts2 ]
		edges = [ edge for edge in edges if edge[2] > sim_thresh ]
		graph.add_weighted_edges_from(edges)

	pairings = nx.max_weight_matching(graph)
	result = []
	matched = []

	for pairing in pairings:
		match = { p.split("_")[0]: p.split("_")[1] for p in pairing }
		result.append( (match["1"], match["2"], graph[pairing[0]][pairing[1]]["weight"]) )
		matched.append(match["1"])
		matched.append(match["2"])

	result += [ (namepart, None, 0) for namepart in nameparts1 if namepart not in matched]
	result += [ (namepart, None, 0) for namepart in nameparts2 if namepart not in matched]

	return result

def name_similarity( n1, n2 ):
	np1 = stopword_tokenize(n1)
	np2 = stopword_tokenize(n2)

	optimal_match = find_optimal_match(n1, n2)

	# Generalized Mongue-Elkan Method for Approximate Text String Comparison
	total_sim = sum( s[2]**2 for s in optimal_match )
	total_sim = (total_sim/len(optimal_match))**(1/2)

	return total_sim

def load_model(path):
	model = gensim.models.Word2Vec.load(path)	
	return model

def connect_solr(path, timeout=10000):
	solr = pysolr.Solr(path, timeout=timeout)
	return solr

def stopword_tokenize( text ):
	return [ t for t in tokenize(text) if t not in stopwords ]

def link( person, model, solr, rows=10, alpha=0.1, beta=0.9 ):
	logging.info("Processing DocID {}".format(person["id"]))
	# Remove special characters from the name that might mess with Solr
	name = re.sub("[(\[\]\):]", " ", person["name"])
	# Don't bother searching if name is empty string
	if len(name.strip()) < 1:
		logging.info("Name field is empty.")
		return list()

	# Execute name as query against solr. Boost on title/altname matches
	results = solr.search(
		"title:{0}^5 OR altnames:{0}^3 OR text:{0}".format(name), 
		rows=rows
	)

	# Tokenize the input essay about person
	tokens = stopword_tokenize(person["text"])
	# Get top N results from solr result generator. Some results might not have
	# associated text, so add a filter for that
	top_n = [ item for item in itertools.islice(results, rows) if "text" in item ]
	# Tokenize the text from each of the solr results
	text = [ stopword_tokenize(item["text"]) for item in top_n ]
	# Build a WMD similarity index from the Solr text results
	comparator = WmdSimilarity(text, model)
	# Compute the similarity between essay and all solr results
	content_similarities = comparator[tokens]
	# Extract surface form from title. Strip out anything in parentheses
	titles = [ re.sub("\([^\)]+\)", "", item["title"]).strip() for item in top_n ]
	# Compute surface form similarity between title and person name
	name_similarities = [ name_similarity(sf, person["name"]) for sf in titles ]
	# compute final weighted similarities
	similarities = [ alpha * s[0] + beta * s[1] for s in list(zip(name_similarities, content_similarities)) ]
	# Combine sims and solr results, sort based on WMD similarity and return
	result = list(zip(top_n, similarities))

	return sorted(result, key=lambda x: -x[1])

def process_args():
	parser = OptionParser(usage="usage: %prog [options] FILE")

	parser.add_option("-m", "--model",
		action="store", type="string", dest="model", default="w2v.model",
		help="Path to Word2Vec model"
	)

	parser.add_option("-o", "--output",
		action="store", type="string", dest="output", default="output.json",
		help="Name of output file"
	)

	parser.add_option("-l", "--log",
		action="store", type="string", dest="log",
		default=None,
		help="File to which logs should be written"
	)

	parser.add_option("-s", "--solr",
		action="store", type="string", dest="solr",
		default="http://localhost:8983/solr/wiki_people",
		help="Path to Solr API for querying"
	)

	options, args = parser.parse_args()

	if len(args) < 1:
		parser.print_help()
		exit()

	return options, args

def main():
	options, args = process_args()

	if options.log != None:
		logging.basicConfig(
			format='%(asctime)s : %(levelname)s : %(message)s', 
			filename=options.log,
			filemode='w',
			level=logging.INFO
		)
	else:
		logging.basicConfig(
			format='%(asctime)s : %(levelname)s : %(message)s',
			level=logging.INFO
		)

	model = load_model(options.model)
	solr = connect_solr(options.solr)

	out = open(options.output, "w", 1)
	with open(args[0]) as f:
		for line in f:
			person = json.loads(line)
			matches = link(person, model, solr)
			matches = [ (item[0]["dbpedia"], item[1]) for item in matches ]
			person["dbpedia"] = matches
			out.write("{}\n".format(json.dumps(person)))

	out.close()

if __name__ == "__main__":
	main()