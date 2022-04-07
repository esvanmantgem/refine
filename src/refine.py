'''Refine: Boolean inference of logical networks'''
import argparse
import sys
from boolean_model import *
from genetic_network import *
from ilp_refine import *
from sat_refine import *
from midassif_input import *
from model_preprocessing import *


def set_functions(gn, bm):
    functions = {}
    inhibitors = {}
    stimuli = {}

    for reaction in gn.reactions:
        # add reation to functions
        if reaction.downstream not in functions:
            functions[reaction.downstream] = [reaction.upstream]
        else:
            functions[reaction.downstream].append(reaction.upstream)
        # handle inhibiting interactions
        if reaction.inhibiting:
            if reaction.downstream not in inhibitors:
                inhibitors[reaction.downstream] = [reaction.upstream]
            else:
                inhibitors[reaction.downstream].append(reaction.upstream)
        else:
            if reaction.downstream not in stimuli:
                stimuli[reaction.downstream] = [reaction.upstream]
            else:
                stimuli[reaction.downstream].append(reaction.upstream)

    for function in functions:
        if function not in inhibitors:
            inhibitors[function] = []
        bm.add_function(Function(function, functions[function], inhibitors[function]))
    #for function in functions:
    #    bm.add_function(Function(function, []))
    #for function in inhibitors:
    #    bm.set_function_inhibitors(function, inhibitors[function])
    for function in stimuli:
        bm.set_function_stimuli(function, stimuli[function])

def create_bm(gn, bm, args):
    set_functions(gn, bm)
    bm.nodes = gn.metabolites
    # TODO insert preprocessing parameter
    if not args.dc:
        #print("preprocessing model...")
        preprocess_model(bm, gn.setup)
        #for function in bm.functions:
        #    print("function: ", function.name)
        #    print("-------++ ", function.inputs)
        #    print("--------- ", function.inhibitors)
        #    print("-------+-", function.double)
        #    print("------>>: ", function.targets)
        #for stim in bm.stimuli:
        #    print("stimulus: ", stim.name)
        #for node in bm.nodes:
        #    print("node: ", node.name)


def check_args():
    print("Checking arguments...")
    #TODO: change experiments help
    parser = argparse.ArgumentParser(description = "Refine command line arguments.")
    parser.add_argument('experiments', help='File containting the experiments in MIDAS format.')
    parser.add_argument('reactions', help = 'File containing the reactions in SIF format.')
    parser.add_argument('-s', '--setup', help = 'Jason file containing the setup.')
    #parser.add_argument('-e', '--experiments', help = 'File containing the experiments.')
    parser.add_argument('-i', action='store_true', help = 'ILP solver, default is SAT.')
    parser.add_argument('-t', action='store_true', help = 'Threshold functions (min nr. inputs) only.')
    parser.add_argument('-d', action='store_true', help = '2-DNF functions only.')
    parser.add_argument('-a', action='store_true', help = 'Find all models.')
    parser.add_argument('-m', action='store_true', help = 'Filter all models removing double options for the full model.')
    parser.add_argument('-b', action='store_true', help = 'Do not ban I/O for SAT, only models.')
    parser.add_argument('-n', action='store_true', help = 'No output other than time and number of solutions.')
    parser.add_argument('-l', type=int, help = 'Initial target value, only for SAT solving. Default 1')
    parser.add_argument('-p', type=int, help = 'Max number of models to find, default is unlimited')
    parser.add_argument('-v', action='store_true', help = 'No output, including gurobi, other than time and number of solutions.')
    parser.add_argument('--dc', action='store_true', help = 'Disable network compression')
    parser.add_argument('--size', action='store_true', help = 'Disable size optimization')
    args = parser.parse_args()
    return args

def print_treatments(gn):
    for treatment in gn.treatments:
        print("stimuli:")
        for stimulus in treatment.stimuli:
            print("stim:", stimulus.name, "value:", stimulus.value)
        for readout in treatment.readouts:
            print("readout:", readout.name, "value", readout.value)

def open_files(args):
    print("Opening files...")
    gn = GeneticNetwork()
    gn = read_midassif(args.experiments, args.reactions, args.setup, gn)
    #print_treatments(gn)
    return gn

if __name__ == '__main__':
    args = check_args()
    gn = open_files(args)
    bm = BooleanModel(len(gn.treatments))
    #create_bm(gn, bm, args.d)
    create_bm(gn, bm, args)
    if args.i:
        run_ilp(args, gn, bm);
    else:
        run_sat(args, gn, bm)
    unknown_gates = "("+ str(bm.unknown_gates())+")"
    print("Reactions:", gn.nr_of_reactions, ", Metabolites:", gn.nr_of_metabolites, ", Functions (unknown):", len(bm.functions), unknown_gates, ", Experiments:", bm.nr_of_experiments)
