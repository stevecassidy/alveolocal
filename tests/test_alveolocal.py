#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_alveolocal
----------------------------------

Tests for `alveolocal` module.
"""

import unittest
import os
import json 


from alveolocal import API

TEST_DATA = os.path.join(os.path.dirname(__file__), "data")


class TestAlveolocalLoad(unittest.TestCase):

    def setUp(self):
        
        self.api = API()
        
        
    def test_attach_directory(self):
        """we can attach a directory containing RDF files"""
        
        # check the number of triples loaded
        self.assertEqual(2355, self.api.attach_directory(TEST_DATA))


    def test_version(self):
        """we return the right version string"""
        
        
        self.assertEqual("V2.0", self.api.version())


class TestAlveolocal(unittest.TestCase):

    def setUp(self):
        
        self.api = API()
        self.api.attach_directory(TEST_DATA)


    def test_item_base_url(self):
        """generating the right url for an item"""
        
        itemuri = "http://ns.ausnc.org.au/corpora/cooee/items/1-012"
        baseurl = "http://localhost:3000/catalog/cooee/1-012"
        
        self.assertEqual(baseurl, self.api._base_url(itemuri))
        
    def test_get_item_lists(self):
        """test retrieval of item lists"""
                
        # get item lists returns a list
        self.assertEqual(list, type(self.api.get_item_lists()))
        

    def test_get_item_metadata(self):
        """we can get the metadata for an item"""

        fp = open(os.path.join(TEST_DATA, "cooee-0-012.json"))
        ref = json.load(fp)
        fp.close()
                
        itemuri = "http://ns.ausnc.org.au/corpora/cooee/items/1-012"
        
        meta = self.api.get_item_metadata(itemuri)
        
        self.assertEqual(dict, type(meta))
        for key in ref.keys():
            self.assertIn(key, meta)
        
        import pprint
        #pprint.pprint(ref)

       # pprint.pprint(meta)
        
        for key in ref['alveo:metadata'].keys():
            self.assertIn(key, meta['alveo:metadata'])
        
        
        # document check
        self.assertEqual(len(ref['alveo:documents']), len(meta['alveo:documents']))
        for doc in meta['alveo:documents']:
            self.assertEqual(str, type(doc[u'alveo:url']))
            self.assertTrue(doc[u'alveo:url'].startswith('http'))
        
    
    def test_get_primary_text(self):
        """we can return the text of the primary document"""

        itemuri = "http://ns.ausnc.org.au/corpora/cooee/items/1-012"
        
        text = self.api.get_primary_text(itemuri)
        
        self.assertEqual('\r\n\r\n\r\nI take the fir', text[:20])
        self.assertEqual(2394, len(text))
        
        # non-existant item has no primary text
        
        text = self.api.get_primary_text("http://example.org/foo")
        
        self.assertEqual(None, text)
        
        

    def test_get_annotations(self):
        """we can get the annotations for an item"""

        itemuri = "http://ns.ausnc.org.au/corpora/cooee/items/1-012"
        docurl = "http://localhost:3000/cooee/1-012-plain.txt"

        ann = self.api.get_annotations(itemuri)
        
        self.assertIn('alveo:annotations', ann)
        self.assertIn('commonProperties', ann)
        self.assertIn('@context', ann)
        
        self.assertEqual(2, len(ann['alveo:annotations']))
        
        self.assertEqual('dada:TextAnnotation', ann['alveo:annotations'][0]['@type'])
        
        self.assertEqual(docurl, ann['commonProperties']['alveo:annotates'])
        



    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()