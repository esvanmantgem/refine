import itertools
from math import comb
from sat_solver import *
from boolean_model import *


def init_activity_levels(s, bm, nodes):
    for node in nodes:
        a = ActivityLevels(node.name)
        for e in range(bm.nr_of_experiments):
            x = s.add_lit()
            a.add_level(x)
        bm.add_activity_levels(a)

# Set the activity levels of the known stimulated nodes
# If a stimulator is present for a node, the activity is 1
# If an hihibitor is present for a node, the activity is 0
# In all other cases, the value is undefined at this point
def set_stimuli(s, bm, gn):
    for i in range(len(gn.treatments)):
        for stimulus in gn.treatments[i].stimuli:
            a = bm.activity_values(stimulus.name)[i]
            # If a node is inhibited, it is knocked out and so 0
            if stimulus.name in gn.setup["inhibitors"]:
                if stimulus.value == 1:
                    s.add_clause([-a])
            else:
            # Otherwise, if a node is stimulated it is 1
                if stimulus.value == 1:
                    s.add_clause([a])

# init tseytin pairs for each function for each experinent and each input pair
# t_pairs [function = exp[pair]]
# Set the AND values for each pair. Take also the inhibiting edges into account for this
# aka A and NOT B if B is inhibiting for the function
def set_t_pairs(s, bm):
    t_pairs = {}
    for function in bm.functions:
        # Check if more than 1 input, otherwise no pairs need to be set
        if len(function.inputs) > 1:
            pair_names = list(itertools.combinations(function.inputs, 2))
            t_pairs[function.name] = []
            t_exp = []
            # For each experiment
            for e in range(bm.nr_of_experiments):
                ts = []
                # For each pair
                for i in range(len(pair_names)):
                    #a_1 = get_a(bm, function, pair_names[i][0])
                    #a_2 = get_a(bm, function, pair_names[i][1])
                    a_1 = bm.activity_values(pair_names[i][0])
                    a_2 = bm.activity_values(pair_names[i][1])
                    # Adjust for inhibiting interactions if needed and create the tseytin variable
                    if pair_names[i][0] in function.inhibitors:
                        if pair_names[i][1] in function.inhibitors:
                            ts.append(add_and_tseytin(s, [-a_1[e], -a_2[e]]))
                        else:
                            ts.append(add_and_tseytin(s, [-a_1[e], a_2[e]]))
                    elif pair_names[i][1] in function.inhibitors:
                        ts.append(add_and_tseytin(s, [a_1[e], -a_2[e]]))
                    else:
                        ts.append(add_and_tseytin(s, [a_1[e], a_2[e]]))
                t_exp.append(ts)
            t_pairs[function.name] = t_exp
    return t_pairs

# Create a tseytin var for the AND of all elements
def add_and_tseytin(s, elements):
    q = s.add_lit()
    tseytin_clause = [q]
    for element in elements:
        s.add_clause([-q, element])

        tseytin_clause.append(-element)
    s.add_clause(tseytin_clause)
    return q

# Init decision variables y for each function for each possible input pair
def init_y(s, bm):
    for function in bm.functions:
        # Check if inputs > 1
        if len(function.inputs) > 1:
            y = []
            for i in range(comb(len(function.inputs), 2)):
                y.append(s.add_lit())
            bm.add_local_tables(function.name, y)

# Init decision variables x for each function for each input
def init_x(s, bm):
    for function in bm.functions:
        x = []
        for i in range(len(function.inputs)):
            x.append(s.add_lit())
        bm.add_global_table(function.name, x)

# Return the activity level adjusted for inhibiting interactions
def get_a(bm, function, input):
    if input in function.inhibitors:
        inputs = []
        for activity in bm.activity_values(input):
            inputs.append(-activity)
        return inputs
    else:
        return bm.activity_values(input)

# Prevent selection of a literal if the literal is active but the function is off
# a AND x -> function
def add_clauses_1(s, bm):
    for function in bm.functions:
        nr_inputs = len(function.inputs)
        for e in range(bm.nr_of_experiments):
            for input in range(nr_inputs):
                a = get_a(bm, function, function.inputs[input])
                # not (a AND x) or f == a AND x -> f
                s.add_clause([-a[e], -function.x[input], bm.activity(function.name).values[e]])

# Prevent selection of a pair if the literals of the pair are active but the function is off
# (a_1 AND a_2) AND y -> f
def add_clauses_2(s, bm, t_pairs):
    for function in bm.functions:
        # if function has more than 1 inputs
        if function.name in t_pairs:
            pair_names = list(itertools.combinations(function.inputs, 2))
            for e in range(bm.nr_of_experiments):
                for i in range(len(pair_names)):
                    t = t_pairs[function.name][e][i]
                    s.add_clause([-t, -function.y[i], bm.activity(function.name).values[e]])

# force at least one literal or pair to be selected if the function is on
# a -> AND xa or AND yab
def add_clauses_3(s, bm, t_pairs):
    for function in bm.functions:
        inputs = len(function.inputs)
        pair_names = list(itertools.combinations(function.inputs, 2))
        for e in range(bm.nr_of_experiments):
            a = []
            for input in range(inputs):
                a.append(get_a(bm, function, function.inputs[input]))
            sum_xy = []
            for i in range(inputs):
                sum_xy.append(add_and_tseytin(s, [a[i][e], function.x[i]]))

            # if we have input pairs check pairs and literals
            if function.name in t_pairs:
                for j in range(len(pair_names)):
                    sum_xy.append(add_and_tseytin(s, [t_pairs[function.name][e][j], function.y[j]]))
            sum_xy.append(-bm.activity(function.name).values[e])
            s.add_clause(sum_xy)

# prevent redundant clauses, i.e., selecting a pair if we already select one of the literals
# x -> not y
def add_clauses_4(s, bm):
    for function in bm.functions:
        pair_names = list(itertools.combinations(function.inputs, 2))
        for i in range(len(function.inputs)):
            for j in range(len(pair_names)):
                if function.inputs[i] in pair_names[j]:
                    s.add_clause([-function.x[i], -function.y[j]])

def add_clauses(s, bm, t_pairs):
    # Prevent selection of a literal if the literal is active but the function is off
    # a AND x -> function
    print("add clauses 1...")
    add_clauses_1(s, bm)
    # Prevent selection of a pair if the literals of the pair are active but the function is off
    # (a_1 AND a_2) AND y -> f
    print("add clauses 2...")
    add_clauses_2(s, bm, t_pairs)
    # force at least one literal or pair to be selected if the function is on
    # a -> AND xa or AND yab
    print("add clauses 3...")
    add_clauses_3(s, bm, t_pairs)
    # prevent redundant clauses, i.e., selecting a pair if we already select one of the literals
    # x -> not y
    print("add clauses 4...")
    add_clauses_4(s, bm)

def init_model(s, bm, nodes):
    # Init decision variables for input literals
    init_x(s, bm)
    # Init decision variables for input pairs
    init_y(s, bm)
    # Init the activity levels for each node and each experiment
    init_activity_levels(s, bm, nodes)

def init_2dnf_model_sat(s, bm ,gn):
    print("Initializing model...")
    init_model(s, bm, gn.metabolites)
    set_stimuli(s, bm, gn)
    # Set tseytin variables for each input pair in each function for each experiment
    t_pairs = set_t_pairs(s, bm)
    add_clauses(s, bm, t_pairs)
