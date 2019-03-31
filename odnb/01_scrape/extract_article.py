#!/usr/bin/env python3
import sys
import re
from os.path import basename, splitext
from bs4 import BeautifulSoup

def get_article(fname):
    with open(fname,"r") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "lxml")
    output = BeautifulSoup("<html><head><meta charset=\"UTF-8\"</head><body></body></html", "lxml")

    article = soup.find("div", {"id":"contentBody"})

    title = article.find("h1")
    author = article.find("li", {"data-role" : "author"})

    head_title = output.new_tag("title")
    output.find("head").insert(0, head_title)
    head_title.string = title.getText()   
    # title.decompose()
    
    if author:
        head_meta_author = output.new_tag("meta", author=re.sub("^by ", "", author.getText()))
        output.find("head").append(head_meta_author)
        # author.decompose()
    
    for div in article.find_all("div", {"class" : "chunkFoot"}):
        div.decompose()

    output.find("body").contents = article.contents

    return output

def main(arg):
    for i in range(len(arg)):
        page = arg[i]
        print("Processing {:4}/{} :: {}".format(i+1, len(arg), page))
        article = get_article(page)
        with open("{}.html".format(splitext(basename(page))[0]), "w") as f:
            f.write(str(article))

if __name__=="__main__":
    main(sys.argv[1:])
