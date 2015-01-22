

import unittest

from alveolocal.wsgiapp import *
import requests


class TestAlveolocal(unittest.TestCase):

    def setUp(self):
        self.api_key = "SMysEekachrdyGfiheGs"
        self.url_prefix = "https://app.alveo.edu.au"
        self.local_prefix = "http://localhost:3000"

    def make_request(self, source, method, url, payload):
        if source == "online":
            prefix = self.url_prefix
        else:
            prefix = self.local_prefix
        headers = {"X-API-KEY": self.api_key, "Accept": "application/json"}
        if method == "get":
            r = requests.get(prefix + url, params=payload, headers=headers)
        elif method == "post":
            r = requests.post(prefix + url, data=json.dumps(payload), headers=headers)
        elif method == "put":
            r = requests.put(prefix + url, data=json.dumps(payload), headers=headers)
        return r
        
    def test_version(self): 
        url = "/version"       
        hit = self.make_request("local", "get", url, None).json()
        compare = self.make_request("online", "get", url, None).json()
        
        self.assertEqual(hit, compare, "Expected the same output")
        
    def test_itemlists(self):
        url = "/item_lists"
        hit = self.make_request("local", "get", url, None).json()
        compare = self.make_request("online", "get", url, None).json()
        
        h1 = type(hit)
        c1 = type(compare)
        self.assertEqual(h1, c1, "Expected dict for both; got local:%s, online:%s." % (h1, c1))
        
        h1 = hit.keys()
        c1 = compare.keys()
        for key in c1:
            self.assertIn(key, h1, "Expected local output to include %s" % key)
            
        h1 = type(hit["shared"])
        c1 = type(compare["shared"])
        self.assertEqual(h1, c1, "Expected list for both; got local:%s, online:%s." % (h1, c1))
        
        h1 = type(hit["shared"][0])
        c1 = type(compare["shared"][0])
        self.assertEqual(h1, c1, "Expected dict for both; got local:%s, online:%s." % (h1, c1))
        
        h1 = hit["shared"][0].keys()
        c1 = compare["shared"][0].keys()
        for key in c1:
            self.assertIn(key, h1, "Expected local output to include %s" % key)
        
    def test_itemlist(self):
        hit = self.make_request("local", "get", "/item_lists/1", None).json()
        compare = self.make_request("online", "get", "/item_lists/64", None).json()
        
        h1 = type(hit)
        c1 = type(compare)
        self.assertEqual(h1, c1, "Expected dict for both; got local:%s, online:%s." % (h1, c1))
        
        h1 = hit.keys()
        c1 = compare.keys()
        for key in c1:
            self.assertIn(key, h1, "Expected local output to include %s" % key)
        
        h1 = type(hit["items"])
        c1 = type(compare["items"])
        self.assertEqual(h1, c1, "Expected list for both; got local:%s, online:%s." % (h1, c1))
        
    def test_metadata(self):
        url = "/catalog/cooee/1-010"
        hit = self.make_request("local", "get", url, None).json()
        compare = self.make_request("online", "get", url, None).json()
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
        
        h1 = type(hit)
        c1 = type(compare)
        self.assertEqual(h1, c1, "Expected dict for both; got local:%s, online:%s." % (h1, c1))
        
        h1 = hit.keys()
        c1 = compare.keys()
        for key in c1:
            self.assertIn(key, h1, "Expected local output to include %s" % key)
            
        h1 = type(hit["alveo:metadata"])
        c1 = type(compare["alveo:metadata"])
        self.assertEqual(h1, c1, "Expected dict for both; got local:%s, online:%s." % (h1, c1))
        
        h1 = hit["alveo:metadata"].keys()
        for key in meta_required:
            self.assertIn(key, h1, "Expected local output to include %s" % key)
            
        h1 = type(hit["alveo:documents"])
        c1 = type(compare["alveo:documents"])
        self.assertEqual(h1, c1, "Expected list for both; got local:%s, online:%s." % (h1, c1))
        
        h1 = type(hit["alveo:documents"][0])
        c1 = type(compare["alveo:documents"][0])
        self.assertEqual(h1, c1, "Expected dict for both; got local:%s, online:%s." % (h1, c1))
        
        h1 = hit["alveo:documents"][0].keys()
        c1 = compare["alveo:documents"][0].keys()
        for key in c1:
            self.assertIn(key, h1, "Expected local output to include %s" % key)
            
    def test_primary_text(self):
        url = "/catalog/cooee/1-010/primary_text"
        hit = self.make_request("local", "get", url, None).text[31:51]
        compare = self.make_request("online", "get", url, None).text[30:50]
        
        self.assertEqual(hit, compare, "Expected the same output")
        
    def test_document(self):
        url = "/catalog/cooee/1-010/document/1-010-plain.txt"
        hit = self.make_request("local", "get", url, None).text[31:51]
        compare = self.make_request("online", "get", url, None).text[34:54]
        
        self.assertEqual(hit, compare, "Expected the same output")
        
    def test_annotation_context(self):
        url = "/schema/json-ld"
        hit = self.make_request("local", "get", url, None).json()
        compare = self.make_request("online", "get", url, None).json()
        
        self.assertEqual(hit, compare, "Expected the same output")
        
    def test_annotations(self):
        url = "/catalog/cooee/1-010/annotations"
        hit = self.make_request("local", "get", url, None).json()
        compare = self.make_request("online", "get", url, None).json()
        
        h1 = type(hit)
        c1 = type(compare)
        self.assertEqual(h1, c1, "Expected dict for both; got local:%s, online:%s." % (h1, c1))
        
        h1 = hit.keys()
        c1 = compare.keys()
        for key in c1:
            self.assertIn(key, h1, "Expected local output to include %s" % key)
            
        h1 = type(hit["commonProperties"])
        c1 = type(compare["commonProperties"])
        self.assertEqual(h1, c1, "Expected dict for both; got local:%s, online:%s." % (h1, c1))
        
        h1 = hit["commonProperties"].keys()
        for key in compare["commonProperties"].keys():
            self.assertIn(key, h1, "Expected local output to include %s" % key)
            
        h1 = type(hit["alveo:annotations"])
        c1 = type(compare["alveo:annotations"])
        self.assertEqual(h1, c1, "Expected list for both; got local:%s, online:%s." % (h1, c1))
        
        h1 = type(hit["alveo:annotations"][0])
        c1 = type(compare["alveo:annotations"][0])
        self.assertEqual(h1, c1, "Expected dict for both; got local:%s, online:%s." % (h1, c1))
        
        h1 = hit["alveo:annotations"][0].keys()
        for key in compare["alveo:annotations"][0].keys():
            self.assertIn(key, h1, "Expected local output to include %s" % key)
            
    def test_annotation_types(self):
        url = "/catalog/cooee/1-010/annotations/types"
        hit = self.make_request("local", "get", url, None).json()
        compare = self.make_request("online", "get", url, None).json()
        
        return
    
    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()