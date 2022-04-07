# Refine: Boolean Inference of Logical Networks
This repository contains the paper, documentation and implementation of Refine: Boolean Inference of Logical Networks, ILP vs. SAT.

Make sure Python3.9, Gurobi9.1 with an active license (https://www.gurobi.com/downloads/) and Cryptominisat5.8.0 (https://github.com/msoos/cryptominisat) are installed.

Input files are in MIDAS (experiments), SIF (network), and JSON (setup) format.

## Python implementation
The implementation uses Gurobi 9.1, Cryptominisat 5.8.0 and Python 3.9.

The code can be found in:
```
cd src
```
To get an overview of the commandline arguments:
```
python3.9 refine.py -h
```
By default, the code will run the truth table version, with the flag -i for the ILP:
```
python3.9 refine.py ../data/caspo/ExtLiver/dataset.csv ../data/caspo/ExtLiver/pkn.sif -s ../data/caspo/ExtLiver/setup.json -i
```
To run the code such that it finds all models, set flag '-a':
```
python3.8 refine.py <experiments> <network> <optional: -s setup> -i -a

```
To run the threshold model use flag '-t'
```
python3.8 refine.py <experiments> <network> <optional: -s experiments> -i -t

```
To run the 2-DNF model use flag '-d'
```
python3.8 refine.py <experiments> <network> <optional: -s experiments> -i -d

```
