#!/usr/bin/env python3
import random
import urllib.parse
import urllib.request
import sys
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

seed = "http://www.oxforddnb.com"

def fetch(link):
    try:
        headers = {
            'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        }
        req = urllib.request.Request(link, "".encode("ascii"), headers)
        handler = urllib.request.urlopen( req )        
        page = handler.read().decode( 'utf-8' )
        return page
    except urllib.error.HTTPError as e:
        print(e, link)

def scrape(root, links):    
    for i, link in enumerate(links):
        print("{:5}/{} :: {}".format(i+1, len(links), links[i]))
        et = ET.fromstring(link)
        content = fetch( root + et.attrib["href"] )
        if content == None:
            continue
        with open("{}.html".format(i), "w") as f:
            f.write(content)

def load_links(fname):
    with open(fname,"r") as f:
        return f.read().split("\n")[:-1]

def main(arg):
    links = load_links(arg)
    scrape( seed, links )

if __name__=="__main__":
    main(sys.argv[1])
