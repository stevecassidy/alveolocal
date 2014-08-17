from rdflib import Namespace

# Define namespaces
RDF = Namespace(u"http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace(u"http://www.w3.org/2000/01/rdf-schema#")
DC = Namespace(u"http://purl.org/dc/terms/")
BIO = Namespace(u"http://purl.org/vocab/bio/0.1/")
FOAF = Namespace(u"http://xmlns.com/foaf/0.1/")
SCHEMA = Namespace(u"http://schemas.talis.com/2005/address/schema#")
BIBO = Namespace(u"http://purl.org/ontology/bibo/")
GEOPOL = Namespace(u"http://aims.fao.org/aos/geopolitical.owl#")
GEONAM = Namespace(u"http://sws.geonames.org/")
DBPEDIA = Namespace(u"http://dbpedia.org/resource/")
FOAF = Namespace(u"http://xmlns.com/foaf/0.1/")
OLAC = Namespace(u"http://www.language-archives.org/OLAC/1.1/")
DADA = Namespace("http://purl.org/dada/schema/0.2#")
RDF = Namespace(u"http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace(u"http://www.w3.org/2000/01/rdf-schema#")
OWL = Namespace(u"http://www.w3.org/2002/07/owl#")
XSD = Namespace(u"http://www.w3.org/2001/XMLSchema#")
HCSVLAB = Namespace(u"http://hcsvlab.org/vocabulary/")

# Namespaces we control
# SCHEMA is the namespace for all schema
SCHEMA = Namespace(u"http://ns.ausnc.org.au/schemas/")

# AUSNC is the default namespace for metadata properties
AUSNC = Namespace(SCHEMA[u"ausnc_md_model/"])

# corpus is used as a prefix for all corpus items
CORPUS = Namespace(u"http://ns.ausnc.org.au/corpora/")

# annotation namespaces
ANNOTATION = Namespace(SCHEMA[u'annotation/'])

ICEA = Namespace(ANNOTATION['ice/'])
ARTA = Namespace(ANNOTATION['art/'])
ACEA = Namespace(ANNOTATION['ace/'])
CA = Namespace(ANNOTATION['conversation/'])
COOEEA = Namespace(ANNOTATION['cooee/'])
MONASHA = Namespace(ANNOTATION['monash/'])
MAUS = Namespace(ANNOTATION['maus/'])



# this hack finds all of the namespaces defined above and 
# puts them into a dictionary that we can use in bind_graph
import sys
NAMESPACES = dict()
namespaces = [n for n in sys.modules[__name__].__dict__.keys() if n.isupper() and 'NAMESPACES' not in n]
for ns in namespaces:
    NAMESPACES[ns.lower()] = eval(ns)

def bind_graph(graph):
    
    for ns in NAMESPACES.keys():
        graph.bind(ns, NAMESPACES[ns]) 

    return graph


def corpus_property_namespace(corpusID):
    """Return a namespace object suitable for use
    in generating new property names for this corpus"""
    
    return Namespace(SCHEMA[corpusID.lower()+"/"])


def corpus_prefix_namespace(corpusID):
    """Return a namespace we can use to generate 
    URIs for things inside this corpus"""

    return Namespace(CORPUS[corpusID.lower()])

def corpus_uri(corpusID):
    """Given a corpus identifier, return the right 
    corpus URI
    
    corpusURI is http://ns.ausnc.org.au/corpora/braided/
    
    """
    
    return corpus_prefix_namespace(corpusID)[""]


def corpus_item_uri(corpusID, itemID):
    """Given a corpus and item identifier, return 
    a URI for the item
    
    http://ns.ausnc.org.au/corpus/<corpusid>/items/<itemid>
    """
    
    return corpus_prefix_namespace(corpusID)["/items/"+itemID]


def corpus_speaker_uri(corpusID, speakerID):
    """Generate a speaker URI for this corpus"""

    return  corpus_prefix_namespace(corpusID)["/person/"+speakerID]

def corpus_source_uri(corpusID, sourceID):
    """Generate a URI for the source data of this item"""
    
    return corpus_prefix_namespace(corpusID)["/source/"+sourceID]


def corpus_annotation_uri(corpusID, annotID):
    """Generate a URI for an annotation in this corpus"""
    
    return corpus_prefix_namespace(corpusID)["/annotation/"+annotID]

