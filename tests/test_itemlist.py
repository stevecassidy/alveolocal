import os
import unittest

from alveolocal.itemlist import ItemListFactory


class TestItemList(unittest.TestCase):

    def setUp(self):
        self.methods = ["redis", "sqlite", "rdf"]
        self.basedir = os.path.join(os.path.dirname(__file__), "data", "itemlists")

    def prepare(self, factory):
        for itemlist_id in factory.db.get_item_lists():
                factory.db.delete_item_list(itemlist_id)
        
    def test_1_empty_database(self):
        for method in self.methods:
            factory = ItemListFactory(method, self.basedir)
            self.prepare(factory)
            
            hit = factory.get_item_lists()
            compare = {"shared":[], "own":[]}
            self.assertEqual(hit, compare, "expected no item lists")
        
    def test_2_create_item_list(self):
        for method in self.methods:
            factory = ItemListFactory(method, self.basedir)
            self.prepare(factory)
            factory.create_item_list("http://localhost:3000/item_lists/1", "first item list", "shared")
            
            hit = factory.get_item_list("http://localhost:3000/item_lists/1")["name"]
            compare = "first item list"
            self.assertEqual(hit, compare, "expected the name of the itemlist to be '%s'" % compare)
            
            hit = factory.get_item_list("http://localhost:3000/item_lists/1")["shared"]
            compare = "shared"
            self.assertEqual(hit, compare, "expected the shared status of the itemlist to be '%s'" % compare)
        
        
        
    def test_3_empty_item_list(self):
        for method in self.methods:
            factory = ItemListFactory(method, self.basedir)
            self.prepare(factory)
            factory.create_item_list("http://localhost:3000/item_lists/1", "first item list", "shared")
            
            hit = factory.get_item_list("http://localhost:3000/item_lists/1")["num_items"]
            compare = 0
            self.assertEqual(hit, compare, "expected the itemlist to have %s items" % str(compare))
        
    def test_4_add_items(self):
        for method in self.methods:
            factory = ItemListFactory(method, self.basedir)
            self.prepare(factory)
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
            factory = ItemListFactory(method, self.basedir)
            self.prepare(factory)
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
            
    def test_6_change_item_list_shared(self):
        for method in self.methods:
            factory = ItemListFactory(method, self.basedir)
            self.prepare(factory)
            
            factory.create_item_list("http://localhost:3000/item_lists/1", "first item list", "shared")
            hit = factory.get_item_list("http://localhost:3000/item_lists/1")["shared"]
            compare = "shared"
            self.assertEqual(hit, compare, "Expected shared status of the item list to be %s" % compare)
            
            factory.unshare_item_list("http://localhost:3000/item_lists/1")
            hit = factory.get_item_list("http://localhost:3000/item_lists/1")["shared"]
            compare = "own"
            self.assertEqual(hit, compare, "Expected shared status of the item list to be %s" % compare)
            
            factory.share_item_list("http://localhost:3000/item_lists/1")
            hit = factory.get_item_list("http://localhost:3000/item_lists/1")["shared"]
            compare = "shared"
            self.assertEqual(hit, compare, "Expected shared status of the item list to be %s" % compare)
            
    def test_7_delete_item_list(self):
        for method in self.methods:
            factory = ItemListFactory(method, self.basedir)
            self.prepare(factory)
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
            
            factory.delete_item_list("http://localhost:3000/item_lists/1")
            itemlists = factory.get_item_lists()
            listitemlists = []
            for status in ["shared", "own"]:
                listitemlists.extend(itemlists[status])
            hit = len(listitemlists)
            compare = 1
            self.assertEqual(hit, compare, "expected %s item lists" % str(compare))
            
            hit = [itemlist["item_list_url"] for itemlist in listitemlists]
            compare = "http://localhost:3000/item_lists/1"
            self.assertNotIn(compare, hit, "expected '%s' not to be in the list" % compare)
            
    def test_8_clear_item_list(self):
        for method in self.methods:
            factory = ItemListFactory(method, self.basedir)
            self.prepare(factory)
            factory.create_item_list("http://localhost:3000/item_lists/1", "first item list", "shared")
            factory.add_to_item_list("http://localhost:3000/item_lists/1", "http://localhost:3000/catalog/cooee/items/1-010")
            factory.add_to_item_list("http://localhost:3000/item_lists/1", "http://localhost:3000/catalog/cooee/items/1-011")
            factory.add_to_item_list("http://localhost:3000/item_lists/1", "http://localhost:3000/catalog/cooee/items/1-012")
            factory.add_to_item_list("http://localhost:3000/item_lists/1", "http://localhost:3000/catalog/cooee/items/1-013")

            items = factory.get_item_list("http://localhost:3000/item_lists/1")["items"]
            hit = len(items)
            compare = 4
            self.assertEqual(hit, compare, "Expected the size of the list to be %s" % str(compare))
            
            factory.clear_item_list("http://localhost:3000/item_lists/1")
            items = factory.get_item_list("http://localhost:3000/item_lists/1")["items"]
            hit = len(items)
            compare = 0
            self.assertEqual(hit, compare, "Expected the size of the list to be %s" % str(compare))
            
    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()