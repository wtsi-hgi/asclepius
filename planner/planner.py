import argparse
import ssl
import sys
import re
import fnmatch

import irods.exception
from irods.session import iRODSSession
from yaml import safe_load

from .object_class import Plan, AVU
from config import ENV_FILE

def get_object_collection_catalogue(path):
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

def verify_infer(infer):
    """Check whether an infer method referenced in a configuration file
    exists."""
    # placeholder while there are no infer methods
    return True

def verify_mapping(mapping):
    """Check whether the mapping is valid for this file type."""
    # placeholder while there are no infer methods
    return True

def verify_config(yaml_file):
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

                    if not verify_infer(avu['infer']):
                        return "Invalid dynamic AVU (nonexistant infer): {}".format(entry)

                    for mapping in avu['mapping'].keys():
                        if not verify_mapping(mapping):
                            return "Invalid dynamic AVU (nonexistant " \
                                "mapping): {}\t{}".format(entry, mapping)

    # TODO: throw errors at invalid keys instead of just ignoring them
    return True

def generate_avus(catalogue, yaml_file, ignore_collections=True):
    """Generates AVU dictionaries for iRODS objects based on the definitions
    in a config file.

    @param catalogue: Lists of iRODS paths in a dictionary {'objects': <list>,
    'collections': <list>}
    @param yaml_file: Path to the configuration file
    @param ignore_collections: If True, only data objects will be returned
    @return: (iRODS path, AVU dictionary) tuples, as a generator"""

    valid = verify_config(yaml_file)
    if valid != True:
        print("Configuration file error:\n\t{}".format(valid), file=sys.stderr)
        exit(1)

    with open(yaml_file) as file:
        config = safe_load(file)

    if ignore_collections:
        _catalogue = catalogue['objects']
    else:
        _catalogue = catalogue['objects'] + catalogue['collections']

    for path in _catalogue:
        plan_object = Plan(path, [])
        avu_dict = {}
        # Prior to Python 3.7, dictionaries did not have an enforced
        # persistent order, so this might not work properly in older versions.
        for pattern in reversed(list(config.keys())):
            if pattern[0] == "/" and pattern[-1] == "/":
                if not re.search(pattern[1:-1], path):
                    # regex pattern didn't match
                    continue
            else:
                if not fnmatch.fnmatch(path, pattern):
                    # glob pattern didn't match
                    continue

            # TODO: Dynamic AVU code

            for entry in config[pattern]:
                attribute = entry['attribute']
                value = entry['value']
                unit = None
                if 'unit' in entry.keys():
                    unit = entry['unit']

                avu_dict[attribute] = (value, unit)

        plan_object = Plan(path, [])
        for attribute in avu_dict.keys():
            value, unit = avu_dict[attribute]
            plan_object.metadata.append(AVU(attribute, value, unit))

        yield plan_object
