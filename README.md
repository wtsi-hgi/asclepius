# Asclepius

Asclepius is used to add metadata AVUs to iRODS objects. It applies different metadata based on file name pattern matching, and can [IN PROGRESS] dynamically extract metadata from some files (like CRAM and VCF).

## Requirements

- `pyyaml`
- `python-irodsclient`

## Usage

`main.py [--config path] [--including_collections] [--overwrite] root_collection`

`root_collection` is an iRODS path. Every child data object of the collection will have metadata added to it as appropriate.
If `--overwrite` is used, AVUs with clashing attribute names will be overwritten instead of being skipped.
`--include_collections` will apply metadata to collection objects as well as data objects.
`--config path` is the path to a metadata configuration file.

The metadata Asclepius will add to objects is defined in a YAML configuration file using the following syntax.

```
"[pattern]":
- attribute: [string]
  value: [string]
  unit: [string]
- infer: ['variant','sequence']
  mapping:
    [string]: [string]
```

`[pattern]` can either be a bash-style glob string (ie, `*.txt`) or a regular expression. A pattern is treated as a regular expression when it is surrounded by forward slashes (ie, `/.*\.(b|cr)am$/`).
The `unit` field is optional.

The `infer` field is used to automatically extract metadata from variant and sequence file headers. The `mapping` list is used to map entries in the header to strings AVU attribute strings. The left string is the attribute name added to the iRODS object. The right string is used to refer to a field in the desired file's header.
For example, let's say you have a VCF file with the following lines in the header:

```
##fileformat=VCFv4.2
##FORMAT=<ID=AB, Number=1, Type=Integer, Description="Something or other">
##FORMAT=<ID=YZ, Number=2, Type=Integer, Description="Something else">
```

To add AVUS `(FORMAT=AB, ID=AB; Number=1; Type=Integer; Description="Something or other")` and `(fileformat, VCFv4.2)` to files ending in `0.vcf`, your configuration would be:

```
"*0.vcf":
- infer: variant
  mapping:
    "FORMAT=AB": FORMAT.AB
    "fileformat": fileformat
```

## Testing

To run the included tests just run `python3 -m unittest` in the root directory of the project.
