#!/usr/bin/env python3
import random
import urllib.parse
import urllib.request
import sys
from bs4 import BeautifulSoup

seed = "http://dib.cambridge.org/"

def fetch(link):
    try:
        req = urllib.request.Request(link)
        handler = urllib.request.urlopen( req )        
        page = handler.read().decode( 'utf-8' )
        return page
    except urllib.error.HTTPError as e:
        print(e)

def scrape(root, links):    
    for i in range(len(links)):        
        print("{:5}/{} :: {}".format(i+1,len(links),links[i]))
        qs = urllib.parse.parse_qs(urllib.parse.urlsplit(links[i]).query)        
        article = qs['articleId'][0]
        content = fetch( root + links[i] )
        
        if content == None:
            continue
        
        with open("{}.html".format(article), "w") as f:
            f.write(content)

def load_links(fname):
    with open(fname,"r") as f:
        return f.read().split("\n")[:-1]

def main(arg):
    links = load_links(arg)
    scrape( seed, links )

if __name__=="__main__":
    main(sys.argv[1])
