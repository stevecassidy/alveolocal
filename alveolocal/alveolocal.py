# -*- coding: utf-8 -*-

import os

from rdflib import Graph, URIRef
from namespaces import RDF, DCMITYPE, DC, AUSNC, HCSVLAB, DADA
from uuid import uuid4
from rdflib.term import Literal
from namespaces import XSD


class API(object):
    """The Alveo API"""

    base_url = "http://localhost:3000/"

    def attach_directory(self, dirname):
        """Attach to a directory containing RDF files
        and deliver data from there"""

        self.graph = Graph()
        self.basedir = dirname

        for dirpath, _, filenames in os.walk(dirname):
            
            for filename in filenames:
                if filename.endswith(".rdf"):
                    self.graph.parse(os.path.join(dirpath, filename), format='turtle')
                elif filename.endswith(".n3"):
                    self.graph.parse(os.path.join(dirpath, filename), format='n3')

        return len(self.graph)

    def version(self):
        """Return the current API version string"""

        return "v3.1.1"

    def get_collections(self):
        """Return a list of collections in the store"""

        result = []
        for collectionuri in self.graph.subjects(RDF.type, DCMITYPE.Collection):
            result.append(str(collectionuri))

        return result
        
        
    def get_collection(self, collectionid):
        """Return the collection metadata for this collection"""
        
        meta = dict()
        for _,p,o in self.graph.triples((URIRef(collectionid), None, None)):
            meta[p.n3(self.graph.namespace_manager)] = o.toPython()
        
        name = self.graph.value(URIRef(collectionid), DC.alternative).toPython()
        return {'collection_url': collectionid,
                'collection_name': name,
                'metadata': meta,
                }

    def _corpus_name(self, itemid):
        """Return the name of the corpus this item is part of"""

        corpusuri = self.graph.value(subject=URIRef(itemid), predicate=DC.isPartOf)
        return os.path.basename(corpusuri)
    
    def _annotation_url(self, itemid):
        """Return the annotation URL for this itemid"""
        
        return os.path.join(itemid, "annotations.json")
        

    def _primary_text_url(self, itemid):
        """Return the primary text URL for this itemid"""

        return os.path.join(itemid, "primary_text.json")      

    def get_item_metadata(self, itemid):
        """Return all metadata for the given item identifier as a
        dictionary"""
        
        meta = {
            u'alveo:annotations_url': self._annotation_url(itemid),
            u'alveo:primary_text_url': self._primary_text_url(itemid),
            u'alveo:metadata': dict(),
            u'alveo:catalog_url': itemid, 
            u'@context': "https://app.alveo.edu.au/schema/json-ld", 
            u'alveo:documents': [],
            }
        
        # all fields that are required but have a value 'unspecified' if missing
        meta_required = [u'ausnc:speech_style', 
                         u'ausnc:interactivity', 
                         u'olac:discourse_type', 
                         u'ausnc:communication_medium',
                         u'ausnc:communication_context',
                         u'ausnc:communication_setting',
                         u'ausnc:audience',
                         u'ausnc:plaintextversion',
                         u'ausnc:written_mode',
                         u'ausnc:publication_status',
                         u'alveo:display_document',
                         u'alveo:handle',
                         u'ausnc:mode',
                         u'alveo:date_group',
                         u'alveo:full_text',
                         u'dcterms:extent',
                         u'alveo:indexable_document',
                         u'alveo:sparqlEndpoint'
                         
                         ]
        
        for _,p,o in self.graph.triples((URIRef(itemid), None, None)):
            #meta[u'alveo:metadata'][p.n3(self.graph.namespace_manager)] = o.n3(self.graph.namespace_manager)
            meta[u'alveo:metadata'][p.n3(self.graph.namespace_manager)] = o.toPython()
            
        for key in meta_required:
            if not key in meta[u'alveo:metadata']:
                meta[u'alveo:metadata'][key] = u'unspecified'
        
        # get documents and add metadata
        types = []
        docs = []
        for _,p,o in self.graph.triples((URIRef(itemid), AUSNC.document, None)):
            dm = self._document_metadata(o)
            meta[u'alveo:documents'].append(dm)
            
            types.append(str(dm[u'dcterms:type']))
            docs.append(str(dm[u'dcterms:title']))
                    
        meta[u'alveo:metadata'][u'dcterms:type'] = ', '.join(types)
        meta[u'alveo:metadata'][u'ausnc:document'] = ', '.join(docs)
        
        return meta
        
        
    def _document_metadata(self, docuri):
        """Generate the dictionary of document metadata for this document"""
        
        
        meta = {
             u'alveo:size': u'',
             u'alveo:url': u'',
             u'dcterms:extent': u'',
             u'dcterms:identifier': u'',
             u'dcterms:title': u'',
             u'dcterms:type': u'',
             u'rdf:type': u'http://xmlns.com/foaf/0.1/Document',
        }
        for _,p,o in self.graph.triples((docuri, None, None)):
            if p.n3(self.graph.namespace_manager) == u'dc:source':
                meta[u'alveo:url'] = str(o)
            else:
                meta[p.n3(self.graph.namespace_manager)] = o.toPython()
        
         
        return meta
        
    
    def _uri_to_path(self, uri):
        """Turn a document URI to a path in the local store"""
        
        if uri.startswith(self.base_url):
            suffix = uri[len(self.base_url + "documents/"):]
            return os.path.join(self.basedir, suffix)
        else:
            return uri
        
    def _get_display_document_url(self, itemid):
        """Return the url of the display document if any, None if not"""

        # get the display document
        docuri = self.graph.value(subject=URIRef(itemid), predicate=HCSVLAB.indexable_document)
        source = self.graph.value(subject=docuri, predicate=DC.source)

        if docuri is None:
            return None
        
        return str(source)
        
        
    def get_primary_text(self, itemid):
        """Return the primary text for this item if any, None if not"""
        
        # get the display document
        source = self._get_display_document_url(itemid)
        
        if source is None:
            return None
        
        # locate it in local storage
        sourcepath = self._uri_to_path(source)
        
        if not os.path.exists(sourcepath):
            return None
        
        # read the text
        with open(sourcepath, 'rb') as fp:
            text = fp.read()
        
        # return it
        return text.decode("utf-8")
        
    def get_document(self, collection_name, file_name):
        path = os.path.join(self.basedir, collection_name, file_name)
        with open(path) as textfile:
            text = textfile.read()
        return text
        
    def get_annotations(self, itemid, **filters):
        """Return the annotations for this item as a dictionary"""
        
        result = {'@context': "https://app.alveo.edu.au/schema/json-ld",
                  'commonProperties': {},
                  }
                  
        anns = []
        for aset in self.graph.subjects(DADA.annotates, URIRef(itemid)):
            for annid in self.graph.subjects(DADA.partof, aset):
                ann = {
                    '@id': str(annid),
                    '@type': '',
                    'label': str(self.graph.value(subject=annid, predicate=DADA.label)),
                    'type': str(self.graph.value(subject=annid, predicate=DADA.type)),
                    'start': '',
                    'end': '',
                }
                
                region = self.graph.value(subject=annid, predicate=DADA.targets)
                ann['start'] = self.graph.value(subject=region, predicate=DADA.start).toPython()
                ann['end'] = self.graph.value(subject=region, predicate=DADA.end).toPython()
                
                atype = self.graph.value(subject=region, predicate=RDF.type)
                if atype == DADA.UTF8Region:
                    ann['@type'] = 'dada:TextAnnotation'
                elif atype == DADA.SecondRegion:
                    ann['@type'] = 'dada:SecondAnnotation'
                
                
                for _,p,o in self.graph.triples((annid, None, None)):
                    if p not in [DADA.label, DADA.type, DADA.targets, RDF.type, DADA.partof]:
                        ann[p.n3(self.graph.namespace_manager)] = o.toPython()
                
                
                conditions = []
                conditions.append("type" not in filters.keys() or URIRef(ann["type"]) == self._denamespace(filters["type"]))
                conditions.append("label" not in filters.keys() or ann["label"] == filters["label"])
                conditions.append("start" not in filters.keys() or str(ann["start"]) == filters["start"])
                conditions.append("end" not in filters.keys() or str(ann["end"]) == filters["end"])
                if all(conditions):
                    anns.append(ann)
                
        result['alveo:annotations'] = anns
        result['commonProperties']['alveo:annotates'] = self._get_display_document_url(itemid)
        
        return result
        
    def get_annotation_types(self, itemid):
        result = {"item_url":itemid}
        types = []
        for aset in self.graph.subjects(DADA.annotates, URIRef(itemid)):
            for annid in self.graph.subjects(DADA.partof, aset):
                dadatype = self.graph.value(subject=annid, predicate=DADA.type).toPython()
                if not dadatype in types:
                    types.append(dadatype)
                
        result["annotation_types"] = types
        return result
             
        
    def get_annotation_context(self):
        output = {
                  "@context":{
                              "commonProperties":{"@id":"http://purl.org/dada/schema/0.2#commonProperties"},
                              "dada":{"@id":"http://purl.org/dada/schema/0.2#"},
                              "type":{"@id":"http://purl.org/dada/schema/0.2#type"},
                              "start":{"@id":"http://purl.org/dada/schema/0.2#start"},
                              "end":{"@id":"http://purl.org/dada/schema/0.2#end"},
                              "label":{"@id":"http://purl.org/dada/schema/0.2#label"},
                              "alveo":{"@id":"http://alveo.edu.au/schema/"},
                              "ace":{"@id":"http://ns.ausnc.org.au/schemas/ace/"},
                              "ausnc":{"@id":"http://ns.ausnc.org.au/schemas/ausnc_md_model/"},
                              "austalk":{"@id":"http://ns.austalk.edu.au/"},
                              "austlit":{"@id":"http://ns.ausnc.org.au/schemas/austlit/"},
                              "bibo":{"@id":"http://purl.org/ontology/bibo/"},
                              "cooee":{"@id":"http://ns.ausnc.org.au/schemas/cooee/"},
                              "dc":{"@id":"http://purl.org/dc/terms/"},
                              "foaf":{"@id":"http://xmlns.com/foaf/0.1/"},
                              "gcsause":{"@id":"http://ns.ausnc.org.au/schemas/gcsause/"},
                              "ice":{"@id":"http://ns.ausnc.org.au/schemas/ice/"},
                              "olac":{"@id":"http://www.language-archives.org/OLAC/1.1/"},
                              "purl":{"@id":"http://purl.org/"},
                              "rdf":{"@id":"http://www.w3.org/1999/02/22-rdf-syntax-ns#"},
                              "schema":{"@id":"http://schema.org/"},
                              "xsd":{"@id":"http://www.w3.org/2001/XMLSchema#"}
                              }
                  }
        return output
    
    def _denamespace(self, qname):
        """Return the full url for qname according to the graph prefixes"""
    
        for ns in self.graph.namespaces():
            if qname.startswith(ns[0]):
                suffix = qname.split(':')[1]
                return URIRef(ns[1] + suffix)
        
        return qname
        
    
    def search(self, query):
        """Find items matching a set of query terms. 
        query is a sequence of tuples (property, value) where
        property is an RDF property name in prefixed form (eg. 'dc:created')
        and value is the desired value.  Returns a list of 
        matching item identifiers"""
        
        
        sparql = """SELECT ?item WHERE {
            ?item rdf:type ausnc:AusNCObject . 
            %s
        }"""
        
        terms = ""
        for pred, value in query:
            terms += "?item %s '%s' .\n" % (pred, value)
        
        sparql = sparql % terms
                
        result = self.graph.query(sparql)
        items = [str(m[0]) for m in result]        
        
        return items
    
    def search_sparql(self, collection_id, query):
        output = {"head":{"vars":[]}, "results":{"bindings":[]}}
        subgraph = Graph()
        subgraph += self.graph.triples((URIRef(collection_id), None, None))
        subgraph += self.graph.triples((None, None, URIRef(collection_id)))
        result = subgraph.query(query)        
        for var in result.vars:
            output["head"]["vars"].append(str(var))
        for binding in result.bindings:
            temp = {}
            for var in output["head"]["vars"]:
                temp[var] = {"type":type(binding[var]).__name__, "value":binding[var].toPython()}
            output["results"]["bindings"].append(temp)
        return output
    
    def add_annotation(self, filename, collection_id, collection_name, data):
        g = Graph()
        g.bind("dada", "http://purl.org/dada/schema/0.2#")
        ann_coll_id = "%s/annotation/%s" %(collection_id, uuid4())
        g.add((URIRef(ann_coll_id), RDF.type, DADA.AnnotationCollection))
        g.add((URIRef(ann_coll_id), DADA.annotates, URIRef(data["commonProperties"]["alveo:annotates"])))
        for annotation in data["alveo:annotations"]:
            ann_id = self.generate_annotation_id(collection_id)
            ann_reg_id = ann_id + "L"
            g.add((URIRef(ann_id), RDF.type, DADA.Annotation))
            g.add((URIRef(ann_id), DADA.partof, URIRef(ann_coll_id)))
            g.add((URIRef(ann_id), DADA.targets, URIRef(ann_reg_id)))
            if "label" in annotation:
                g.add((URIRef(ann_id), DADA.label, Literal(annotation["label"])))
            g.add((URIRef(ann_id), DADA.type, URIRef(annotation["type"])))
            if annotation["@type"] == "dada:TextAnnotation":
                g.add((URIRef(ann_reg_id), RDF.type, DADA.UTF8Region))
            elif annotation["@type"] == "dada:SecondAnnotation":
                g.add((URIRef(ann_reg_id), RDF.type, DADA.SecondRegion))
            g.add((URIRef(ann_reg_id), DADA.start, Literal(annotation["start"], datatype=XSD.int)))
            g.add((URIRef(ann_reg_id), DADA.end, Literal(annotation["end"], datatype=XSD.int)))
        g.serialize(os.path.join(self.basedir, collection_name, filename+".n3"), format="n3")
        self.graph += g
        return {"success":"file %s uploaded successfully" % filename}
     
    num = 1000   
    def generate_annotation_id(self, collection_id):
        API.num += 1
        return collection_id + "/annotation/" + str(API.num)
        
    
    
    
        