#!/usr/bin/env python3

import sys
import json
from collections import defaultdict

def best_match(doi, doi2dbp, mappings, threshold):
    for m in doi2dbp[doi]:
        dbpid = m[0]
        weight = m[1]

        if weight < threshold:
            return

        if mappings[dbpid] == None:
            mappings[dbpid] = [doi, weight]
            break
        else:
            if weight > mappings[dbpid][1]:                
                tmp = mappings[dbpid][0]
                mappings[dbpid][0] = doi
                mappings[dbpid][1] = weight
                best_match(tmp, doi2dbp, mappings, threshold)
                break

if __name__=="__main__":
    with open(sys.argv[1], "r") as f:
        data = [ json.loads(line) for line in f ]

        doi2dbp = defaultdict(list)

        for datum in data:
            doi2dbp[datum["doi"]] = datum["dbpedia"]

        mappings = defaultdict(lambda: None)
        
        for doi in doi2dbp:
            best_match(doi, doi2dbp, mappings, 0.55)

        mappings = { v[0] : k for k, v in mappings.items() if v != None }

        for doi in doi2dbp:
            link = "NIL"
            if doi in mappings:
                link = mappings[doi]

            print(doi, link)
        
