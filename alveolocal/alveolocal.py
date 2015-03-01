# -*- coding: utf-8 -*-

import os

from rdflib import Graph, URIRef
from namespaces import RDF, DCMITYPE, DC, AUSNC, HCSVLAB, DADA, XSD, PROV, LOCALTERMS, RDFS, XYZZY, FOAF
from uuid import uuid4
from rdflib.term import Literal
from rdflib.plugins.sparql.processor import prepareQuery
from base import Store
import requests
import json


class API(object):
    """The Alveo API"""

    base_url = "http://localhost:3000/"
    last_generated_ann_id = None

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

        return "V2.0"

    def get_collections(self):
        """Return a list of collections in the store"""

        result = []
        for collection_uri in self.graph.subjects(RDF.type, DCMITYPE.Collection):
            result.append(str(collection_uri))

        return result
        
        
    def get_collection(self, collection_uri):
        """Return the collection metadata for this collection"""
        
        meta = dict()
        for _,p,o in self.graph.triples((URIRef(collection_uri), None, None)):
            meta[p.n3(self.graph.namespace_manager)] = o.toPython()
        
        name = self.graph.value(URIRef(collection_uri), DC.alternative).toPython()
        return {'collection_url': collection_uri,
                'collection_name': name,
                'metadata': meta,
                }

    def _corpus_name(self, item_uri):
        """Return the name of the corpus this item is part of"""

        corpus_uri = self.graph.value(subject=URIRef(item_uri), predicate=DC.isPartOf)
        return os.path.basename(corpus_uri)
    
    def _annotation_url(self, item_uri):
        """Return the annotation URL for this itemid"""
        
        return os.path.join(item_uri, "annotations.json")
        

    def _primary_text_url(self, item_uri):
        """Return the primary text URL for this itemid"""

        return os.path.join(item_uri, "primary_text.json")      

    def get_item_metadata(self, item_uri):
        """Return all metadata for the given item identifier as a
        dictionary"""
        
        meta = {
            u'alveo:annotations_url': self._annotation_url(item_uri),
            u'alveo:primary_text_url': self._primary_text_url(item_uri),
            u'alveo:metadata': dict(),
            u'alveo:catalog_url': item_uri, 
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
        
        for _,p,o in self.graph.triples((URIRef(item_uri), None, None)):
            #meta[u'alveo:metadata'][p.n3(self.graph.namespace_manager)] = o.n3(self.graph.namespace_manager)
            meta[u'alveo:metadata'][p.n3(self.graph.namespace_manager)] = o.toPython()
            
        for key in meta_required:
            if not key in meta[u'alveo:metadata']:
                meta[u'alveo:metadata'][key] = u'unspecified'
        
        # get documents and add metadata
        types = []
        docs = []
        for _,p,o in self.graph.triples((URIRef(item_uri), AUSNC.document, None)):
            dm = self._document_metadata(o)
            meta[u'alveo:documents'].append(dm)
            
            types.append(str(dm[u'dcterms:type']))
            docs.append(str(dm[u'dcterms:title']))
                    
        meta[u'alveo:metadata'][u'dcterms:type'] = ', '.join(types)
        meta[u'alveo:metadata'][u'ausnc:document'] = ', '.join(docs)
        
        return meta
        
        
    def _document_metadata(self, doc_uri):
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
        for _,p,o in self.graph.triples((doc_uri, None, None)):
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
        
    def _get_display_document_url(self, item_uri):
        """Return the url of the display document if any, None if not"""

        # get the display document
        doc_uri = self.graph.value(subject=URIRef(item_uri), predicate=HCSVLAB.indexable_document)
        source = self.graph.value(subject=doc_uri, predicate=DC.source)

        if doc_uri is None:
            return None
        
        return str(source)
        
        
    def get_primary_text(self, item_uri):
        """Return the primary text for this item if any, None if not"""
        
        # get the display document
        source = self._get_display_document_url(item_uri)
        
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
        
    def get_document(self, collection_id, file_name):
        path = os.path.join(self.basedir, collection_id, file_name)
        with open(path) as textfile:
            text = textfile.read()
        return text
        
    def get_annotations(self, item_uri, filters):
        """Return the annotations for this item as a dictionary"""
        
        result = {'@context': "https://app.alveo.edu.au/schema/json-ld",
                  'commonProperties': {},
                  }
                  
        if filters is None:
            filters = {}
        anns = []
        initBindings = {"item":URIRef(item_uri)}
        query = prepareQuery("""select ?annotation where {
                                                          ?annotation dada:partof ?annCollection.
                                                          ?annCollection dada:annotates ?item.
                                                       }""", initNs={"dada":DADA})
        if "priorTo" in filters:
            initBindings = {"item":URIRef(item_uri),
                            "givenTime":Literal(filters["priorTo"].strftime('%Y-%m-%dT%I:%M:%S'), datatype=XSD.dateTime)}
            query = prepareQuery("""select ?annotation where {
                                                              ?annotation dada:partof ?annCollection.
                                                              ?annCollection dada:annotates ?item.
                                                              ?annCollecction prov:generatedAtTime ?time.
                                                              FILTER (?time < ?givenTime)
                                                           }""", initNs={"dada":DADA,
                                                                         "prov":PROV})
        elif "user" in filters:
            initBindings = {"item":URIRef(item_uri),
                            "user":Literal(filters["user"])}
            query = prepareQuery("""select ?annotation where {
                                                              ?annotation dada:partof ?annCollection.
                                                              ?annCollection dada:annotates ?item.
                                                              ?annCollection prov:generatedBy ?activity.
                                                              ?activity prov:wasAssociatedWith ?user.
                                                           }""", initNs={"dada":DADA,
                                                                         "prov":PROV})
        elif "type" in filters:
            initBindings = {"item":URIRef(item_uri),
                            "type":URIRef(self._denamespace(filters["type"]))}
            query = prepareQuery("""select ?annotation where {
                                                              ?annotation dada:partof ?annCollection.
                                                              ?annCollection dada:annotates ?item.
                                                              ?annotation dada:type ?type
                                                           }""", initNs={"dada":DADA})
        annResults = self.graph.query(query, initBindings=initBindings)
        annIDs = [annResult["annotation"] for annResult in annResults.bindings]
        for annid in annIDs:
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
            
            anns.append(ann)
                
                
        result['alveo:annotations'] = anns
        result['commonProperties']['alveo:annotates'] = self._get_display_document_url(item_uri)
        
        return result
        
    def get_annotation_types(self, item_uri):
        result = {"item_url":item_uri}
        types = []
        for aset in self.graph.subjects(DADA.annotates, URIRef(item_uri)):
            for annid in self.graph.subjects(DADA.partof, aset):
                dadatype = self.graph.value(subject=annid, predicate=DADA.type).toPython()
                if not dadatype in types:
                    types.append(dadatype)
                
        result["annotation_types"] = types
        return result
             
        
    def get_annotation_context(self):
        output = {
                    "@context": {
                        "@base":"http://purl.org/dada/schema/0.2/",
                        "annotations":{
                            "@id":"http://purl.org/dada/schema/0.2/annotations",
                            "@container":"@list"
                        },
                        "commonProperties": {"@id":"http://purl.org/dada/schema/0.2/commonProperties"},
                        "type":{"@id":"http://purl.org/dada/schema/0.2/type"},
                        "start":{"@id":"http://purl.org/dada/schema/0.2/start"},
                        "end":{"@id":"http://purl.org/dada/schema/0.2/end"},
                        "label":{"@id":"http://purl.org/dada/schema/0.2/label"},
                        "annotates":{"@id":"http://purl.org/dada/schema/0.2/annotates"}
                    }
                }
        return output
    
    def _denamespace(self, qname):
        """Return the full url for qname e.g. dada:partof according to the graph prefixes"""
    
        for ns in self.graph.namespaces():
            parts = qname.split(':')
            if ns[0] == parts[0]:
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
    
    def search_sparql(self, collection_uri, query):
        collection_id = self._get_id(collection_uri)
        output = {"head":{"vars":[]}, "results":{"bindings":[]}}
        subgraph = Store()
        subgraph.attach_directory(os.path.join(self.basedir, collection_id))
        subgraph.graph.parse(os.path.join(self.basedir, collection_id+".n3"), format='n3')
        result = subgraph.graph.query(query)        
        for var in result.vars:
            output["head"]["vars"].append(str(var))
        for binding in result.bindings:
            temp = {}
            for var in output["head"]["vars"]:
                temp[var] = {"type":type(binding[var]).__name__, "value":binding[var].toPython()}
            output["results"]["bindings"].append(temp)
        return output
    
    def download_files(self, items, api_key):
        url = "https://app.alveo.edu.au/catalog/download_items"
        headers = {"X-API-KEY": api_key, "Accept": "application/json"}
        headers["content-type"] = "application/json"
        payload = {'items':items}
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        with open('temp.zip', 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024): 
                if chunk:
                    f.write(chunk)
                    f.flush()
        # TODO: run the script to generate local version of the files
        # move the final files to the correct place
    
    def add_annotation(self, **params):
        if "collection_uri" in params:
            collection_uri = params["collection_uri"]
        if "data" in params:
            data = params["data"]
        if "filename" in params:
            filename = params["filename"]
        g = Graph()
        g.bind("dada", "http://purl.org/dada/schema/0.2#")
        ann_coll_id = "%s/annotation/%s" %(collection_uri, uuid4())
        activity = self.create_activity()
        user = self.get_user(data["metadata"]["creator"])
        software = self.get_software(data["metadata"]["generatedBy"])
        # Annotation Collection
        g.add((URIRef(ann_coll_id), RDF.type, DADA.AnnotationCollection))
        g.add((URIRef(ann_coll_id), RDF.type, PROV.Entity))
        g.add((URIRef(ann_coll_id), DADA.annotates, URIRef(data["metadata"]["alveo:annotates"])))
        g.add((URIRef(ann_coll_id), PROV.generatedAtTime, Literal(data["metadata"]["generatedAtTime"], datatype=XSD.dateTime)))
        g.add((URIRef(ann_coll_id), PROV.wasGeneratedBy, URIRef(activity["@id"])))
        # Activity
        g.add((URIRef(activity["@id"]), RDF.type, PROV.Activity))
        g.add((URIRef(activity["@id"]), RDFS.label, Literal(activity["label"])))
        g.add((URIRef(activity["@id"]), PROV.wasAssociatedWith, URIRef(user["@id"])))
        g.add((URIRef(activity["@id"]), PROV.wasAssociatedWith, URIRef(software["@id"])))
        # Software
        g.add((URIRef(software["@id"]), RDF.type, PROV.Activity))
        g.add((URIRef(software["@id"]), RDF.type, PROV.SoftwareAgent))
        g.add((URIRef(software["@id"]), RDFS.label, Literal(software["label"])))
        g.add((URIRef(software["@id"]), XYZZY.source, URIRef(software["source"])))
        # User
        g.add((URIRef(user["@id"]), RDF.type, FOAF.Person))
        g.add((URIRef(user["@id"]), RDF.type, PROV.Agent))
        g.add((URIRef(user["@id"]), FOAF.name, Literal(user["name"])))
        # Annotations
        for annotation in data["alveo:annotations"]:
            ann_id = self.generate_annotation_id(collection_uri)
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
            g.add((URIRef(ann_reg_id), DADA.start, Literal(annotation["start"], datatype=XSD.integer)))
            g.add((URIRef(ann_reg_id), DADA.end, Literal(annotation["end"], datatype=XSD.integer)))
        g.serialize(os.path.join(self.basedir, self._get_id(collection_uri), filename+".n3"), format="n3")
        self.graph += g
        return {"success":"file %s uploaded successfully" % filename}
     
    def generate_annotation_id(self, collection_uri):
        collection_id = self._get_id(collection_uri)
        prefix = collection_uri + "/annotation/"
        if API.last_generated_ann_id is None:
            query = prepareQuery('select ?annotation where {?annotation a ?type}')
            annotations = []
            g = Store()
            g.attach_directory(os.path.join(self.basedir, collection_id))
            results = g.graph.query(query, initBindings={'type': DADA.Annotation})
            for result in results.bindings:
                annotations.append(int(result["annotation"].toPython().replace(prefix, "")))
    
            API.last_generated_ann_id = max(annotations)
        API.last_generated_ann_id += 1
        return prefix + str(API.last_generated_ann_id)

    def _get_uri(self, output_uri_type, input_uri_type, input_uri):
        if output_uri_type == "collection":
            if input_uri_type == "item":
                query = prepareQuery("""select ?collection where{
                                                    ?collection a dcmitype:Collection.
                                                    ?item dc:isPartOf ?collection.
                                                    }""", initNs = {"dc":DC, 
                                                                    "dcmitype":DCMITYPE})
            elif input_uri_type == "document":
                query = prepareQuery("""select ?collection where{
                                                    ?collection a dcmitype:Collection.
                                                    ?item dc:isPartOf ?collection.
                                                    ?item ausnc:document ?document.
                                                    }""", initNs = {"dc":DC, 
                                                                    "dcmitype":DCMITYPE,
                                                                    "ausnc":AUSNC})
            elif input_uri_type == "source":
                query = prepareQuery("""select ?collection where{
                                                    ?collection a dcmitype:Collection.
                                                    ?item dc:isPartOf ?collection.
                                                    ?item ausnc:document ?document.
                                                    ?document dc:source ?source. 
                                                    }""", initNs = {"dc":DC, 
                                                                    "dcmitype":DCMITYPE,
                                                                    "ausnc":AUSNC})
            elif input_uri_type == "annotation":
                query = prepareQuery("""select ?collection where{
                                                    ?collection a dcmitype:Collection.
                                                    ?item dc:isPartOf ?collection.
                                                    ?annCollID dada:annotates ?item.
                                                    ?annotation dada:partof ?annCollID.
                                                    }""", initNs = {"dc":DC, 
                                                                    "dcmitype":DCMITYPE,
                                                                    "dada":DADA})
            else:
                return []
        elif output_uri_type == "item":
            if input_uri_type == "collection":
                query = prepareQuery("""select ?item where{
                                                    ?collection a dcmitype:Collection.
                                                    ?item dc:isPartOf ?collection.
                                                    }""", initNs = {"dc":DC, 
                                                                    "dcmitype":DCMITYPE})
            elif input_uri_type == "itemlist":
                query = prepareQuery("""select ?item where{
                                                    ?itemlistid a localterms:itemList.
                                                    ?item dc:isPartOf ?itemlistid.
                                                    }""", initNs = {"localterms":LOCALTERMS,
                                                                    "dc":DC})
            elif input_uri_type == "annotation":
                query = prepareQuery("""select ?item where{
                                                    ?annCollID dada:annotates ?item.
                                                    ?annotation dada:partof ?annCollID.
                                                    }""", initNs = {"dada":DADA})
            elif input_uri_type == "document":
                query = prepareQuery("""select ?item where{
                                                    ?item ausnc:document ?document.
                                                    }""", initNs = {"ausnc":AUSNC})
            elif input_uri_type == "source":
                query = prepareQuery("""select ?item where{
                                                    ?item ausnc:document ?document.
                                                    ?document dc:source ?source. 
                                                    }""", initNs = {"dc":DC, 
                                                                    "ausnc":AUSNC})
            else:
                return []
        elif output_uri_type == "annotation":
            if input_uri_type == "item":
                query = prepareQuery("""select ?annotation where{
                                                    ?annotation dada:partof ?annCollID.
                                                    ?annCollID dada:annotates ?item.
                                                    }""", initNs = {"dada":DADA})
            else:
                return []
        initBindings={input_uri_type: URIRef(input_uri)}
        results = self.graph.query(query, initBindings=initBindings)
        output = [result[output_uri_type].toPython() for result in results.bindings]
        return output
    
    def _get_id(self, input_uri):
        return input_uri[input_uri.rfind("/")+1:]
        
    def get_user(self, user_email):
        return {
                "@id":"person21",
                "name":"Steve Cassidy",
                "email":"Steve.Cassidy@mq.edu.au"
                }
        
    def get_software(self, software_id):
        return {
                "label":"A python script to parse the annotation",
                "source":"https://github.com/IntersectAustralia/hcsvlab_robochef/commit/2b5baa438bb57687a567ec4b0668b169d349c2ae",
                "@id":"parsedManualAnnotation"
                }
        
    def create_activity(self):
        return {
                "@id":"originalAnnotation12",
                "label":"parsing of the original annotation supplied with the corpus"
                }
        