# Scrape

Run `fetch_page_links.py` to download a list of biographies in DIB.  Outputs `links.txt`

Run `scrape.py` on the output of `fetch_page_links.py` to download biographies. Outputs HTML files with biography ID as filename.

Run `extract_article.py` on the downloaded biographies to convert them to a standard format that is used by the rest of the pipeline.

`id_missing_pages.py` can be used to identify which of the page links identified by `fetch_page_links.py` could not be scraped.