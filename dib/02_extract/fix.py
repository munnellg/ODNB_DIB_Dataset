#!/usr/bin/env python3
import sys
import re
from os.path import basename, splitext

def process( fname ):
    with open(fname, "r") as f:
        content = f.read()
        content = content.replace("–", "-")      
        content = content.replace("‘", "'")
        content = content.replace("’", "'")
        content = re.sub(" +", " ", content.strip())
        return content

def main(args):
    for arg in args:
        print("Processing {}".format(arg))
        raw = process(arg)
        with open("{}.html".format(splitext(basename(arg))[0]), "w") as f:
            f.write(raw)

if __name__ == "__main__":
    main(sys.argv[1:])
