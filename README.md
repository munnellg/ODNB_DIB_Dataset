# ODNB and DIB Datasets

Scripts used to structure ODNB and DIB data into a format that could be used as a knowledge base for entity linking.

Minor variations exist between the scripts for scraping content from DIB and ODNB. The link and to_ttl processes can be applied to either collection.

Order of operations should be:

+ scrape
+ extract
+ link
+ to_ttl