#!/usr/bin/env python3
import os
import sys

def load_links(fname):
    with open(fname,"r") as f:
        return f.read().split("\n")[:-1]

def load_articles(dirname):
    files = os.listdir(dirname)
    return [ os.path.splitext(os.path.basename(f))[0] for f in files ]

def main(args):
    links = sorted(load_links(args[0]))
    files = load_articles(args[1])
    missing = [ link for link in links if link not in files ]
    print("\n".join(missing))

if __name__=="__main__":
    main(sys.argv[1:])
