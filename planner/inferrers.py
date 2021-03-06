import subprocess
import sys
import os
import re
from tokenize import generate_tokens
from io import StringIO

from pysam import libcalignmentfile

def _split_by_symbol(string, symbol):
    """Splits a string of elements divided by a symbol into a list. Unlike
    the csv module, this ignores symbols in quoted strings even if the
    quotation mark isn't immediately before or after a symbol.

    The symbol range is limited by the Python tokeniser."""

    # The function doesn't have to do any quote detection itself, the
    # Python tokeniser just handles quoted strings better than the csv library.

    symbols = [-1] # list of comma positions
    # For each token (t) indicating a symbol, get its position (t[2][1])
    # and add it to the symbols list
    symbols.extend(t[2][1] for t in generate_tokens(
        StringIO(string).readline) if t[1] == symbol)
    symbols.append(len(string))
    # Creates a list of slices of the string based on symbol locations
    return [ string[symbols[i]+1:symbols[i+1]] for i in range(len(symbols)-1)]


def parse_variant_header(header):
    """Convert a VCF header string into a Python data structure. The header's
    validity is NOT checked.

    @param header: VCF header string"""
    header = header.split('\n')

    header_dict = {}

    for line in header:
        if line[:2] != '##':
            continue

        _line = line[2:] # remove leading ##

        # If the line is ##x=y, header_dict[x] = y. However, most of the time
        # line is ##x=<ID=y, AB=a, etc> where x appears multiple times. In
        # this case, header_dict[x][y] = {'AB': a, etc}
        namespace, values = _line.split('=', 1)

        if values[0] == '<' and values[-1] == '>':
            _values = _split_by_symbol(values[1:-1], ',')

            line_dict = {}
            for pair in _values:
                subkey, subvalue = pair.split('=', 1)
                line_dict[subkey] = subvalue

            # Should the ID be left in the line_dict redundantly? Not sure.
            if namespace not in header_dict.keys():
                header_dict[namespace] = {}
            header_dict[namespace][line_dict['ID']] = line_dict

        else:
            # In case there are multiple key-value pairs with the same key,
            # just turn them into a list
            if namespace in header_dict.keys():
                if type(header_dict[namespace]) == list:
                    header_dict[namespace].append(values)
                else:
                    header_dict[namespace] = [header_dict[namespace], values]
            else:
                header_dict[namespace] = values

    return header_dict


def get_sequence_header(irods_path):
    """Extract the header from a SAM type file in iRODS and convert it into
    a Python dictionary. Returns None if header extraction fails."""

    try:
        header = subprocess.check_output(['samtools', 'view', '-H',
            'irods:' + irods_path]).decode("UTF-8")
    except subprocess.CalledProcessError:
        print("Failed to extract {} header. It's possible the file no longer " +
            "exists, or is not a valid sequence file.".format(irods_path),
            file=sys.stderr)

        return None

    header_dict = libcalignmentfile.AlignmentHeader.from_text(header).as_dict()

    # Used to suggest whether a @CO line should be treated as a dictionary or
    # plain text string
    keyvalue_regex = re.compile('(\s*[a-zA-Z0-9_]+:\s*[^\s]*\s*)*')
    for key in header_dict.keys():
        if key == 'CO':
            # pysam's 'from_text' just keeps CO tags as as one big string,
            # this makes them more uniform
            co_dict = {}
            for index, line in enumerate(header_dict[key]):
                if not keyvalue_regex.fullmatch(line):
                    co_dict[str(index)] = line
                else:
                    # Split individual lines into dictionaries
                    _line = line.split()
                    _line_dict = {}
                    for item in _line:
                        # NOTE: Assumes every @CO row has the same formatting as
                        # other tags. Potentially untrue?
                        _split = item.split(':', 1)
                        if len(_split) == 2:
                            _item_key, _item_value = _split
                        elif len(_split) == 1:
                            # Deals with incomplete/empty key value pairs
                            _item_key = _split[0]
                            _item_value = ''
                        else:
                            continue
                        _line_dict[_item_key] = _item_value

                    co_dict[str(index)] = _line_dict

            header_dict[key] = co_dict

        elif type(header_dict[key]) == list:

            # Convert list representations of header elements into dictionaries
            # with the identifier tag as the key
            if 'ID' in header_dict[key][0].keys():
                identifier = 'ID'
            elif 'SN' in header_dict[key][0].keys():
                identifier = 'SN'
            else:
                print("Couldn't find ID or SN in sequence file header row, " +
                    "using first key in the row instead. File: {}"
                    .format(irods_path), file=sys.stderr)
                identifier = header_dict[key][0].keys()[0]

            new_dict = {}
            for item in header_dict[key]:
                new_dict[item[identifier]] = item

            header_dict[key] = new_dict

    return header_dict

def get_variant_header(irods_path):
    """Extract the header from a VCF type file in iRODS and convert it into
    a Python dictionary. Stores the file's sample names under 'sample_names'.
    Returns None if header extraction fails."""

    try:
        header = subprocess.check_output(['bcftools', 'view', '-h',
            'irods:' + irods_path]).decode("UTF-8")
        samples = subprocess.check_output(['bcftools', 'query', '-l',
            'irods:' + irods_path]).decode("UTF-8")
    except subprocess.CalledProcessError:
        print("Failed to extract {} header. It's possible the file no longer " +
        "exists, or is not a valid variant file.".format(irods_path),
        file=sys.stderr)

        return None
    except FileNotFoundError:
        print("bcftools not found. Please use the 'hgi_base' anaconda " +
            "environment or add the bcftools binary to the PATH.")

        return None

    # remove index file bcftools automatically creates in the working directory
    filename = irods_path.split('/')[-1]
    try:
        os.remove(filename + '.tbi')
    except FileNotFoundError:
        pass

    header_dict = parse_variant_header(header)
    header_dict['sample_names'] = samples
    return header_dict
