#!/usr/bin/env python3
import json
from optparse import OptionParser
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, FOAF, RDFS, NamespaceManager
from datetime import date

class App:
	def __init__(self):
		
		self.__process_args()		

		self.__initialize_graph()

		self.__load_data()
		
	def __process_args(self):
		parser = OptionParser(usage="usage: %prog [options] FILE")
	
		parser.add_option("-o", "--output",
			action="store", type="string", dest="output", default="graph.ttl",
			help="file to which the updated graph should be written"
		)

		parser.add_option("-f", "--format",
			action="store", type="string", dest="format", default="turtle",
			help="output format of the application (turtle, n3, nquads) "
		)

		parser.add_option("-e", "--external",
			action="store", type="string", dest="external", default=None,
			help="Source of DBpedia links which are sameAs entities in dataset"
		)

		parser.add_option("-F", "--filter",
			action="store", type="string", dest="filter", default=None,
			help="List of IDs that should be included in the knowledge base"
		)

		(self.options, self.args) = parser.parse_args()

		if self.options.filter == None:
			self.filter = [] 
		else:
			with open(self.options.filter, "r") as f:
				self.filter = [ line.strip() for line in f ]

		if len(self.args) < 1:
			parser.print_help()

	def __initialize_graph(self):
		self.dbo = Namespace("http://dbpedia.org/ontology/")		
		self.owl = Namespace("http://www.w3.org/2002/07/owl#")
		self.crm = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
		self.odnb = Namespace("http://adaptcentre.ie/odnb/")
		self.odnb_events = Namespace("http://adaptcentre.ie/odnb/events")
		self.odnb_events_time = Namespace("http://adaptcentre.ie/odnb/time")

		namespace_manager = NamespaceManager(Graph())
		namespace_manager.bind('dbo', self.dbo, override=False)
		namespace_manager.bind('owl', self.owl, override=False)
		namespace_manager.bind('odnb', self.odnb, override=False)		
		namespace_manager.bind('crm', self.crm, override=False)
		namespace_manager.bind('foaf', FOAF, override=False)
		
		self.graph = Graph()
		self.graph.namespace_manager = namespace_manager

	def __load_data(self):
		self.entities = {}
		with open(self.args[0], "r") as f:
			for line in f:
				entity = json.loads(line)
				if len(self.filter) > 0 and entity["article_id"] not in self.filter:
					continue

				entity["ont_id"] = "{}_{}".format(
						entity["givenName"].replace(" ", "_").replace("'", "_"), 
						entity["article_id"]
					)
				entity["uri"] = URIRef(self.odnb[entity["ont_id"]])
				self.entities[entity["article_id"]] = entity

	def __create_or_add_timespan( self, start_year, end_year ):
		start = date(start_year, 1, 1).strftime('%Y-%m-%d')
		end   = date(end_year, 12, 31).strftime('%Y-%m-%d')

		ts_uri = URIRef(self.odnb_events_time[start + "_" + end])
		self.graph.add((ts_uri, RDF.type, self.crm["E52_Time-Span"]))
		self.graph.add((ts_uri, self.crm.P82a_begin_of_the_begin, Literal(date(start_year, 1, 1))))
		self.graph.add((ts_uri, self.crm.P82b_end_of_the_end, Literal(date(end_year, 12, 31))))

		return ts_uri

	def __add_birth_event( self, entity ):
		birth_uri = URIRef(self.odnb_events["birth_" + entity["article_id"]])
		self.graph.add((birth_uri, RDF.type, self.crm.E67_Birth))
		self.graph.add((birth_uri, self.crm.P98_brought_into_life, entity["uri"]))

		ts = self.__create_or_add_timespan(entity["born_low"], entity["born_high"])
		self.graph.add((birth_uri, self.crm["P4_has_time-span"], ts))

	def __add_death_event( self, entity ):
		death_uri = URIRef(self.odnb_events["death_" + entity["article_id"]])
		self.graph.add((death_uri, RDF.type, self.crm.E69_Death))
		self.graph.add((death_uri, self.crm.P100_was_death_of, entity["uri"]))

		ts = self.__create_or_add_timespan(entity["died_low"], entity["died_high"])
		self.graph.add((death_uri, self.crm["P4_has_time-span"], ts))

	def __add_floruit_event( self, entity ):
		floruit_uri = URIRef(self.odnb_events["period_" + entity["article_id"]])
		self.graph.add((floruit_uri, RDF.type, self.crm.E4_Period))
		self.graph.add((entity["uri"], self.crm.P12_occurred_in_the_presence_of, floruit_uri))

		ts = self.__create_or_add_timespan(entity["floruit_low"], entity["floruit_high"])
		self.graph.add((floruit_uri, self.crm["P4_has_time-span"], ts))

	def __add_to_graph(self, entity):
		 
		surname = Literal(entity["surname"])
		name = Literal(entity["givenName"])
		if len(entity["forename"]) > 0:
			forename = Literal(entity["forename"])			
			self.graph.add(( entity["uri"], FOAF.givenName, forename))

		# Add the data about the entity to the graph
		self.graph.add(( entity["uri"], RDF.type, self.dbo.Person ))
		self.graph.add(( entity["uri"], RDF.type, FOAF.Person ))
		self.graph.add(( entity["uri"], RDF.type, self.crm.E21_Person ))
		
		self.graph.add(( entity["uri"], FOAF.familyName, surname))		
		self.graph.add(( entity["uri"], FOAF.name, name))

		for label in entity["labels"]:
			self.graph.add((entity["uri"], RDFS.label, Literal(label)))

		for nickname in entity["nicknames"]:
			self.graph.add((entity["uri"], FOAF.nickname, Literal(nickname)))

		for link in entity['article_links']:			
			if link['article_id'] in self.entities:
				target = self.entities[link['article_id']]
				self.graph.add((entity["uri"], self.dbo.related, target['uri']))
				# self.graph.add((target['uri'], self.dbo.related, entity["uri"]))				
				# self.graph.add((target['uri'], RDFS.label, Literal(link['anchor_text'])))

		if entity['born_low'] > 0 and entity['floruit'] < 0:
			born = Literal(date(entity['born_low'], 1, 1))
			self.graph.add((entity["uri"], self.dbo.birthYear, born))
			self.__add_birth_event(entity)
		
		if entity['died_high'] > 0 and entity['floruit_low'] < 0:
			died = Literal(date(entity['died_high'], 1, 1))
			self.graph.add((entity["uri"], self.dbo.deathYear, died))
			self.__add_death_event(entity)
		
		if entity['floruit_low'] > 0:
			self.__add_floruit_event(entity)

		# This needs to be captured when scraping and extracting
		# self.graph.add((entity["uri"], FOAF.primaryTopic, Literal("http://www.oxforddnb.com/view/10.1093/ref:odnb/9780198614128.001.0001/odnb-9780198614128-e-{}".format(entity["article_id"])) ))

	def __graph2file(self):
		self.graph.serialize(destination=self.options.output, 
			format=self.options.format)

	def __build_same_as_links(self, external):
		with open(external, "r") as f:
			for line in f:
				entity_id, uri = line.strip().split(" ", 1)
				if uri != "NIL" and entity_id in self.entities:
					entity = self.entities[entity_id]
					self.graph.add((entity["uri"], self.owl.sameAs, URIRef(uri) )) 

	def run(self):
		for entity_id in self.entities:
			self.__add_to_graph(self.entities[entity_id])

		if self.options.external != None:
			self.__build_same_as_links(self.options.external)

		self.__graph2file()

if __name__=="__main__":
	App().run()
