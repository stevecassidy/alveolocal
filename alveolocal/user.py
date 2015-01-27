from rdflib.graph import Graph
import os
from namespaces import LOCALTERMS, RDF, XSD
from rdflib.term import URIRef, Literal


class UserDb(object):
        
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
        
    def _save_user(self, user_id, dir_name):
        """Save an item list into a file in a given directory"""
        
        subgraph = Graph()
        subgraph.bind("localterms", LOCALTERMS)
        subgraph += self.graph.triples((URIRef(user_id), None, None))
        subgraph += self.graph.triples((None, None, URIRef(user_id)))
        name = self.graph.value(URIRef(user_id), LOCALTERMS.username).toPython()
        subgraph.serialize(os.path.join(dir_name, "%s.n3" % name), format="n3")
        
    def get_users(self):
        """Return a list of currently defined item lists"""
        
        return [user_id.toPython() for user_id in self.graph.subjects(RDF.type, LOCALTERMS.user)]
    
    def create_user(self, user_id, username):
        """Create new item list with the given name"""
        
        self.graph.add((URIRef(user_id), RDF.type, LOCALTERMS.user))
        self.graph.add((URIRef(user_id), LOCALTERMS.username, Literal(username)))
        self._save_item_list(user_id, self.basedir)
    
    def add_annotation(self, user_id, annotation_id, date):
        """Add an item to an item list"""
        
        self.graph.add((URIRef(annotation_id), LOCALTERMS.addedOn, Literal(date, datatype=XSD.date)))
        self.graph.add((URIRef(annotation_id), LOCALTERMS.addedBy, URIRef(user_id)))
        self._save_item_list(user_id, self.basedir)
        
    def get_annotations_by_user(self, user_id):
        """Return items of a given item list"""
        
        return [s.toPython() for s in self.graph.subjects(LOCALTERMS.addedBy, URIRef(user_id))]
    
    def get_annotations_by_date(self, date):
        """Return items of a given item list"""
        
        return [s.toPython() for s in self.graph.subjects(LOCALTERMS.addedOn, Literal(date, datatype=XSD.date))]
    
    def get_annotation_user(self, annotation_id):
        """Return name of a given item list"""
        
        return self.graph.value(URIRef(annotation_id), LOCALTERMS.addedBy).toPython()
    
    def get_annotation_date(self, annotation_id):
        """Return shared status of a given item list"""
        
        return self.graph.value(URIRef(annotation_id), LOCALTERMS.addedOn).toPython()
    
