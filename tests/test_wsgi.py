

import unittest

from webAPI.wsgiapp import *
import requests


class TestWSGI(unittest.TestCase):

    def setUp(self):
        self.api_key = "SMysEekachrdyGfiheGs"
        self.url_prefix = "https://app.alveo.edu.au"
        self.local_prefix = "http://localhost:3000"

    def make_request(self, source, method, url, payload=None, files=None):
        if source == "online":
            prefix = self.url_prefix
        else:
            prefix = self.local_prefix
        headers = {"X-API-KEY": self.api_key, "Accept": "application/json"}
        if payload is not None:
            headers["content-type"] = "application/json"
        if files is not None:
            r = requests.post(prefix + url, headers=headers, files=files)
        elif method == "get":
            r = requests.get(prefix + url, params=payload, headers=headers)
        elif method == "post":
            r = requests.post(prefix + url, data=json.dumps(payload), headers=headers)
        elif method == "put":
            r = requests.put(prefix + url, data=json.dumps(payload), headers=headers)
        elif method == "delete":
            r = requests.delete(prefix + url, headers=headers)
        return r
        
    def test_version(self): 
        url = "/version"       
        hit = self.make_request("local", "get", url).json()
        compare = {"API version":"V2.0"}
        
        self.assertEqual(hit, compare, "Expected the same output, got %s" % hit)
        
    def test_1download(self):
        headers = {"X-API-KEY": self.api_key, "Accept": "application/json"}
        headers["content-type"] = "application/json"
        payload = {'items':[
                            "https://app.alveo.edu.au/catalog/cooee/2-036",
                            "https://app.alveo.edu.au/catalog/cooee/2-037",
                            "https://app.alveo.edu.au/catalog/cooee/2-038",
                            "https://app.alveo.edu.au/catalog/cooee/2-040"
                            ]}
        answer = requests.post('https://app.alveo.edu.au/catalog/download_items', data=json.dumps(payload), headers=headers)
        with open('temp.zip', 'wb') as f:
            for chunk in answer.iter_content(chunk_size=1024): 
                if chunk:
                    f.write(chunk)
                    f.flush()
        pass
    
    def test_itemlists(self):
        payload = {"name":"mylist"}
        self.make_request("local", "post", "/item_lists/229/create", payload)
        payload = {"name":"mySecondlist"}
        self.make_request("local", "post", "/item_lists/230/create", payload)
        
        url = "/item_lists"
        hit = self.make_request("local", "get", url).json()
        compare = self.make_request("online", "get", url).json()
        
        h1 = type(hit).__name__
        c1 = "dict"
        self.assertEqual(h1, c1, "Expected %s; got %s." % (c1, h1))
        
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
        
        self.make_request("local", "delete", "/item_lists/229")
        self.make_request("local", "delete", "/item_lists/230")
        
    def test_itemlist(self):
        payload = {"name":"mylist"}
        self.make_request("local", "post", "/item_lists/229/create", payload)
        payload = {"name":"mySecondlist"}
        self.make_request("local", "post", "/item_lists/230/create", payload)
        
        hit = self.make_request("local", "get", "/item_lists/229").json()
        compare = self.make_request("online", "get", "/item_lists/64").json()
        
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
        hit = self.make_request("local", "get", url).json()
        compare = self.make_request("online", "get", url).json()
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
        hit = self.make_request("local", "get", url).text[31:51]
        compare = self.make_request("online", "get", url).text[30:50]
        
        self.assertEqual(hit, compare, "Expected the same output")
        
    def test_document(self):
        url = "/catalog/cooee/1-010/document/1-010-plain.txt"
        hit = self.make_request("local", "get", url).text[31:51]
        compare = self.make_request("online", "get", url).text[34:54]
        
        self.assertEqual(hit, compare, "Expected the same output")
        
    def test_annotations(self):
        url = "/catalog/cooee/1-012/annotations"
        hit = self.make_request("local", "get", url).json()
        compare = self.make_request("online", "get", url).json()
        
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
        hit = self.make_request("local", "get", url).json()
        compare = self.make_request("online", "get", url).json()
        
        h1 = type(hit)
        c1 = type(compare)
        self.assertEqual(h1, c1, "Expected dict for both; got local:%s, online:%s." % (h1, c1))
        
        h1 = hit.keys()
        c1 = compare.keys()
        for key in c1:
            self.assertIn(key, h1, "Expected local output to include %s" % key)
            
        h1 = type(hit["annotation_types"])
        c1 = type(compare["annotation_types"])
        self.assertEqual(h1, c1, "Expected list for both; got local:%s, online:%s." % (h1, c1))
        
        h1 = hit["annotation_types"]
        c1 = compare["annotation_types"]
        for item in c1:
            self.assertIn(item, h1, "Expected local output to include %s" % item)
            
    def test_share_item_list(self):
        payload = {"name":"mylist"}
        self.make_request("local", "post", "/item_lists/229/create", payload)
        url = "/item_lists/229/share"
        hit = self.make_request("local", "post", url).json()
        compare = {"success":"Item list mylist is shared. Any user in the application will be able to see it."}
        
        self.assertEqual(hit, compare, "Expected the same output, got %s" % hit)
        
    def test_unshare_item_list(self):
        payload = {"name":"mylist"}
        self.make_request("local", "post", "/item_lists/229/create", payload)
        url = "/item_lists/229/share"
        self.make_request("local", "post", url).json()
        url = "/item_lists/229/unshare"
        hit = self.make_request("local", "post", url).json()
        compare = {"success":"Item list mylist is not being shared anymore."}
        
        self.assertEqual(hit, compare, "Expected the same output, got %s" % hit)
        
    def test_add_to_item_list(self):
        self.make_request("local", "delete", "/item_lists/229")
        payload = {"name":"mylist"}
        self.make_request("local", "post", "/item_lists/229/create", payload)
        url = "/item_lists"
        payload = {
                   "name":"mylist",
                   "num_results":2,
                   "items":[
                            "/catalog/cooee/1-010",
                            "/catalog/cooee/1-011"
                            ]
                   }
        hit = self.make_request("local", "post", url, payload).json()
        compare = {"success":"2 items added to existing item list mylist"}
        
        self.assertEqual(hit, compare, "Expected the same output, got %s" % hit)
        
        url = "/item_lists/229"
        hit = self.make_request("local", "get", url).json()
        
        h1 = len(hit["items"])
        c1 = 2
        self.assertEqual(h1, c1, "Expected the same result, got %s" % h1)
        
    def test_clear_item_list(self):
        self.make_request("local", "delete", "/item_lists/229")
        payload = {"name":"mylist"}
        self.make_request("local", "post", "/item_lists/229/create", payload)
        url = "/item_lists"
        payload = {
                   "name":"mylist",
                   "num_results":2,
                   "items":[
                            "/catalog/cooee/1-010",
                            "/catalog/cooee/1-011"
                            ]
                   }
        self.make_request("local", "post", url, payload)
        url = "/item_lists/229/clear"
        hit = self.make_request("local", "post", url).json()
        compare = {"success":"2 cleared from item list mylist"}
        
        self.assertEqual(hit, compare, "Expected the same result, got %s" % hit)
        
    def test_rename_item_list(self):
        payload = {"name":"emtylist"}
        self.make_request("local", "post", "/item_lists/230/create", payload)
        url = "/item_lists/230"
        payload = {"name":"new name"}
        hit = self.make_request("local", "put", url, payload).json()
        compare = {
                    "name":"new name",
                    "num_items":0,
                    "items":[]
                    }
        self.assertEqual(hit, compare, "Expected %s, got %s" %(compare, hit))
        
        hit = self.make_request("local", "get", url).json()["name"]
        compare = "new name"
        self.assertEqual(hit, compare, "Expected %s, got %s" %(compare, hit))
        
    def test_upload_annotation(self):
        filename = "1-010-newAnn"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        files = {'file': open(filepath, 'rb')}
        url = "/catalog/cooee/1-010/annotations"
        
        hit = self.make_request("local", "post", url, files=files).json()
        compare = {"success":"file 1-010-newAnn uploaded successfully"}
        self.assertEqual(hit, compare, "Expected the same output, got %s" % hit)
        
    
    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()