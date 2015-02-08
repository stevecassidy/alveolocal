from rdflib.graph import Graph
import os


class Store(object):
    
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