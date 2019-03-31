#!/usr/bin/env python3

import re
import math
import json
import logging
import itertools
import urllib.parse
import networkx as nx
from bs4 import BeautifulSoup
from os.path import basename, splitext
from pyjarowinkler.distance import get_jaro_distance
from config import HONORIFICS, TITLES, LOCATIONS, NORMALS

class Entity:
    
    def __init__(self, fname):       
        # Initialize everything that this class is going to try to extract
        self.fname           = fname # Name of the file being processed
        self.title           = ""    # Title of the article     
        self.article_id      = ""    # ID of article on Dictionary site
        self.article_links   = []    # Anchor tags in the body of the article
        self.forename        = ""    # 
        self.surname         = ""    #
        self.altnames        = []    #
        self.nicknames       = []
        self.given_name      = ""
        self.born            = -1
        self.died            = -1
        self.born_low        = -1
        self.born_high       = -1
        self.died_low        = -1
        self.died_high       = -1
        self.floruit         = -1
        self.floruit_low     = -1
        self.floruit_high    = -1
        self.fuzzy           = False
        self.titles          = []
        self.honorifics      = []
        self.locations       = []
        self.first_sentence  = ""
        self.content         = ""
        self.first_paragraph = ""
        self.pos_tags        = []
        self.chunks          = []
        
        self.__info("Processing")

        soup = self.__fname2soup(fname)
        
        self.__extract_article_id()
        self.__extract_title(soup)
        self.__extract_links(soup)
        self.__extract_text_extracts(soup)
        self.__extract_born_death_dates()
        self.__extract_names()

        corrected_name = re.sub(r"\s+", " ", " ".join(re.compile(r",(?![^\(]+\))").split(self.title, 1)[::-1]).strip())
        corrected_name = re.sub("\s+", " ", re.sub(r"\([^\)]+\)", "", corrected_name)).strip()
        self.given_name = corrected_name
        # self.__transform_and_append(name, self.labels)

        nameparts = self.__apply_normalization_patterns(corrected_name)
        nameparts = self.__collapse_locations(nameparts)
        nameparts = self.__collapse_titles_honorifics(nameparts)
        nameparts = nameparts.split()
        
        if len(nameparts) > 1:
            self.surname = nameparts[-1]
            self.forename = nameparts[0]
        elif len(nameparts) > 0:
            self.surname = nameparts[0]
            self.forename = ""
        else:
            self.surname = self.forename = ""

        self.nameparts = nameparts

        self.labels = self.__generate_name_permutations(self.title)

        self.location = ""
        for pattern in LOCATIONS:
            location = re.search(pattern, self.title)
            if location != None:
                self.location = location.group(0)[3:]
    
    def __fname2soup(self, fname):
        with open(fname, "r") as f:
            return BeautifulSoup(f.read(), "lxml")

    def __generate_name_permutations(self, name):
        permutations = []

        nameparts = re.compile(r",(?![^\(]+\))").split(name, 1)[::-1]
        nameparts = [ part.strip() for part in nameparts ]

        if len(nameparts) > 1:
            surname_parts = nameparts[1]
            forename_parts = nameparts[0]
        else:
            surname_parts = nameparts[0]
            forename_parts = ""

        alt_forenames = re.findall("(?<=\()[^\)]+(?=\))", forename_parts)
        alt_surnames  = re.findall("(?<=\()[^\)]+(?=\))", surname_parts)

        alt_forenames = [ altname.strip() for np in alt_forenames for altname in re.split(r",|;", np) ]
        alt_surnames  = [ altname.strip() for np in alt_surnames for altname in re.split(r",|;", np) ]
        alt_forenames.append(self.forename)
        alt_surnames.append(self.surname)

        self.nicknames = [ nickname[1:-1] for nickname in alt_forenames + alt_surnames if re.match(r"^[\"'].+[\"']$", nickname) ]
        permutations += self.nicknames
        alt_forenames = [ re.sub(r"^[\"']?([^'\"]+)[\"']?$", r"\1", altname.strip()) for altname in alt_forenames ]
        alt_surnames = [ re.sub(r"^[\"']?([^'\"]+)[\"']?$", r"\1", altname.strip()) for altname in alt_surnames ]

        altnames = list(itertools.product(alt_forenames, alt_surnames))
        altnames = [ re.sub(r"\s+", " ", " ".join(altname).strip()) for altname in altnames ]

        name = re.sub(r"\s+", " ", " ".join(nameparts).strip())
        
        self.__transform_and_append(name, permutations)
        
        for altname in altnames:
            self.__transform_and_append(altname, permutations)

        self.__transform_and_append(
            name, 
            permutations, 
            transf = lambda x: re.sub("\s+", " ", re.sub(r"\([^\)]+\)", "", name)).strip()
        )
        

        #for perm in permutations:
        #    self.__transform_and_append(
        #        perm, 
        #        permutations, 
        #        transf = self.__apply_normalization_patterns
        #    )   

        for perm in permutations:
            # collapse titles "Sir John of Kinsale" to "John of Kinsale"
            self.__transform_and_append(
                perm, 
                permutations, 
                transf = self.__collapse_titles_honorifics
            )

        for perm in permutations:
            # collapse locations "Sir John of Kinsale" to "Sir John"
            self.__transform_and_append(
                perm,
                permutations,
                transf = self.__collapse_locations
            )

        # Filter permutations that are comprised only of titles or locations
        permutations = [ permutation for permutation in permutations if not self.__matches_pattern_set(permutation, HONORIFICS) ]
        permutations = [ permutation for permutation in permutations if not self.__matches_pattern_set(permutation, TITLES) ]
        permutations = [ permutation for permutation in permutations if not self.__matches_pattern_set(permutation, LOCATIONS) ]

        return permutations

    def __transform_and_append(self, label, permutations, transf = lambda x: x):
        transformation = transf(label)
        if transformation not in permutations and len(transformation) > 0:
            permutations.append(transformation)

    def __apply_normalization_patterns( self, name ):
        
        for pattern, sub in NORMALS:            
            newname = re.sub(pattern, sub, name)
            #if name != newname:
            #   self.__info("Normalizing '{}' : '{}'".format(name, newname))
            name = newname

        return name

    def __collapse_locations( self, name ):
        for pattern in LOCATIONS:           
            name = re.sub("\s+", " ", re.sub(pattern, "", name)).strip()

        return name

    def __collapse_titles_honorifics( self, name ):
        nameparts = name.split(" ")
        nameparts = [ part for part in nameparts if not self.__matches_pattern_set(part, HONORIFICS) ]
        nameparts = [ part for part in nameparts if not self.__matches_pattern_set(part, TITLES) ]
        return " ".join(nameparts)

    def __matches_pattern_set( self, term, pattern_set ):
        for pattern in pattern_set:
            if re.match(pattern, term, re.IGNORECASE):
                return True
        return False

    def __extract_article_id(self):
        self.article_id = splitext(basename(self.fname))[0]

    def __extract_title(self, soup):
        self.title = self.__compress_space(soup.find("title").getText())

        if len(self.title) < 1:
            self.__warn("Blank title")

    def __compress_space(self, text):
        return re.sub(" +", " ", text.strip())

    def __extract_names(self):
        re_between_parens = re.compile("\([^\)]*\)")
        names = re.sub(re_between_parens, "", self.title).split(",")
        # self.forename = self._compress_space(names[1] if len(names) > 1 else names[0])
        # self.surname  = self._compress_space(names[0] if len(names) > 1 else "")

        # flip name order (forename first followed by surname)
        names = [ self.__compress_space(n) for n in names[::-1] ]

        # Easier to do pattern matching on full name in correct word order
        fullname = " ".join(names).strip()

        if len(fullname) <= 0:
            self.__warn("Empty name")
            return

        # Apply normalization regexps to name
        # self.normalize_strings(fullname)

        # name_parts can be empty after this
        name_parts = fullname.split()
                
        if len(self.altnames) > 1:
            self.forename = self.altnames[0]
            self.surname = self.altnames[-1]
            self.altnames = self.altnames[1:-1]
        elif len(self.altnames) == 1:
            self.surname = self.altnames[0]
            self.altnames = []

        parens = [ alt[1:-1] for alt in re.findall(re_between_parens, self.title) ]

        self.nicknames = []
        for p in parens:
            self.nicknames += re.findall(r"(?<=\')[^\']*(?=\')", p)
            s = re.sub(r"\'[^\']*\'", "", p).strip()
            if len(s) > 0:
                self.altnames.append(s)

    def __parse_date_part(self, date_part):
        date = re.search(r"[0-9/]+", date_part).group()
        date = re.compile(r"/|×").split(date)

        date_low = date[0]
        date_high = date[-1]

        diff = len(date_low)-len(date_high)
        date_high = date_low[:diff] + date_high

        return int(date_low), int(date_high)

    def __fix_century(self, date_low, date_high):
        if date_high < date_low:
            date_high += (date_low//100)*100
        return date_high

    def __extract_born_death_dates(self):                
        match = re.search("(?<=\()([^\)]*[0-9])", self.first_paragraph)
        
        if match == None:            
            return

        dates = match.group().split("-")

        if len(dates) > 1:
            self.born, self.died = dates[0], dates[1]
            self.born_low, self.born_high = self.__parse_date_part(self.born)
            self.died_low, self.died_high = self.__parse_date_part(self.died)
            
            self.died_low  = self.__fix_century(self.born_low, self.died_low)
            self.died_high = self.__fix_century(self.born_high, self.died_high)
        else:            
            if "d." in dates[0]:
                self.died_low, self.died_high = self.__parse_date_part(dates[0])
            else:
                self.born_low, self.born_high = self.__parse_date_part(dates[0])           
        
        if self.died_low > 0 and self.died_low <= 10:
            self.died_low = (self.died_low - 1) * 100
            self.died_high = self.died_low + 100
            self.floruit_low  = self.died_low
            self.floruit_high = self.died_high

        if self.born_low > 0 and self.born_low <= 10:
            self.born_low     = (self.born_low - 1) * 100
            self.born_high    = self.born_low + 100
            self.floruit_low  = self.born_low
            self.floruit_high = self.born_high

        self.fuzzy = re.search( r"c\.|f\.|fl\.|a\.|/|×|\?|p\.", match.group() ) != None

        print( "{:<24} | {:>4} | {:>4} | {:>4} | {:>4} | {:>4} | {} ".format(match.group(), self.born_low, self.born_high, self.died_low, self.died_high, self.floruit, self.fuzzy ))

    def __extract_links(self, soup):
        body = soup.find('body')
        if body != None:
            self.article_links = [ 
                { 
                    "article_id"  : self.__article_id_from_link(link["href"]), 
                    "anchor_text" : self.__compress_space(link.getText()) 
                } 
                for link in body.find_all('a') if link.has_attr("href") 
            ]

    def __article_id_from_link(self, link):
        url = urllib.parse.urlparse(link)
        qs = urllib.parse.parse_qs(url.query)       
        return qs['articleId'][0] if 'articleId' in qs else None

    def __extract_text_extracts(self, soup):
        body = soup.find("body")        
        pars = [par for par in [self.__compress_space(p.get_text()) for p in body.find_all("p")] if len(par) != 0]
        self.first_paragraph = pars[0]
        self.content = "\n\n".join(pars)

    def __debug(self, msg):
        logging.debug("{:>4}: {}".format(self.fname, msg))

    def __info(self, msg):
        logging.info("{:>4}: {}".format(self.fname, msg))

    def __warn(self, msg):
        logging.warn("{:>4}: {}".format(self.fname, msg))

    def __error(self, msg):
        logging.error("{:>4}: {}".format(self.fname, msg))
