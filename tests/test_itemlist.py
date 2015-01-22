import unittest

from alveolocal.itemlist import ItemListFactory


class TestItemList(unittest.TestCase):

    def setUp(self):
        self.factory = ItemListFactory()

    def test_1_empty_database(self):
        self.assertEqual(self.factory.get_item_lists(), [], "expected an empty list")
        
    def test_2_create_item_list(self):
        self.factory.create_item_list("firstItemList", "my itemlist")
        self.assertEqual("my itemlist", self.factory.get_item_list("firstItemList")["name"], "expected the name of the itemlist to be 'my itemlist'")
        
    def test_3_empty_item_list(self):
        self.factory.create_item_list("firstItemList", "my itemlist")
        self.assertEqual(0, self.factory.get_item_list("firstItemList")["num_items"], "expected the itemlist to have no items")
        
    def test_4_add_items(self):
        self.factory.create_item_list("firstItemList", "my itemlist")
        self.factory.add_to_item_list("firstItemList", "item1")
        self.factory.add_to_item_list("firstItemList", "item2")
        self.factory.add_to_item_list("firstItemList", "item3")
        self.factory.add_to_item_list("firstItemList", "item4")
        self.assertEqual(4, self.factory.get_item_list("firstItemList")["num_items"], "expected the itemlist to have 4 items")
        self.assertIn("item1", self.factory.get_item_list("firstItemList")["items"], "expected 'item1' to be in the items")
        self.assertNotIn("item5", self.factory.get_item_list("firstItemList")["items"], "expected 'item5' not to be in the items")
        
    def test_5_get_item_lists(self):
        self.factory.create_item_list("firstItemList", "my itemlist")
        self.factory.add_to_item_list("firstItemList", "item1")
        self.factory.add_to_item_list("firstItemList", "item2")
        self.factory.add_to_item_list("firstItemList", "item3")
        self.factory.add_to_item_list("firstItemList", "item4")
        self.factory.create_item_list("secondItemList", "your itemlist")
        self.factory.add_to_item_list("secondItemList", "item5")
        self.factory.add_to_item_list("secondItemList", "item6")
        self.factory.add_to_item_list("secondItemList", "item7")
        self.assertEqual(2, len(self.factory.get_item_lists()), "expected two item lists")
        self.assertIn("firstItemList", [itemlist["item_list_url"] for itemlist in self.factory.get_item_lists()], "expected 'firstItemList' to be in the list")
        self.assertNotIn("thirdItemList", [itemlist["item_list_url"] for itemlist in self.factory.get_item_lists()], "expected 'thirdItemList' to be in the list")
        

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()