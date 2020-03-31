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
```

`[pattern]` can either be a bash-style glob string (ie, `*.txt`) or a regular expression. A pattern is treated as a regular expression when it is surrounded by forward slashes (ie, `/.*\.(b|cr)am$/`).
The `unit` field is optional.

## Testing

To run the included tests just run `python3 -m unittest` in the root directory of the project.
