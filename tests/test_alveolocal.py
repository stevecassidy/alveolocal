#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_alveolocal
----------------------------------

Tests for `alveolocal` module.
"""

import json 
import os
import unittest

from alveolocal import API
from datetime import datetime


TEST_DATA = os.path.join(os.path.dirname(__file__), "data")


class TestAlveolocalLoad(unittest.TestCase):

    def setUp(self):
        
        self.api = API()
        
        
    def test_attach_directory(self):
        """we can attach a directory containing RDF files"""
        
        # check the number of triples loaded
        self.assertEqual(7628, self.api.attach_directory(TEST_DATA))


    def test_version(self):
        """we return the right version string"""
        
        
        self.assertEqual("V2.0", self.api.version())


class TestAlveolocal(unittest.TestCase):

    def setUp(self):
        
        self.api = API()
        self.api.attach_directory(TEST_DATA)


    def test_item_base_url(self):
        """generating the right url for an item"""
        
        itemuri = "http://localhost:3000/catalog/cooee/1-012"
        baseurl = "http://localhost:3000/catalog/cooee/1-012"
        
        self.assertEqual(baseurl, itemuri)
        
        
    def test_get_collections(self):
        """we can get the list of collections"""
        
        collections = self.api.get_collections()
        
        self.assertEqual(2, len(collections))
        self.assertIn('http://localhost:3000/catalog/mitcheldelbridge', collections)
        self.assertIn('http://localhost:3000/catalog/cooee', collections)
        
    def test_get_collection(self):
        """We can get the details of a collection"""
        
        coluri = 'http://localhost:3000/catalog/cooee'
        
        meta = self.api.get_collection(coluri)
        
        
        self.assertEqual(coluri, meta['collection_url'])
        self.assertEqual('COOEE', meta['collection_name'])
        self.assertEqual(dict, type(meta['metadata']))
        self.assertEqual('2004', meta['metadata']['dc:created'])

    def test_get_item_metadata(self):
        """we can get the metadata for an item"""

        fp = open(os.path.join(TEST_DATA, "cooee-0-012.json"))
        ref = json.load(fp)
        fp.close()
                
        itemuri = "http://localhost:3000/catalog/cooee/items/1-012"
        
        meta = self.api.get_item_metadata(itemuri)
        
        self.assertEqual(dict, type(meta))
        for key in ref.keys():
            self.assertIn(key, meta)
        
        for key in ref['alveo:metadata'].keys():
            self.assertIn(key, meta['alveo:metadata'])
        
        # document check
        self.assertEqual(len(ref['alveo:documents']), len(meta['alveo:documents']))
        for doc in meta['alveo:documents']:
            self.assertEqual(str, type(doc[u'alveo:url']))
            self.assertTrue(doc[u'alveo:url'].startswith('http'), "expected url '%s' to start with http" % doc[u'alveo:url'])
        
    
    def test_get_primary_text(self):
        """we can return the text of the primary document"""

        itemuri = "http://localhost:3000/catalog/cooee/items/1-012"
        
        text = self.api.get_primary_text(itemuri)
        
        self.assertEqual('\r\n\r\n\r\nI take the fir', text[:20])
        self.assertEqual(2394, len(text))
        
        # non-existant item has no primary text
        
        text = self.api.get_primary_text("http://example.org/foo")
        
        self.assertEqual(None, text)
        
        

    def test_get_annotations(self):
        """we can get the annotations for an item"""

        itemuri = "http://localhost:3000/catalog/cooee/items/1-012"
        docurl = "http://localhost:3000/documents/cooee/1-012-plain.txt"

        ann = self.api.get_annotations(itemuri)
        
        self.assertIn('alveo:annotations', ann)
        self.assertIn('commonProperties', ann)
        self.assertIn('@context', ann)
        
        self.assertEqual(2, len(ann['alveo:annotations']))
        
        self.assertEqual('dada:TextAnnotation', ann['alveo:annotations'][0]['@type'])
        
        self.assertEqual(docurl, ann['commonProperties']['alveo:annotates'])
        
        ann = self.api.get_annotations(itemuri, {"user":"Steve.Cassidy@mq.edu.au"})
        ann = self.api.get_annotations(itemuri, {"priorTo":datetime.strptime("2013-12-20T12:20:00", '%Y-%m-%dT%I:%M:%S')})
        
        pass

    def test_search(self):
        """we can search for items"""
        
        query = (('dc:created', '1788'), )
        
        items = self.api.search(query)
        
        self.assertEqual(5, len(items))
        self.assertIn('http://localhost:3000/catalog/cooee/items/1-011', items)

        query = (('dc:created', '1788'), ('cooee:texttype', 'Private Correspondence'))
        items = self.api.search(query)
        
        self.assertEqual(4, len(items))
        self.assertNotIn('http://localhost:3000/catalog/cooee/items/1-013', items)
        self.assertIn('http://localhost:3000/catalog/cooee/items/1-011', items)
        
    def test_search_sparql(self):
        
        query = "select * where {?s <http://purl.org/dc/terms/isPartOf> ?o}"
        collection_name = "cooee"
        result = self.api.search_sparql(collection_name, query)
        
        self.assertIsInstance(result, dict, "Expected dict, got %s" % type(result))
        for key in result.keys():
            self.assertIn(key, ["head", "results"], "Expected %s to be one of the items in the list" % key)
        self.assertIn("vars", result["head"], "Expected to include vars")
        self.assertIn("bindings", result["results"], "Expected to include bindings")
        for binding in result["results"]["bindings"]:
            for var in result["head"]["vars"]:
                self.assertIn(var, binding, "Expected all bindings to include items in vars")
        
    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()