# Refine: Boolean Inference of Logical Networks
This repository contains the paper, documentation and implementation of Refine: Boolean Inference of Logical Networks, ILP vs. SAT.

Make sure both Gurobi9.1 with an active license (https://www.gurobi.com/downloads/) and Cryptominisat5.8.0 (https://github.com/msoos/cryptominisat) are installed.

## Python implementation
The implementation uses Gurobi 9.1, Cryptominisat 5.8.0 and Python 3.8.

The code can be found in:
```
cd src
```
To get an overview of the commandline arguments:
```
python3.8 refine.py -h
```
By default, the code will run the SAT version, with a default lower bound of 1 and the default values as given in the metabolites file:
```
python3.8 refine.py ../../data/egfr/metabolites ../../data/egfr/reactions
```
To run SAT with the EGFR dataset and all experiments, starting at lower bound 3:
```
python3.8 refine.py ../../data/egfr/metabolites ../../data/egfr/reactions -e ../../data/egfr/experiments -l 3
```
To run the ILP with the EGFR dataset and all experiments:
```
python3.8 refine.py ../../data/egfr/metabolites ../../data/egfr/reactions -e ../../data/egfr/experiments -i
```
To run the code such that it finds all models, set flag '-a':
```
python3.8 refine.py <metabolites_file> <reactions_file> <optional: -e experiments_file> -a

```
To run the threshold model use flag '-t'
```
python3.8 refine.py <metabolites_file> <reactions_file> <optional: -e experiments_file> <-i> -t

```
