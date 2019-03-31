# Extract

Extract semi-structured data from the articles downloaded in 01_scrape.

Pass the articles as arguments to `02_extract` which will extract entity information and output a json file containg one entry per biography for the entity who is the subject of the article.

`fix.py` fixes some Unicode issues that were encountered.