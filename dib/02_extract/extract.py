#!/usr/bin/env python3
import re
import sys
import json
import nltk
import logging
import urllib.parse
import multiprocessing
from optparse import OptionParser
from bs4 import BeautifulSoup
from os.path import basename, splitext

from entity_processor import Entity
from config import HONORIFICS, TITLES, NORMALS

class EntityEncoder(json.JSONEncoder):
    def default(self, e):
        return {
        	"title"           : e.title,
        	"article_id"      : e.article_id,
        	"article_links"   : e.article_links,
        	"forename"        : e.forename,
        	"surname"         : e.surname,
        	"givenName"       : e.given_name,
        	# "altnames"        : e.altnames,
        	"nicknames"       : e.nicknames,
        	"labels"          : e.labels,
        	# "content"         : e.content,
        	# "first_paragraph" : e.first_paragraph,
        	# "first_sentence"  : e.first_sentence,
        	"born"			  : e.born,
        	"died"            : e.died,
        	"born_low"		  : e.born_low,
        	"born_high"	      : e.born_high,
        	"died_low"        : e.died_low,
        	"died_high"       : e.died_high,
        	"floruit"         : e.floruit,
        	"floruit_low"     : e.floruit_low,
        	"floruit_high"    : e.floruit_high,
        	"fuzzy_date"      : e.fuzzy,
        	# "titles"          : e.titles,
			# "honorifics"      : e.honorifics,
			# "locations"       : e.locations
        }

# Main application class. Handles command line arguments and spins out worker
# processes as requested to manage each of the input articles
class EntityApp:
	def __init__(self):
		# Parser for handling command line arguments
		parser = OptionParser(usage="usage: %prog [options] FILE ...")	
		
		# File to which the extracted entities will be written
		parser.add_option("-o", "--output",
                  	action="store", type="string", dest="output", 
                  	default="entities.json",
	                help="file to which the entities should be written")

		# integer argument for controlling parallelisation 
		# 4 processes by default
		parser.add_option("-p", "--processes",
                  	action="store", type="int", dest="processes", default=4,
	                help="number of parallel processes to use for extraction")

		# Used to determine the logging level of the output
		# WARNING when false. INFO when true
		parser.add_option("-v", "--verbose",
		                  action="store_true", dest="verbose", default=False,
		                  help="verbose program output")

		# Parse user inputs using OptionParser
		(self.options, self.args) = parser.parse_args()

		# Enable logging so we can monitor progress
		logging.basicConfig(
			format='%(asctime)s : %(levelname)s : %(message)s',
			level = logging.INFO if self.options.verbose else logging.WARNING
		)	

		# If no input was given, print usage information and quit the program
		if len(self.args) < 1:
			parser.print_help()
			exit()

		self.extracted = []

		# We could be using the length of the args list quite a bit. So lets
		# just store it
		self.num_inputs = len(self.args)

	def _write_results(self):
		with open(self.options.output, "w") as f:
			for e in self.extracted:
				f.write("{}\n".format(json.dumps(e, cls=EntityEncoder)))

	def run(self):
		if self.options.processes < 2:
			self.extracted = [Entity(arg) for arg in self.args]
		else:
			# The Pool resource in multiprocessing makes parallelising this 
			# kind of problem ridiculously easy
			p = multiprocessing.Pool(self.options.processes)
			self.extracted = p.map(Entity, self.args)

		# output our extracted entities to the destination file
		self._write_results()

# Boiler plate python if __name__ == "__main__" code.
# Actual program runs from the EntityApp class
if __name__=="__main__":
	EntityApp().run()	