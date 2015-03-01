# -*- coding: utf-8 -*-

from bottle import Bottle, request, abort, response, jinja2_view as view, static_file
from alveolocal import API
import json
import os
from alveolocal.itemlist import ItemListFactory


application = Bottle()
alveo = API()
TEST_DATA = os.path.join(os.path.dirname(__file__), "..", "tests", "data")
factory = ItemListFactory("rdf", os.path.join(TEST_DATA, "itemlists"))

@application.get('/static/<path:path>')
def static_files(path):
    return static_file(path, root='./static')

@application.get('/')
@view('home')
def home():
    temp_col = alveo.get_collections()
    collections = {}
    for collection in temp_col:
        collections[alveo.get_collection(collection)['collection_name']] = collection
    itemlists = factory.get_item_lists()
    return {'collections':collections, 'itemlists':itemlists}
    
@application.get('/version')
@view('version')
def version():
    output = {"API version":alveo.version()}
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    else:
        output = {"version":alveo.version()}
    return output


@application.get('/catalog')
@view('catalog')
def catalog():
    coll =  alveo.get_collections()
    output = {'num_collections': len(coll),
            'collections': coll}
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    return output

@application.get('/catalog/<collection_id>')
@view('collection')
def collection(collection_id):
    output = alveo.get_collection(request.url)
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    return output
    
@application.get('/item_lists')
@view('itemlists')
def itemlists():
    output = factory.get_item_lists()
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    return output
    
@application.get('/item_lists/<itemlist_id>')
@view('itemlist')
def itemlist(itemlist_id):
    output = factory.get_item_list(request.url)
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    return output

@application.delete('/item_lists/<itemlist_id>')
@view('del_itemlist')
def delete_itemlist(itemlist_id):
    output = factory.delete_item_list(request.url)
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    return output

@application.post('/item_lists/<itemlist_id>/create')
@view('create_itemlist')
def create_itemlist(itemlist_id):
    input_data = request.json
    url = request.url
    name = input_data["name"]
    output = factory.create_item_list(url.replace("/create", ""), name, "own")
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    return output

@application.post('/item_lists/<itemlist_id>/share')
@view('share_itemlist')
def share_itemlist(itemlist_id):
    url = request.url
    output = factory.share_item_list(url.replace("/share", ""))
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    return output

@application.post('/item_lists/<itemlist_id>/unshare')
@view('unshare_itemlist')
def unshare_itemlist(itemlist_id):
    url = request.url
    output = factory.unshare_item_list(url.replace("/unshare", ""))
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    return output

@application.post('/item_lists/<itemlist_id>/clear')
@view('clear_itemlist')
def clear_itemlist(itemlist_id):
    url = request.url
    output = factory.clear_item_list(url.replace("/clear", ""))
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    return output

@application.get('/catalog/<collection_id>/items/<item_id>')
@application.get('/catalog/<collection_id>/<item_id>')
@view('metadata')
def metadata(collection_id, item_id):
    url = request.url
    if not 'items' in url:
        url = url.replace(item_id, "items/%s" % item_id)
    output = alveo.get_item_metadata(url)
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    else:
        output = {"vars":output}
    return output

@application.get('/catalog/<collection_id>/<item_id>/primary_text')
@view('primary_text')
def primary_text(collection_id, item_id):
    url = request.url
    url = url.replace("%s/primary_text" % item_id, "items/%s" % item_id)
    output = alveo.get_primary_text(url)
    if output == None:
        abort(404, "Item has no primary text")
    else:
        if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
            response.content_type = 'text/plain'
        else:
            output = {'text':output}
    return output
    
@application.get('/documents/<collection_id>/<file_name>')
@application.get('/catalog/<collection_id>/<item_id>/document/<file_name>')
@view('document')
def document(collection_id, item_id=None, file_name=None):
    output = alveo.get_document(collection_id, file_name)
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'text/plain'
    else:
        output = {'text':output}
    return output

@application.get('/schema/json-ld')
@view('ann_context')
def annotation_context():
    output = alveo.get_annotation_context()
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    else:
        output = {"vars":output}
    return output

@application.get('/catalog/<collection_id>/<item_id>/annotations')
@view('annotations')
def annotations(collection_id, item_id):
    input_data = request.query
    url = request.url
    if "?" in url:
        url = url[:url.index("?")]
    url = url.replace("%s/annotations" % item_id, "items/%s" % item_id)
    output = alveo.get_annotations(url, input_data)
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    else:
        result = {"context":"https://app.alveo.edu.au/schema/json-ld",
                  "commonProperties":{},
                  "annotations":[]}
        for key in output["commonProperties"].keys():
            result['commonProperties'][key.replace("alveo:", "")] = output["commonProperties"][key]
        for annotation in output['alveo:annotations']:
            temp = {}
            for key in annotation.keys():
                value = annotation[key]
                if key == "@type":
                    key = "annType"
                temp[key.replace("@", "")] = value
            result["annotations"].append(temp)
        output = result
    return output

@application.route('/catalog/<collection_name>/<item_id>/annotations/types')
@view('annotation_types')
def annotation_types(collection_name, item_id):
    url = "http://localhost:3000/catalog/%s/items/%s" %(collection_name, item_id)
    output = alveo.get_annotation_types(url)
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    else:
        output = {'vars':output}
    return output

@application.post('/catalog/download_items')
@view('download')
def download_items():
    """download items documents and metadata from the real server into local server"""

    input_data = request.POST
    items = input_data["items"]
    if 'X-API-KEY' in request.headers:
        api_key = request.headers['X-API-KEY']
        output = alveo.download_files(items, api_key)
    else:
        abort(404, "No X-API-KEY was found in headers")
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    return output
        
@application.get('/catalog/search')
@view("search_metadata")
def search_metadata():
    query = request.query["metadata"]
    index = query.rfind(":")
    key, value = query[:index], query[index+1:]
    query = ((key, value),)
    items = alveo.search(query)
    n = len(items)
    output = {"num_results":n, "items":items}
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    return output

@application.post('/item_lists')
@view('add_item')
def add_to_itemlist():
    
    input_data = request.json
    if not "name" in input_data:
        output = {"error":"name parameter not found"}
    else:
        name = input_data["name"]
        if not "items" in input_data:
            output = {"error":"items parameter not found"}
        else:
            items = input_data["items"]
            itemlist_id = factory.get_item_list_id(name)
            if not isinstance(items, list):
                output = {"error":"items parameter not an array"}
            else:
                for item in items:
                    factory.add_to_item_list(itemlist_id, item)
                    output = {"success":"%s items added to existing item list %s" %(len(items), name)}
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    else:
        output = {'vars':output}
    return output

@application.put('/item_lists/<itemlist_id>')
@view('rename_itemlist')
def rename_itemlist(itemlist_id):
    input_data = request.json
    new_name = input_data["name"]
    factory.rename_item_list(request.url, new_name)
    output = {
                "name":factory.get_item_list(request.url)["name"],
                "num_items":len(factory.get_item_list(request.url)["items"]),
                "items":factory.get_item_list(request.url)["items"]
                } 
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    return output

@application.post('/catalog/<collection_id>/<item_id>/annotations')
@view('upload_ann')
def upload_annotation(collection_id, item_id):
    url = request.url
    collection_uri = url.replace("/%s/annotations" % item_id, "")
    uploadedfile = request.POST.get("file").file
    text = uploadedfile.read()
    data = json.loads(text)
    name = request.POST.get("file").raw_filename
    output = alveo.add_annotation(filename=name, collection_uri=collection_uri, data=data)
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    return output

@application.get('/sparql/<collection_id>')
@view('sparql_search')
def search_metadata_sparql(collection_id):
    collection_uri = "%scatalog/%s" %(alveo.base_url, collection_id)
    sparql_query = request.query["query"]
    output = alveo.search_sparql(collection_uri, sparql_query)
    if 'Accept' in request.headers and request.headers['Accept'] == "application/json":
        response.content_type = 'application/json'
        output = json.dumps(output)
    return output

if __name__=='__main__':
    
    
    #alveo = API()
    alveo.attach_directory(TEST_DATA)
    
    application.run(host='localhost', port=3000, reloader=True) # This starts the HTTP server