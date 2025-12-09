# Introduction

## What is this package for?
At [CHESS](https://www.chess.cornell.edu), most data is collected with [SPEC](https://certif.com/content/spec/). Often, different beamlines and experimental setups use different SPEC macros to control the format / structure of the collected metadata and data. These formats are also subject to change over time as beamlines are upgraded. Also, some experiment types may need to collect pieces of metadata not collected by others. This variability can make it challenging for users to know how to consistently read in their experimental data for further processing and analysis.

The `chess-scanparsers` package attempts to solve this problem by providing a uniform object oriented python interface to access data and metadata for a single SPEC scan from [supported beamlines and experiment types](#supported_beamlines_and_experiment_types). The interface is made available when an instance of a `ScanParser` object is initialized -- the `ScanParser` object's [properties](https://www.w3schools.com/python/python_class_properties.asp) will provide access to information like the start time of the scan, the command string used to run the scan, etc. In order to initialize the correct `ScanParser` object to properly parse their scan, users will need to know:
1. The name of the beamline at which the scan was run
1. The type of experiment being performned with this scan
1. The full path to the [SPEC data file](https://certif.com/spec_manual/user_1_4_1.html) in which data from that scan was logged
1. The number of the scan of interest in the given SPEC file

## Supported Beamlines and Experiment Types
The table below indicates which combinations of beamlines and experimental techniques are supported by `chess-scanparsers`.
|                        | "id1a3" | "id3a" | "id3b" | "id4b" |
|------------------------|---------|--------|--------|--------|
| "edd"                  | YES     | YES    | no     | no     |
| "giwaxs"               | no      | no     | YES    | no     |
| "hdrm"                 | no      | no     | no     | YES    |
| "powder" or "saxswaxs" | YES     | YES    | YES    | no     |
| "tomo"                 | YES     | YES    | YES    | no     |
| "xrf"                  | no      | no     | YES    | no     |


## Examples

### Choosing the correct type of `ScanParser` for your beamline and experiment type
```python
>>> from chess_scanparsers import choose_scanparser
>>> SP = choose_scanparser("id3b", "saxswaxs")
>>> print(SP)
<class 'chess_scanparsers.scanparsers.FMBSAXSWAXSScanParser'>
```

### Initializing a usable `ScanParser` object
```python
>>> # Continued from previous example
>>> sp = SP("spec_file", 1)
>>> print(sp)
FMBSAXSWAXSScanParser(spec_file, 1) -- flymesh samz 68.538 70.288 350 0.5 samx 8.8 9.05 50
```

### Using a `ScanParser` object to get SPEC-related metadata about a scan
```python
>>> # Continued from previous example

>>> print(sp.spec_command)
flymesh samz 68.538 70.288 350 0.5 samx 8.8 9.05 50

>>> print(sp.spec_scan_dwell)
0.5

>>> print(sp.spec_scan_shape)
(351, 51)
```

### Acessing detector data
```python
# Continued from previous examples
>>> print(sp.get_detector_data("PIL5", 0))
[[-2  0  0 ...  0  0 -2]
 [ 0  0  0 ...  0  0  0]
 [ 0  0  0 ... -2  0  0]
 ...
 [ 0  0  0 ...  0  0  0]
 [ 1  1  0 ...  0  0  1]
 [-2  1  1 ...  0  0 -2]]
```