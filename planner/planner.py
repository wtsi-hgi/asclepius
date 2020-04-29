import argparse
import sys
import re
import fnmatch

from yaml import safe_load

import core.irods_wrapper as irods_wrapper
import planner.inferrers as inferrers
from .object_class import Plan, AVU
from config import ENV_FILE

VALID_INFERS = ['sequence', 'variant']

def verify_infer(infer):
    """Check whether an infer method referenced in a configuration file
    exists."""
    if infer in VALID_INFERS:
        return True
    else:
        return False


def verify_config(yaml_file):
    """Parse configuration file 'file'. Returns True if the config appears
    valid, or a string describing the issue otherwise.

    @param file: Path to the configuration file.
    @return: True if config appears valid, problem string otherwise."""

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

                    if avu['infer'] not in VALID_INFERS:
                        return "Invalid dynamic AVU (nonexistant infer): {}".format(entry)

                    for mapping in avu['mapping'].keys():
                        split_map = mapping.split('.')
                        if split_map[0] == '*':
                            return "Invalid dynamic AVU (wildcard can't " +
                                "come first)"
                        if avu['infer'] in ['sequence', 'variant']:
                            # TODO: better way to check that an index
                            if split_map[1] == '*' and len(split_map) == 2:
                                return "Invalid dynamic AVU (variant and " +
                                    "sequence files can't have a wildcard " +
                                    "as the second index without a " +
                                    "non-wildcard third index.): {}"
                                    .format(entry)
                        if split_map.count('*') > 1:
                            return "Invalid dynamic AVU (can't have multiple " +
                                "wildcards in a single mapping): {}"
                                .format(entry)

    return True


def _stringify_dict(dictionary):
    """Convert a simple dictionary into a string. Nested dictionaries won't
    work."""

    if type(dictonary) != dict:
        # TODO: Throw an error instead?
        return dictionary

    _string = ''
    for _key, _value in dictionary.items():
        _string += "{}={},".format(_key, _value)
    dictionary = _string.strip(',')

    return dictionary


def _resolve_wildcard(header, target):
    """Return string of values from the header based on a column defined by
    the wildcard.

    @param header: Dictionary representation of file header
    @param target: List of header indices (ie ["SQ", "5", "LN"])
    @return: Value string"""

    wildcard_space = header # where in the header the wildcard applies to
    wildcard_index = 0 # index of the wildcard in the target
    try:
        for index, subtarget in enumerate(target):
            if subtarget == '*':
                wildcard_index = index
                break
            wildcard_space = wildcard_space[subtarget]
    except KeyError:
        print("Metadata target {} not found."
            .format('.'.join(target)), file=sys.stderr)

    try:
        wildcard_target = target[wildcard_index+1]
    except IndexError:
        wildcard_target = None

    # The only iterable type the value can be is a dictionary.
    if type(wildcard_space) != dict:
        if len(wildcard_target) != 0:
            # If the user is trying to find go another level deeper but the
            # target isn't a dictionary, raise a KeyError.
            raise KeyError
        # If the wildcard matches a non-dictionary value, just return that
        return wildcard_target

    target_string = ""
    _wildcard_space = wildcard_space

    if wildcard_target == None:
        # Wildcard is the final index, so it gets the whole row as a dictionary.
        target_string = _stringify_dict(wildcard_space)
    else:
        # Wildcard is in the middle, so it gets a column of header values
        for header_row in wildcard_space.values():
            target_string += "{},".format(header_row[wildcard_target])

        target_string = target_string.strip(',')

    return target_string


def infer_file(plan, mapping, file_type):
    """Adds AVUs to a plan object pointing at a file based on file metadata.

    @param plan: Plan object
    @param mapping: Dictionary corresponding to a list of 'mapping' entries
        in the YAML configuration file
    @param file_type: File type as defined by the 'infer' entry in the YAML
        configuration file
    @return: Modified Plan object"""

    if file_type == 'variant':
        header = inferrers.get_variant_header(plan.path)
    elif file_type == 'sequence':
        header = inferrers.get_sequence_header(plan.path)

    for key in mapping.keys():
        target = mapping[key].split('.')

        target_value = header
        try:
            if '*' in target:
                target_value = _resolve_wildcard(header, target)
            else:
                # Iteratively descend the header dictionary
                for subtarget in target:
                    target_value = target_value[subtarget]
        except KeyError:
            # TODO: Abort execution? Continue after omitting bad target?
            print("Metadata target {} not found in {}."
                .format(mapping[key], plan.path), file=sys.stderr)
            continue

        if type(target_value) == dict:
            try:
                target_value = _stringify_dict(target_value)
            except KeyError:
                continue

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
                            plan_object = infer_file(plan_object,
                                entry['mapping'], 'variant')

                        elif entry['infer'] == 'sequence':
                            plan_object = infer_file(plan_object,
                                entry['mapping'], 'sequence')

            yield plan_object
