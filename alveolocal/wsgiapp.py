from bottle import Bottle, request, route, run, abort
from alveolocal import API

application = Bottle()

@application.route('/version')
def version():
    return  {"API version": alveo.version()}


@application.route('/catalog/')
def catalog():
    coll =  alveo.get_collections()
    return {'num_collections': len(coll),
            'collections': coll}


@application.route('/catalog/:name')
def collection(name):
     
    return alveo.get_collection(request.url)
    
@application.route('/item_lists')
def itemlists():

    return alveo.get_item_lists()
    
    
@application.route('/catalog/<corpus>/items/<id>')
def item(corpus, id):
    
    return alveo.get_item_metadata(request.url)

@application.route('/catalog/<corpus>/items/<id>/primary_text.json')
def item(corpus, id):
    
    url = request.url
    url = url.replace('/primary_text.json', '')
    result = alveo.get_primary_text(url)
    if result == None:
        abort(404, "Item has no primary text")
    else:
        return result


if __name__=='__main__':
    
    TEST_DATA = "tests/data"
    
    alveo = API()
    alveo.attach_directory(TEST_DATA)
    
    application.run(host='localhost', port=3000, reloader=True) # This starts the HTTP server