import ssl

import irods.exception
from irods.session import iRODSSession

from config import ENV_FILE

def create_session():
    """Returns an iRODSSession object."""

    ssl_settings = {'ssl_context':
        ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)}

    return iRODSSession(irods_env_file=ENV_FILE, **ssl_settings)

def get_metadata(session, filepath):

    obj = session.data_objects.get(filepath)
    return obj.metadata


def get_irods_catalogue(path):
    """Returns a dictionary of lists, {'objects': [], 'collections': []},
    which contains the iRODS path of every object and subcollection in
    the given path.

    @param path: Root iRODS path string
    @return: Dictionary with two lists, 'objects' and 'collections'"""

    coll_buffer = []
    objects = []
    collections = []

    # session.collections.get fails if there's a trailing slash in the path
    path = path.rstrip("/")

    with create_session() as session:
        try:
            coll = session.collections.get(path)
        except irods.exception.CollectionDoesNotExist:
            print("Error! Collection {} not found!".format(path),
                file=sys.stderr)
            return False

        collections.append(coll)
        collections.extend(coll.subcollections)
        objects.extend(coll.data_objects)
        coll_buffer.extend(coll.subcollections)

        while len(coll_buffer) != 0:
            coll = coll_buffer.pop()
            collections.extend(coll.subcollections)
            objects.extend(coll.data_objects)
            coll_buffer.extend(coll.subcollections)

    # uncomment to return full iRODS objects instead of just paths
    #return {'objects': objects, 'collections': collections}

    object_paths = []
    collection_paths = []

    for object in objects:
        object_paths.append(object.path)

    for collection in collections:
        collection_paths.append(collection.path)

    return {'objects': object_paths, 'collections': collection_paths}
