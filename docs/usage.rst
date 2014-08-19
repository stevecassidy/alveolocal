========
Usage
========

To use Alveo Local in a project::

    import alveolocal
    
    # create an API instance and attach a directory containing RDF files
    # and data
    api = alveolocal.API()
    api.attach_directory("/path/to/data")
    
    # exercise the API
    version = api.version()
    collections = api.get_collections()
    info = api.get_collection(collections[0])
    
    