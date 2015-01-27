from bottle import Bottle, request, abort, response
from alveolocal import API
import json
import os
from itemlist import ItemListFactory

application = Bottle()
alveo = API()
TEST_DATA = os.path.join(os.path.dirname(__file__), "..", "tests", "data")
factory = ItemListFactory("rdf", os.path.join(TEST_DATA, "itemlists"))


@application.route('/version')
def version():
    return json.dumps({"API version":alveo.version()})


@application.route('/catalog/')
def catalog():
    coll =  alveo.get_collections()
    output = {'num_collections': len(coll),
            'collections': coll}
    response.content_type = 'application/json'
    return json.dumps(output)


@application.route('/catalog/<collection_name>')
def collection(collection_name):
    
    response.content_type = 'application/json'
    return json.dumps(alveo.get_collection(request.url))
    
@application.route('/item_lists')
def itemlists():
    
    response.content_type = 'application/json'
    return json.dumps(factory.get_item_lists())
    
@application.route('/item_lists/<itemlist_id>')
def itemlist(itemlist_id):
    
    response.content_type = 'application/json'
    return json.dumps(factory.get_item_list(request.url))

@application.route('/catalog/<collection_name>/<item_id>')
def metadata(collection_name, item_id):
    url = "http://localhost:3000/catalog/%s/items/%s" %(collection_name, item_id)
    response.content_type = 'application/json'
    return json.dumps(alveo.get_item_metadata(url))

@application.route('/catalog/<collection_name>/<item_id>/primary_text')
def primary_text(collection_name, item_id):
    
    url = "http://localhost:3000/catalog/%s/items/%s" %(collection_name, item_id)
    result = alveo.get_primary_text(url)
    if result == None:
        abort(404, "Item has no primary text")
    else:
        response.content_type = 'text/plain'
        return result

@application.route('/catalog/<collection_name>/<item_id>/document/<file_name>')
def document(collection_name, item_id, file_name):
    text = alveo.get_document(collection_name, file_name)
    response.content_type = 'text/plain'
    return text

@application.route('/schema/json-ld')
def annotation_context():
    output = alveo.get_annotation_context()
    response.content_type = 'application/json'
    return json.dumps(output)

@application.route('/catalog/<collection_name>/<item_id>/annotations')
def annotations(collection_name, item_id):
    url = "http://localhost:3000/catalog/%s/items/%s" %(collection_name, item_id)
    result = alveo.get_annotations(url)
    response.content_type = 'application/json'
    return json.dumps(result)

@application.route('/catalog/<collection_name>/<item_id>/annotations/types')
def annotation_types(collection_name, item_id):
    url = "http://localhost:3000/catalog/%s/items/%s" %(collection_name, item_id)
    return alveo.get_annotation_types(url)

@application.route('/catalog/download_items')
def download_items():
    """download items documents and metadata from the real server into local server"""
    
    input_data = request.json()
    items = input_data["items"]
    
@application.route('/catalog/search?metadata=<query>')
def search_metadata(query):
    
    pass

@application.post('item_lists')
def add_to_itemlist(query):
    
    pass

@application.put('item_lists/<itemlist_id>')
def rename_itemlist(itemlist_id):
    
    pass

@application.post('/catalog/<collection_name>/<item_id>/annotations')
def upload_annotation(collection_name, item_id):
    
    pass

@application.route('/sparql/<collection_name>?query=<sparql_query>')
def search_metadata_sparql(collection_name, sparql_query):
    
    pass

if __name__=='__main__':
    
    
    
    #alveo = API()
    alveo.attach_directory(TEST_DATA)
    
    application.run(host='localhost', port=3000, reloader=True) # This starts the HTTP server