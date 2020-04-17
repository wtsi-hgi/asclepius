import argparse
import sys
import re
import fnmatch

from yaml import safe_load

import core.irods_wrapper as irods_wrapper
import planner.inferrers as inferrers
from .object_class import Plan, AVU
from config import ENV_FILE

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

def _infer_file(plan, mapping, file_type):
    """Adds AVUs to a plan object pointing at a file."""

    if file_type == 'variant':
        header = inferrers.get_variant_header(plan.path)
    elif file_type == 'sequence':
        header = inferrers.get_sequence_header(plan.path)

    for key in mapping.keys():
        target = mapping[key].split('.')

        target_value = header
        try:
            # Iteratively descend the header dictionary
            for subtarget in target:
                target_value = target_value[subtarget]
        except KeyError:
            # TODO: Abort execution? Continue after omitting bad target?
            print("Metadata target {} not found in {}."
                .format(mapping[key], plan.path))
            continue

        if type(target_value) == dict:
            # Convert dictinary to a cleaner string
            _string = ''
            for _key, _value in target_value.items():
                _string += "{}={},".format(_key, _value)
            target_value = _string.strip(',')

        plan.metadata.append(AVU(key, target_value))

    return plan

def generate_plans(catalogue, yaml_file, progress_file, resume,
        include_collections=False):
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

    if not include_collections:
        _catalogue = {'objects': catalogue['objects']}
    else:
        _catalogue = catalogue

    if resume:
        with open(progress_file, 'rt') as f:
            # _catalogue['objects'] = list(set(_catalogue['objects']) - set(line.strip() for line in f)) This doesnt work for some reason
            progress_file_set = set(line.strip() for line in f)
            _catalogue['objects'] = list(set(_catalogue['objects']) - progress_file_set)
            if include_collections:
                _catalogue['collections'] = list(set(_catalogue['collections']) - progress_file_set)


    for object_type in _catalogue.keys():
        for path in _catalogue[object_type]:
            if object_type == 'objects':
                plan_object = Plan(path, False, [])
            elif object_type == 'collections':
                plan_object = Plan(path, True, [])

            avu_dict = {}
            # Prior to Python 3.7, dictionaries did not have an enforced
            # persistent order, so this might not work properly in older
            # versions.
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
                    if 'attribute' in entry.keys():
                        # Fixed AVUs
                        attribute = entry['attribute']
                        value = entry['value']
                        unit = None
                        if 'unit' in entry.keys():
                            unit = entry['unit']

                        plan_object.metadata.append(AVU(attribute, value, unit))

                    elif 'infer' in entry.keys():
                        # Dynamic AVUs
                        if entry['infer'] == 'variant':
                            plan_object = _infer_file(plan_object,
                                entry['mapping'], 'variant')

                        elif entry['infer'] == 'sequence':
                            plan_object = _infer_file(plan_object,
                                entry['mapping'], 'sequence')

            yield plan_object
