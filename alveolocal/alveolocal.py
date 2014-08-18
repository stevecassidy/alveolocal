# -*- coding: utf-8 -*-

from rdflib import Graph, URIRef, Literal
import os

from namespaces import *


class API(object):
    """The Alveo API"""

    base_url = "http://localhost:3000/"

    def attach_directory(self, dirname):
        """Attach to a directory containing RDF files
        and deliver data from there"""

        self.graph = Graph()
        self.basedir = dirname

        for dirpath, dirnames, filenames in os.walk(dirname):
            
            for filename in filenames:
                if filename.endswith(".rdf"):
                    self.graph.parse(os.path.join(dirpath, filename), format='turtle')
                elif filename.endswith(".n3"):
                    self.graph.parse(os.path.join(dirpath, filename), format='n3')

        return len(self.graph)

    def version(self):
        """Return the current API version string"""

        return "V2.0"

    def get_collections(self):
        """Return a list of collections in the store"""

        result = []
        for collectionuri in self.graph.subjects(RDF.type, DCMITYPE.Collection):
            result.append(str(collectionuri))

        return result
        
        
    def get_collection(self, collectionid):
        """Return the collection metadata for this collection"""
        
        meta = dict()
        for s,p,o in self.graph.triples((URIRef(collectionid), None, None)):
            meta[p.n3(self.graph.namespace_manager)] = o.toPython()
        
        name = self.graph.value(URIRef(collectionid), DC.alternative).toPython()
        return {'collection_url': collectionid,
                'collection_name': name,
                'metadata': meta,
                }

    def get_item_lists(self):
        """Return a list of currently defined item lists"""

        return []

    def _corpus_name(self, itemid):
        """Return the name of the corpus this item is part of"""

        corpusuri = self.graph.value(subject=URIRef(itemid), predicate=DC.isPartOf)
        return os.path.basename(corpusuri)

    def _base_url(self, itemid):
        """Return the base URL for this itemid"""
        
        collection = self._corpus_name(itemid)
        item = self.graph.value(subject=URIRef(itemid), predicate=DC.identifier)
                
        
        return os.path.join(self.base_url, "catalog", collection, item)
    
    def _annotation_url(self, itemid):
        """Return the annotation URL for this itemid"""
        
        base = self._base_url(itemid)
        return os.path.join(base, "annotations.json")
        

    def _primary_text_url(self, itemid):
        """Return the primary text URL for this itemid"""

        base = self._base_url(itemid)
        return os.path.join(base, "primary_text.json")      

    def get_item_metadata(self, itemid):
        """Return all metadata for the given item identifier as a
        dictionary"""
        
        meta = {
            u'alveo:annotations_url': self._annotation_url(itemid),
            u'alveo:primary_text_url': self._primary_text_url(itemid),
            u'alveo:metadata': dict(),
            u'alveo:catalog_url': self._base_url(itemid), 
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
        
        for s,p,o in self.graph.triples((URIRef(itemid), None, None)):
            #meta[u'alveo:metadata'][p.n3(self.graph.namespace_manager)] = o.n3(self.graph.namespace_manager)
            meta[u'alveo:metadata'][p.n3(self.graph.namespace_manager)] = o.toPython()
            
        for key in meta_required:
            if not key in meta[u'alveo:metadata']:
                meta[u'alveo:metadata'][key] = u'unspecified'
        
        # get documents and add metadata
        types = []
        docs = []
        for s,p,o in self.graph.triples((URIRef(itemid), AUSNC.document, None)):
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
        for s,p,o in self.graph.triples((docuri, None, None)):
            if p.n3(self.graph.namespace_manager) == u'dc:source':
                meta[u'alveo:url'] = str(o)
            else:
                meta[p.n3(self.graph.namespace_manager)] = o.toPython()
        
         
        return meta
        
    
    def _uri_to_path(self, uri):
        """Turn a document URI to a path in the local store"""
        
        if uri.startswith(self.base_url):
            suffix = uri[len(self.base_url):]
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
        return text
        
        
    def get_annotations(self, itemid):
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
                
                
                for s,p,o in self.graph.triples((annid, None, None)):
                    if p not in [DADA.label, DADA.type, DADA.targets, RDF.type, DADA.partof]:
                        ann[p.n3(self.graph.namespace_manager)] = o.toPython()
                
                
                anns.append(ann)
                
        result['alveo:annotations'] = anns
        result['commonProperties']['alveo:annotates'] = self._get_display_document_url(itemid)
        
        return result
        
    
    def _denamespace(self, qname):
        """Return the full url for qname according to the graph prefixes"""
    
        for ns in self.graph.namespace_manager.namespaces():
            if qname.startswith(ns[0]):
                suffix = qname.split(':')[1]
                return URIRef(ns[1] + suffix)
        
        return qname
    
    
    def search(self, query):
        """Search for items using the query, 
        query is a sequence of property, values tuples eg. (('dc:created', '1788'),)
        Return a list of item identifiers that match the queries."""
        
        result = []
        for pred, value in query:
            partial = set()
            for obj in self.graph.subjects(self._denamespace(pred), Literal(value)):
                partial.add(obj)
                
            if len(result) == 0:
                result = partial
            else:
                result = result.intersection(partial)
                
        return [str(i) for i in result]
    
    
        