# Link

Links entities from ODNB and DIB to DBpedia

The script `link_to_dbpedia.py` is used to link entities extracted from ODNB and DIB to DBpedia. At this stage a single referent is not chosen. All candidate matches and their respective weights are added to the entity's attributes in sorteted order. This requires a trained Word2Vec model and a solr instance which indexes the title (preferred surface form), alternate names and content of the corresponding DBpedia entity.

The `create_link_map.py` script produces the final mapping of entities to DBpedia entities. This applies the hard threshold and also resolves conflicts where two entities have been mapped to the same referent. On a conflict, the entity with the higher similarity is assigned the referent and the entity with the lower similarity is moved down to its next preference.