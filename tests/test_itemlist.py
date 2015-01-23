import unittest

from alveolocal.itemlist import ItemListFactory
import redis
import sqlite3


class TestItemList(unittest.TestCase):

    def setUp(self):
        self.methods = ["redis", "sqlite"]

    def prepare(self, method):
        if method == "redis":
            db = redis.StrictRedis(host="localhost", port=6379, db=0)
            db.flushall()
        elif method == "sqlite":
            conn = sqlite3.connect('itemlists.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM item")
            cursor.execute("DELETE FROM itemlist")
            conn.commit()
        elif method == "rdf":
            pass
        
    def test_1_empty_database(self):
        for method in self.methods:
            factory = ItemListFactory(method)
            self.prepare(method)
            
            hit = factory.get_item_lists()
            compare = {"shared":[], "own":[]}
            self.assertEqual(hit, compare, "expected no item lists")
        
    def test_2_create_item_list(self):
        for method in self.methods:
            factory = ItemListFactory(method)
            self.prepare(method)
            factory.create_item_list("http://localhost:3000/item_lists/1", "first item list", "shared")
            
            hit = factory.get_item_list("http://localhost:3000/item_lists/1")["name"]
            compare = "first item list"
            self.assertEqual(hit, compare, "expected the name of the itemlist to be '%s'" % compare)
            
            hit = factory.get_item_list("http://localhost:3000/item_lists/1")["shared"]
            compare = "shared"
            self.assertEqual(hit, compare, "expected the shared status of the itemlist to be '%s'" % compare)
        
        
        
    def test_3_empty_item_list(self):
        for method in self.methods:
            factory = ItemListFactory(method)
            self.prepare(method)
            factory.create_item_list("http://localhost:3000/item_lists/1", "first item list", "shared")
            
            hit = factory.get_item_list("http://localhost:3000/item_lists/1")["num_items"]
            compare = 0
            self.assertEqual(hit, compare, "expected the itemlist to have %s items" % str(compare))
        
    def test_4_add_items(self):
        for method in self.methods:
            factory = ItemListFactory(method)
            self.prepare(method)
            factory.create_item_list("http://localhost:3000/item_lists/1", "first item list", "shared")
            factory.add_to_item_list("http://localhost:3000/item_lists/1", "http://localhost:3000/catalog/cooee/items/1-010")
            factory.add_to_item_list("http://localhost:3000/item_lists/1", "http://localhost:3000/catalog/cooee/items/1-011")
            factory.add_to_item_list("http://localhost:3000/item_lists/1", "http://localhost:3000/catalog/cooee/items/1-012")
            factory.add_to_item_list("http://localhost:3000/item_lists/1", "http://localhost:3000/catalog/cooee/items/1-013")
            
            itemlist = factory.get_item_list("http://localhost:3000/item_lists/1")
            hit = itemlist["num_items"]
            compare = 4
            self.assertEqual(hit, compare, "expected the itemlist to have %s items" % str(compare))
            
            hit = itemlist["items"]
            compare = "http://localhost:3000/catalog/cooee/items/1-010"
            self.assertIn(compare, hit, "expected '%s' to be in the items" % compare)
            
            hit = itemlist["items"]
            compare = "http://localhost:3000/catalog/cooee/items/1-015"
            self.assertNotIn(compare, hit, "expected '%s' not to be in the items" % compare)
        
    def test_5_get_item_lists(self):
        for method in self.methods:
            factory = ItemListFactory(method)
            self.prepare(method)
            factory.create_item_list("http://localhost:3000/item_lists/1", "first item list", "shared")
            factory.add_to_item_list("http://localhost:3000/item_lists/1", "http://localhost:3000/catalog/cooee/items/1-010")
            factory.add_to_item_list("http://localhost:3000/item_lists/1", "http://localhost:3000/catalog/cooee/items/1-011")
            factory.add_to_item_list("http://localhost:3000/item_lists/1", "http://localhost:3000/catalog/cooee/items/1-012")
            factory.add_to_item_list("http://localhost:3000/item_lists/1", "http://localhost:3000/catalog/cooee/items/1-013")
            factory.create_item_list("http://localhost:3000/item_lists/2", "second item list", "own")
            factory.add_to_item_list("http://localhost:3000/item_lists/2", "http://localhost:3000/catalog/cooee/items/1-013")
            factory.add_to_item_list("http://localhost:3000/item_lists/2", "http://localhost:3000/catalog/cooee/items/1-014")
            factory.add_to_item_list("http://localhost:3000/item_lists/2", "http://localhost:3000/catalog/cooee/items/1-015")
            
            itemlists = factory.get_item_lists()
            listitemlists = []
            for status in ["shared", "own"]:
                listitemlists.extend(itemlists[status])
            hit = len(listitemlists)
            compare = 2
            self.assertEqual(hit, compare, "expected %s item lists" % str(compare))
            
            hit = [itemlist["item_list_url"] for itemlist in listitemlists]
            compare = "http://localhost:3000/item_lists/1"
            self.assertIn(compare, hit, "expected '%s' to be in the list" % compare)
            
            compare = "http://localhost:3000/item_lists/3"
            self.assertNotIn(compare, hit, "expected '%s' not to be in the list" % compare)
            

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()