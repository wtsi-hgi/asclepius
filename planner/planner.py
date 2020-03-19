import argparse
import ssl
import sys
import re

import irods.exception
from irods.session import iRODSSession
from yaml import safe_load

from config import ENV_FILE

def getObjectCollectionCatalogue(path):
    """Returns a dictionary of lists, {'objects': [], 'collections': []},
    which contains the iRODS path of every object and subcollection in
    the given path.

    @param path: Root iRODS path string
    @return: Dictionary with two lists, 'objects' and 'collections'"""

    ssl_settings = {'ssl_context':
        ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)}


    coll_buffer = []
    objects = []
    collections = []

    with iRODSSession(irods_env_file=ENV_FILE, **ssl_settings) as session:
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

    for collection in collection_paths:
        collection_paths.append(collection.path)

    return {'objects': object_paths, 'collections': collection_paths}

def verifyInfer(infer):
    """Check whether an infer method referenced in a configuration file
    exists."""
    # placeholder while there are no infer methods
    return True

def verifyMapping(mapping):
    """Check whether the mapping is valid for this file type."""
    # placeholder while there are no infer methods
    return True

def verifyConfig(yaml_file):
    """Parse configuration file 'file'. Returns True if the config appears
    valid, or a string describing the issue otherwise.

    @param file: Path to the configuration file.
    @return: True if config appears valid, string otherwise."""

    with open(yaml_file) as file:
        config = safe_load(file)

        if len(config) == 0:
            return "Invalid configuration (empty file)"

        for entry in config.keys():
            # If it's wrapped in forward slashes (ie, '/.cram/'), the entry
            # should be a valid regular expression.
            if entry[0] == "/" and entry[-1] == "/":
                regex = entry[1:-1]
                try:
                    re.compile(regex)
                except (re.error, RecursionError):
                    return "Invalid pattern (regex): {}".format(entry)

            for avu in config[entry]:
                keys = avu.keys()
                if 'infer' not in keys:
                    if 'attribute' not in keys:
                        return "Invalid AVU (no attribute): {}".format(entry)
                    if 'value' not in keys:
                        return "Invalid AVU (no value): {}".format(entry)
                    # unit field is optional, so don't check for it
                else:
                    if 'mapping' not in keys:
                        return "Invalid dynamic AVU (no mapping): {}".format(entry)

                    if not verifyInfer(avu['infer']):
                        return "Invalid dynamic AVU (nonexistant infer): {}".format(entry)

                    for mapping in avu['mapping'].keys():
                        if not verifyMapping(mapping):
                            return "Invalid dynamic AVU (nonexistant " \
                                "mapping): {}\t{}".format(entry, mapping)

    # TODO: throw errors at invalid keys instead of just ignoring them
    return True

def generateAVUs(catalogue):
    """Generator function that returns (iRODS path, AVU dictionary) tuples.

    @param catalogue: Lists of iRODS paths in a dictionary {'objects': <list>,
    'collections': <list>}"""
