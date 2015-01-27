import os
import sqlite3

from rdflib import Graph
from rdflib.term import URIRef, Literal
import redis

from namespaces import RDF, DC, LOCALTERMS


class RedisDb(object):
    
    def __init__(self):
        self.db = redis.StrictRedis(host="localhost", port=6379, db=0)
        
    def get_item_lists(self):
        return [itemlistid.decode("utf-8") for itemlistid in self.db.keys()]
    
    def create_item_list(self, itemlist_id, itemlist_name, shared):
        self.db.rpush(itemlist_id, itemlist_name)
        self.db.rpushx(itemlist_id, shared)
    
    def add_to_item_list(self, itemlist_id, item_id):
        self.db.rpushx(itemlist_id, item_id)
        
    def get_items(self, itemlist_id):
        return [item.decode("utf-8") for item in self.db.lrange(itemlist_id, 2, -1)]
    
    def get_item_list_name(self, itemlist_id):
        return self.db.lrange(itemlist_id, 0, 1)[0].decode("utf-8")
    
    def get_item_list_shared(self, itemlist_id):
        return self.db.lrange(itemlist_id, 1, 2)[0].decode("utf-8")
    
    def change_item_list_shared(self, itemlist_id, shared):
        self.db.lset(itemlist_id, 1, shared)
        
    def delete_item_list(self, itemlist_id):
        self.db.delete(itemlist_id)
        
    def remove_item(self, itemlist_id, item_id):
        self.db.lrem(itemlist_id, 1, item_id)
        
    def clear_item_list(self, itemlist_id):
        self.db.ltrim(itemlist_id, 0, 1)
    
class SqliteDb(object):
    
    def __init__(self, dirname):
        self._create_database(dirname)
        
    def _create_database(self, dirname):
        conn = sqlite3.connect(os.path.join(dirname, 'itemlists.db'))
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
        cursor.execute("""CREATE TABLE IF NOT EXISTS [itemlist] 
                        (
                        [itemlistid] TEXT PRIMARY KEY, 
                        [itemlistname] TEXT,
                        [itemlistshared] TEXT
                        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS [item] 
                        (
                        [itemid] TEXT, 
                        [itemlistid] TEXT, 
                        CONSTRAINT [] PRIMARY KEY ([itemid], [itemlistid])
                        FOREIGN KEY(itemlistid) REFERENCES itemlist(itemlistid) ON DELETE CASCADE
                        )""")
        conn.commit()
        conn.close()
        self.conn = sqlite3.connect(os.path.join(dirname, 'itemlists.db'))
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")
        self.conn.commit()
        
    def get_item_lists(self):
        self.cursor.execute("SELECT itemlistid FROM itemlist")
        return [itemlistid[0] for itemlistid in self.cursor.fetchall()]
    
    def create_item_list(self, itemlist_id, itemlist_name, shared):
        self.cursor.execute("INSERT INTO itemlist VALUES (?, ?, ?)", (itemlist_id, itemlist_name, shared))
        self.conn.commit()
    
    def add_to_item_list(self, itemlist_id, item_id):
        self.cursor.execute("INSERT INTO item VALUES (?, ?)", (item_id, itemlist_id))
        self.conn.commit()
        
    def get_items(self, itemlist_id):
        self.cursor.execute("SELECT itemid FROM item WHERE itemlistid = ?", (itemlist_id,))
        return [itemid[0] for itemid in self.cursor.fetchall()]

    def get_item_list_name(self, itemlist_id):
        self.cursor.execute("SELECT itemlistname FROM itemlist WHERE itemlistid = ?", (itemlist_id,))
        result = self.cursor.fetchone()
        if result is not None:
            return result[0]
        
    def get_item_list_shared(self, itemlist_id):
        self.cursor.execute("SELECT itemlistshared FROM itemlist WHERE itemlistid = ?", (itemlist_id,))
        result = self.cursor.fetchone()
        if result is not None:
            return result[0]
    
    def change_item_list_shared(self, itemlist_id, shared):
        self.cursor.execute("UPDATE itemlist SET itemlistshared = ? WHERE itemlistid = ?", (shared, itemlist_id))
        self.conn.commit()
        
    def delete_item_list(self, itemlist_id):
        self.cursor.execute("DELETE FROM itemlist WHERE itemlistid = ?", (itemlist_id,))
        self.conn.commit()
        
    def remove_item(self, itemlist_id, item_id):
        self.cursor.execute("DELETE FROM item WHERE itemlistid = ? AND itemid = ?", (itemlist_id, item_id))
        self.conn.commit()
        
    def clear_item_list(self, itemlist_id):
        self.cursor.execute("DELETE FROM item WHERE itemlistid = ?", (itemlist_id,))
        self.conn.commit()
            
class RdfDb(object):
        
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
        
    def _save_item_list(self, item_list_id, dir_name):
        """Save an item list into a file in a given directory"""
        
        subgraph = Graph()
        subgraph.bind("localterms", LOCALTERMS)
        subgraph += self.graph.triples((URIRef(item_list_id), None, None))
        subgraph += self.graph.triples((None, None, URIRef(item_list_id)))
        name = self.graph.value(URIRef(item_list_id), LOCALTERMS.itemListName).toPython()
        subgraph.serialize(os.path.join(dir_name, "%s.n3" % name), format="n3")
        
    def get_item_lists(self):
        """Return a list of currently defined item lists"""
        
        return [item_list_id.toPython() for item_list_id in self.graph.subjects(RDF.type, LOCALTERMS.itemList)]
    
    def create_item_list(self, itemlist_id, itemlist_name, shared):
        """Create new item list with the given name"""
        
        self.graph.add((URIRef(itemlist_id), RDF.type, LOCALTERMS.itemList))
        self.graph.add((URIRef(itemlist_id), LOCALTERMS.itemListName, Literal(itemlist_name)))
        self.graph.add((URIRef(itemlist_id), LOCALTERMS.sharedStatus, Literal(shared)))
        self._save_item_list(itemlist_id, self.basedir)
    
    def add_to_item_list(self, itemlist_id, item_id):
        """Add an item to an item list"""
        
        self.graph.add((URIRef(item_id), DC.isPartOf, URIRef(itemlist_id)))
        self._save_item_list(itemlist_id, self.basedir)
        
    def get_items(self, itemlist_id):
        """Return items of a given item list"""
        
        return [s.toPython() for s in self.graph.subjects(DC.isPartOf, URIRef(itemlist_id))]
    
    def get_item_list_name(self, itemlist_id):
        """Return name of a given item list"""
        
        return self.graph.value(URIRef(itemlist_id), LOCALTERMS.itemListName).toPython()
    
    def get_item_list_shared(self, itemlist_id):
        """Return shared status of a given item list"""
        
        return self.graph.value(URIRef(itemlist_id), LOCALTERMS.sharedStatus).toPython()
    
    def change_item_list_shared(self, itemlist_id, shared):
        """Update shared status of a given item list"""
        
        self.graph.set((URIRef(itemlist_id), LOCALTERMS.sharedStatus, Literal(shared)))
        self._save_item_list(itemlist_id, self.basedir)
        
    def delete_item_list(self, itemlist_id):
        """Delete a given item list"""
        
        os.remove(os.path.join(self.basedir, "%s.n3" % self.get_item_list_name(itemlist_id)))
        self.graph.remove((URIRef(itemlist_id), None, None))
        self.graph.remove((None, None, URIRef(itemlist_id)))
        
        
    def remove_item(self, itemlist_id, item_id):
        """Remove an item from the item list"""
        
        self.graph.remove((URIRef(item_id), DC.isPartOf, URIRef(itemlist_id)))
        self._save_item_list(itemlist_id, self.basedir)
        
    def clear_item_list(self, itemlist_id):
        """Remove all items from the item list"""
        
        self.graph.remove((None, DC.isPartOf, URIRef(itemlist_id)))
        self._save_item_list(itemlist_id, self.basedir)

class ItemListFactory():
    
    def __init__(self, method, dirname):
        if method == "redis":
            self.db = RedisDb()
        elif method == "sqlite":
            self.db = SqliteDb(dirname)
        elif method == "rdf":
            self.db = RdfDb()
            self.db.attach_directory(dirname)
            
    def get_item_lists(self):
        itemlists = self.db.get_item_lists()
        output = {"shared":[], "own":[]}
        for itemlistid in itemlists:
            itemlist = {
                        "name":self.db.get_item_list_name(itemlistid),
                        "shared":self.db.get_item_list_shared(itemlistid),
                        "item_list_url":itemlistid,
                        "num_items":len(self.db.get_items(itemlistid))
                        }
            output[itemlist["shared"]].append(itemlist)
        return output
    
    def get_item_list(self, itemlistid):
        items = self.db.get_items(itemlistid)
        output = {
                  "name":self.db.get_item_list_name(itemlistid),
                  "shared":self.db.get_item_list_shared(itemlistid),
                  "num_items":len(items),
                  "items":items
                  }
        return output
    
    def create_item_list(self, itemlistid, itemlistname, shared):
        self.db.create_item_list(itemlistid, itemlistname, shared)
        
    def add_to_item_list(self, itemlistid, itemid):
        self.db.add_to_item_list(itemlistid, itemid)
        
    def share_item_list(self, itemlist_id):
        self.db.change_item_list_shared(itemlist_id, "shared")
        
    def unshare_item_list(self, itemlist_id):
        self.db.change_item_list_shared(itemlist_id, "own")
        
    def delete_item_list(self, itemlist_id):
        self.db.delete_item_list(itemlist_id)
        
    def clear_item_list(self, itemlist_id):
        self.db.clear_item_list(itemlist_id)

                
    