from bottle import Bottle, request, abort, response
from alveolocal import API
import json
import os
from itemlist import ItemListFactory


application = Bottle()
alveo = API()
TEST_DATA = os.path.join(os.path.dirname(__file__), "..", "tests", "data")
factory = ItemListFactory("rdf", os.path.join(TEST_DATA, "itemlists"))


@application.get('/version')
def version():
    output = {"API version":alveo.version()}
    return json.dumps(output)


@application.get('/catalog/')
def catalog():
    coll =  alveo.get_collections()
    output = {'num_collections': len(coll),
            'collections': coll}
    response.content_type = 'application/json'
    return json.dumps(output)


@application.get('/catalog/<collection_id>')
def collection(collection_id):
    output = alveo.get_collection(request.url)
    response.content_type = 'application/json'
    return json.dumps(output)
    
@application.get('/item_lists')
def itemlists():
    output = factory.get_item_lists()
    response.content_type = 'application/json'
    return json.dumps(output)
    
@application.get('/item_lists/<itemlist_id>')
def itemlist(itemlist_id):
    output = factory.get_item_list(request.url)
    response.content_type = 'application/json'
    return json.dumps(output)

@application.delete('/item_lists/<itemlist_id>')
def delete_itemlist(itemlist_id):
    output = factory.delete_item_list(request.url)
    response.content_type = 'application/json'
    return json.dumps(output)

@application.post('/item_lists/<itemlist_id>/create')
def create_itemlist(itemlist_id):
    input_data = request.json
    url = request.url
    name = input_data["name"]
    output = factory.create_item_list(url.replace("/create", ""), name, "own")
    response.content_type = 'application/json'
    return json.dumps(output)

@application.post('/item_lists/<itemlist_id>/share')
def share_itemlist(itemlist_id):
    url = request.url
    output = factory.share_item_list(url.replace("/share", ""))
    response.content_type = 'application/json'
    return json.dumps(output)

@application.post('/item_lists/<itemlist_id>/unshare')
def unshare_itemlist(itemlist_id):
    url = request.url
    output = factory.unshare_item_list(url.replace("/unshare", ""))
    response.content_type = 'application/json'
    return json.dumps(output)

@application.post('/item_lists/<itemlist_id>/clear')
def clear_itemlist(itemlist_id):
    url = request.url
    output = factory.clear_item_list(url.replace("/clear", ""))
    response.content_type = 'application/json'
    return json.dumps(output)

@application.get('/catalog/<collection_id>/<item_id>')
def metadata(collection_id, item_id):
    url = request.url
    url = url.replace(item_id, "items/%s" % item_id)
    output = alveo.get_item_metadata(url)
    response.content_type = 'application/json'
    return json.dumps(output)

@application.get('/catalog/<collection_id>/<item_id>/primary_text')
def primary_text(collection_id, item_id):
    url = request.url
    url = url.replace("%s/primary_text" % item_id, "items/%s" % item_id)
    output = alveo.get_primary_text(url)
    if output == None:
        abort(404, "Item has no primary text")
    else:
        response.content_type = 'text/plain'
        return output

@application.get('/catalog/<collection_id>/<item_id>/document/<file_name>')
def document(collection_id, item_id, file_name):
    output = alveo.get_document(collection_id, file_name)
    response.content_type = 'text/plain'
    return output

@application.get('/schema/json-ld')
def annotation_context():
    output = alveo.get_annotation_context()
    response.content_type = 'application/json'
    return json.dumps(output)

@application.get('/catalog/<collection_id>/<item_id>/annotations')
def annotations(collection_id, item_id):
    input_data = request.json
    url = request.url
    url = url.replace("%s/annotations" % item_id, "items/%s" % item_id)
    output = alveo.get_annotations(url)
    response.content_type = 'application/json'
    return json.dumps(output)

@application.route('/catalog/<collection_name>/<item_id>/annotations/types')
def annotation_types(collection_name, item_id):
    url = "http://localhost:3000/catalog/%s/items/%s" %(collection_name, item_id)
    return alveo.get_annotation_types(url)

@application.route('/catalog/download_items')
def download_items():
    """download items documents and metadata from the real server into local server"""
    
    input_data = request.POST
    items = input_data["items"]
    
@application.route('/catalog/search?metadata=<query>')
def search_metadata(query):
    
    pass

@application.post('/item_lists')
def add_to_itemlist():
    
    response.content_type = 'application/json'
    input_data = request.json
    if not "name" in input_data:
        return {"error":"name parameter not found"}
    name = input_data["name"]
    if not "items" in input_data:
        return {"error":"items parameter not found"}
    items = input_data["items"]
    itemlist_id = factory.get_item_list_id(name)
    if not isinstance(items, list):
        return {"error":"items parameter not an array"}
    for item in items:
        factory.add_to_item_list(itemlist_id, item)
    return json.dumps({"success":"%s items added to existing item list %s" %(len(items), name)})

@application.put('/item_lists/<itemlist_id>')
def rename_itemlist(itemlist_id):
    
    response.content_type = 'application/json'
    input_data = request.json
    new_name = input_data["name"]
    factory.rename_item_list(request.url, new_name)
    output = {
                "name":factory.get_item_list(request.url)["name"],
                "num_items":len(factory.get_item_list(request.url)["items"]),
                "items":factory.get_item_list(request.url)["items"]
                } 
    return json.dumps(output)

@application.post('/catalog/<collection_id>/<item_id>/annotations')
def upload_annotation(collection_id, item_id):
    url = request.url
    collection_uri = url.replace("/%s/annotations" % item_id, "")
    uploadedfile = request.POST.get("file").file
    text = uploadedfile.read()
    data = json.loads(text)
    name = request.POST.get("file").raw_filename
    response.content_type = 'application/json'
    return json.dumps(alveo.add_annotation(filename=name, collection_uri=collection_uri, data=data))

@application.route('/sparql/<collection_id>?query=<sparql_query>')
def search_metadata_sparql(collection_id, sparql_query):
    collection_uri = "%scatalog/%s" %(alveo.base_url, collection_id)
    output = alveo.search_sparql(collection_uri, sparql_query)
    response.content_type = 'application/json'
    return output

if __name__=='__main__':
    
    
    
    #alveo = API()
    alveo.attach_directory(TEST_DATA)
    
    application.run(host='localhost', port=3000, reloader=True) # This starts the HTTP server