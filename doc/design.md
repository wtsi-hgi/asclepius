# Design Document

## Glossary

* **iRODS** Object store filesystem, federated across mutually exclusive
  "zones"

* **Collection** iRODS equivalent of a POSIX directory

* **Data-Object** iRODS equivalent of a POSIX file

* **AVU** Metadata tuple that can be applied to objects, such as
  collections and data-objects, in iRODS
  (**a**ttribute-**v**alue-**u**nit; the unit is often omitted.)

## User Stories

1. I would like to apply AVUs to data-objects that already exist in
   iRODS under a specific collection. AVUs should be any combination of
   the following:

   1. I would like general AVUs, which apply to everything.

   2. I would like specific AVUs, which match data-objects by filename
      pattern(s). These specific AVUs should come in two flavours:

      1. Explicit AVUs, that are applied to matching data-objects.

      2. AVUs that are extracted from the contents of matching
         data-objects.

2. I would like to specify the pattern-to-AVU mapping in a
   human-readable configuration file.

3. I would like BAM, CRAM and VCF files to have AVUs extracted from
   their contents (using the mechanism from 1.ii.b.) The specific
   metadata to be extracted from these types of files and mapped to AVUs
   will be confirmed at a later date (potentially iteratively, during
   implementation).

4. I would like this process to run, unattended, as a farm job.

5. I would like concurrent usage of iRODS, if any, to be throttleable.

6. I would like the application of AVUs to be idempotent (i.e., never
   applying the same AVU more than once).

## Notes

* 1.i. is generalised by 1.ii.a., using an appropriate pattern.

* Patterns could be globs or regexes; whichever's easier.

* AVU application is fast, but it has to be done on each data-object
  separately. This has scope for parallelisation, hence 5.

* If any parallelisation is implemented, then atomicity (as well as
  idempotency per 6.) must be enforced programmatically. This would be
  most easily achieved by partitioning applications such that they are
  mutually exclusive with respect to thread.

I would implement this using a plan-and-apply strategy, where the plan
stage first gets the listing of all data-objects under the specified
collection and then resolves the AVU mapping defined by the
configuration file. The apply stage would then simply loop through each
item in the plan, to set (if necessary) the relevant AVU for each
data-object. There's no reason why the planning and application phases
can't run concurrently (i.e., where the application phase waits for
tasks from the planner). This is how Shepherd works, for example;
however, this may be simple enough that you don't need to separate the
stages quite so explicitly.

The [icommands (iRODS' client
software)](https://docs.irods.org/master/icommands/user) give an
interface to iRODS, however they're a bit cludgy. Their use can be
augmented with [baton](http://wtsi-npg.github.io/baton). Python wrappers
for these can be found (or derived) from the Shepherd source.

To extract metadata from BAM/CRAM files, you'll need to use
[Samtools](http://www.htslib.org/doc/samtools.html) with iRODS support
(this is installed on the farm). There is a Python library too, "Pysam",
but it's not clear whether it supports reading files from iRODS. Domain
knowledge from colleagues can be used for other types of files (e.g.,
VCF). The point would be to make it general enough such that arbitrary
metadata extraction can be implemented.

The idempotency guarantee in 6. means you should not need to persist
state to disk. Either way, if you implement any parallelism, be careful
about atomic access to your state.

## Implementation

The system will be in three parts (in a single binary/script):

1. An overall wrapper
2. A planner
3. An execution manager

The overall wrapper is not interesting; its purpose is to plumb the
planner and execution manager together and, say, interpret command line
arguments, etc.

The planner will do the following:

* Take as input the root collection and a human-readable configuration
  file which defines filename pattern to AVU mappings. (These AVU sets
  are either explicit, or a function of the filetype.)

* Iterate through every data-object in the root collection, resolving
  the aforementioned mappings to generate the complete AVU set for each
  data-object. This will be done lazily (i.e., a stream or generator),
  for the execution manager to consume. When a filetype mapping is
  encountered, the planner will have to read the data-object off iRODS
  to extract and map the necessary metadata.

The execution manager will do the following:

* It will consume the stream of data-object/AVU tuples.

* It will pass this to an execution worker (the pool thereof is either
  managed by this, or by the overall wrapper...probably the execution
  manager would be best).

* Each execution worker will check the current AVUs on said data-object,
  then commit the difference (i.e., the new ones) per its input. This
  will ensure idempotency.

The planner and execution manager are decoupled. This facilitates
codified testing, which is always good and, for independent work, it
helps document the interfaces that are expected between parts. One
caveat would be that any interfacing with iRODS would be in the realm of
integration testing, which may be harder to codify.

Ultimately, the end-user interface will be something like:

     asclepius --collection ROOT_COLLECTION --config /path/to/config

...probably submitted as an LSF job. (Names and options subject to
change.)

### Data-Object to AVU Mapping Configuration

The data-object to AVU mapping will be defined in a YAML-based file with
the following schema:

```yaml
<pattern>:
- attribute: <string>
  value: <string>
  unit: <string>      # Optional
- infer: <handler>
  mapping:
    <handler_key1>: <irods_attribute1>
    <handler_key2>: <irods_attribute2>
    # etc.
# etc.
```

That is, the file will consist of a sequence of `pattern`s, which
represent the data-object name pattern to match. The patterns are to be
considered in ascending priority, such that later matches appearing in
the file will override any that have preceded it.

Patterns will be expressed either as a glob (e.g., `*.cram`), or as a
regular expression. Regular expressions must be enclosed within slashes
(e.g., `/\.([sb]|cr)am$/`).

The contents of these mapping objects will be a list, containing a
mixture of explicit and inferred metadata.

#### Explicit Metadata

This is an explicit AVU, defined in the configuration:

```yaml
attribute: <string>
value: <string>
unit: <string>      # Optional
```

#### Inferred Metadata

This is metadata that is read from the contents of a data-object and
then mapped to the given iRODS attribute:

```yaml
infer: <handler>
mapping:
  <handler_key1>: <irods_attribute1>
  <handler_key2>: <irods_attribute2>
  # etc.
```

That is, the named `handler` will return a sequence of key/value pairs
that have been extracted from the data-object. The named keys in the
`mapping` section will be mapped to the defined iRODS attribute.

#### Example

```yaml
# n.b., Some patterns will need to be quoted to be valid YAML
"*":
- attribute: asclepius
  value: seen
- attribute: group
  value: humgen

/\.([sb]|cr)am$/:
- attribute: pi
  value: ch12
- attribute: group
  value: hgi
- infer: SequenceData
  mapping:
    reference: reference
    sample: sample_id
    library: library_id
- attribute: cost
  value: 100000
  unit: gbp
```

Here, SAM/BAM/CRAM files will have their group AVU overridden (from the
catch-all rule that appears earlier) and have sequence data-specific
metadata extracted from them and mapped to a canonical iRODS attribute.
