#!/usr/bin/env python3
import random
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup

seed = "http://www.oxforddnb.com/browse"

def scrape(root):
        
    pf = 1
    pl = 746

    f = open("links.txt", "w")

    for i in range(pf,pl+1):
        print("Page {}/{}".format(i,pl))

        args = {
            "btog" : "chap",
            "isQuickSearch" : "true",
            "page" : i,
            "pageSize" : 100,
            "sort" : "titlesort"
        }

        headers = {
            'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        }

        query_string = urllib.parse.urlencode(args)
        url = "{}?{}".format(root, query_string)
        
        try:
            req = urllib.request.Request(url, "".encode("ascii"), headers)
            handler = urllib.request.urlopen( req )        
            page = handler.read().decode( 'utf-8' )
            soup = BeautifulSoup(page, "html.parser")
            search_results = soup.find_all("div", {"class" : "title-wrapper"})
            for link in [ div.find("a") for div in search_results ]:
                f.write("{}\n".format(str(link)))
                
        except urllib.error.HTTPError as e:
            print(e)

    f.close()

def main():
    scrape(seed)

if __name__=="__main__":
    main()
