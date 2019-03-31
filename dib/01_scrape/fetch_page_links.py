#!/usr/bin/env python3
import random
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup

seed = "http://dib.cambridge.org/browse.do"

def scrape(root):
    
    links = []
    pf = 1
    pl = 105
    for i in range(pf,pl+1):
        print("Page {}/{}".format(i,pl))

        args = {
            "searchBy": "1",
            "_currentPage" : i,
            "_pageSize" : "100",
            "_sortBy" : "name",
            "_sortOrder" : "asc"
        }

        query_string = urllib.parse.urlencode(args)
        url = "{}?{}".format(root, query_string)
        
        try:
            req = urllib.request.Request(url)
            handler = urllib.request.urlopen( req )        
            page = handler.read().decode( 'utf-8' )
            soup = BeautifulSoup(page, "html.parser")
            search_results = soup.find("div", {"class" : "text_04"})
            for link in search_results.find_all("a"):
                links.append(str(link))
                
        except urllib.error.HTTPError as e:
            print(e)

    return links

def main():
    links = set(scrape(seed))

    with open("links.txt", "w") as f:
        f.write("\n".join(links))

if __name__=="__main__":
    main()
