method = None
try:
    import redis
    method = "redis"
except:
    import sqlite3
    method = "sqlite"
    
class RedisDb(object):
    
    def __init__(self):
        self.db = redis.StrictRedis(host="localhost", port=6379, db=0)
        self.db.flushall()
        
    def get_item_lists(self):
        return [itemlistid.decode("utf-8") for itemlistid in self.db.keys()]
    
    def create_item_list(self, itemlist_id, itemlist_name):
        self.db.rpush(itemlist_id, itemlist_name)
    
    def add_to_item_list(self, itemlist_id, item_id):
        self.db.rpushx(itemlist_id, item_id)
        
    def get_items(self, itemlist_id):
        return [item.decode("utf-8") for item in self.db.lrange(itemlist_id, 1, -1)]
    
    def get_item_list_name(self, itemlist_id):
        return self.db.lrange(itemlist_id, 0, 1)[0].decode("utf-8")
    
class SqliteDb(object):
    
    def __init__(self):
        self._create_database()
        
    def _create_database(self):
        conn = sqlite3.connect('itemlists.db')
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS [itemlist] 
                        (
                        [itemlistid] TEXT PRIMARY KEY, 
                        [itemlistname] TEXT
                        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS [item] 
                        (
                        [itemid] TEXT, 
                        [itemlistid] TEXT, 
                        CONSTRAINT [] PRIMARY KEY ([itemid], [itemlistid])
                        )""")
        conn.commit()
        conn.close()
        self.conn = sqlite3.connect('itemlists.db')
        self.cursor = self.conn.cursor()
        
    def get_item_lists(self):
        self.cursor.execute("SELECT itemlistid FROM itemlist")
        return [itemlistid[0] for itemlistid in self.cursor.fetchall()]
    
    def create_item_list(self, itemlist_id, itemlist_name):
        self.cursor.execute("INSERT INTO itemlist VALUES (?, ?)", (itemlist_id, itemlist_name))
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
            
class ItemListFactory():
    
    def __init__(self):
        if method == "redis":
            self.db = RedisDb()
        else:
            self.db = SqliteDb()
            
    def get_item_lists(self):
        itemlists = self.db.get_item_lists()
        output = []
        for itemlistid in itemlists:
            itemlist = {
                        "name":self.db.get_item_list_name(itemlistid),
                        "item_list_url":itemlistid,
                        "num_items":len(self.db.get_items(itemlistid))
                        }
            output.append(itemlist)
        return output
    
    def get_item_list(self, itemlistid):
        items = self.db.get_items(itemlistid)
        output = {
                  "name":self.db.get_item_list_name(itemlistid),
                  "num_items":len(items),
                  "items":items
                  }
        return output
    
    def create_item_list(self, itemlistid, itemlistname):
        self.db.create_item_list(itemlistid, itemlistname)
        
    def add_to_item_list(self, itemlistid, itemid):
        self.db.add_to_item_list(itemlistid, itemid)

                
    