#!/usr/bin/env python3

import os
import sys

from bs4 import BeautifulSoup

def main():

    for fname in sys.argv[1:]:
        soup = BeautifulSoup(open(fname), "html.parser")
        docid = os.path.splitext(os.path.basename(fname))[0]
        elements = soup.find_all("li", {"class":"doi"})

        uri = "NONE"
        if len(elements) > 0:
            uri = "\t".join([ e.text for e in elements ])
        print( "{}\t{}".format(docid, uri) )

if __name__ == "__main__":
    main()
