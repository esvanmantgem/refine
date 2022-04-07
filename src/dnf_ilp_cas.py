from gurobipy import GRB
from gurobipy import *
from boolean_model import *
from math import comb
import itertools

# Set the AND values for each pair. Take also the inhibiting edges into account for this
# aka A and NOT B if B is inhibiting for the function
def set_t_pairs(m, bm):
    t_pairs = {}
    for function in bm.functions:
        if len(function.inputs) > 1:
            pair_names = list(itertools.combinations(function.inputs, 2))
            t_pairs[function.name] = []
            t_exp = []
            for e in range(bm.nr_of_experiments):
                ts = []
                for i in range(len(pair_names)):
                    a_1 = bm.activity(pair_names[i][0]).values[e]
                    a_2 = bm.activity(pair_names[i][1]).values[e]
                    t = m.addVar(vtype=GRB.BINARY, name = function.name + "_t_" + str(e))
                    if pair_names[i][0] in function.inhibitors:
                        a_1t = m.addVar(vtype=GRB.BINARY, name = function.name + "_a1t_" + str(e))
                        m.addConstr(a_1t == 1 - a_1)
                        if pair_names[i][1] in function.inhibitors:
                            a_2t = m.addVar(vtype=GRB.BINARY, name = function.name + "_a2t_" + str(e))
                            m.addConstr(a_2t == 1 - a_2)
                            m.addConstr(t == min_(a_1t, a_2t))
                        else:
                            m.addConstr(t == min_(a_1t, a_2))
                    elif pair_names[i][1] in function.inhibitors:
                        a_2t = m.addVar(vtype=GRB.BINARY, name = function.name + "_a2t_" + str(e))
                        m.addConstr(a_2t == 1 - a_2)
                        m.addConstr(t == min_(a_1, a_2t))
                    else:
                        m.addConstr(t == min_(a_1, a_2))
                    ts.append(t)
                t_exp.append(ts)
            t_pairs[function.name] = t_exp
    m.update()
    return t_pairs

# Set the activity levels of the known stimulated nodes
# If a stimulator is present for a node, the activity is 1
# If an hihibitor is present for a node, the activity is 0
# In all other cases, the value is undefined at this point
def set_stimuli(m, bm, gn):
    for i in range(len(gn.treatments)):
        treatment = gn.treatments[i]
        for stimulus in treatment.stimuli:
            if bm.activity_values(stimulus.name) != None:
                a = bm.activity_values(stimulus.name)[i]
                # If a node is inhibited, it is knocked out and so 0
                print("----------------stimname: ", stimulus.name)
                if stimulus.name in gn.setup["inhibitors"]:
                    print("kommmmmmtttieiieieieeiieie ---------------")
                    if stimulus.value == 1:
                        m.addConstr(a == 0)
                # If a node is stimulated it is 1
                else:
                    if stimulus.value == 1:
                        m.addConstr(a == 1)
                    if stimulus.value == 0:
                        m.addConstr(a == 0)
            #if bm.has_function(stimulus.name):
            #    print("stimulus nm")
            #    function = bm.get_function(stimulus.name)
            #    for input in function.inputs:
            #        m.addConstr(bm.activity_values(input)[i] == 0)


def init_activity_levels(m, bm, nodes):
    #TODO: add not if signed
    for node in nodes:
        a = ActivityLevels(node.name)
        for e in range(bm.nr_of_experiments):
            x = m.addVar(vtype=GRB.INTEGER, name = a.name + "_a_e_" + str(e))
            a.add_level(x)
        bm.add_activity_levels(a)

# init decision variable y for each function for each possible input pair
def init_y(m, bm):
    for function in bm.functions:
        # Check if inputs > 1
        if len(function.inputs) > 1:
            y = []
            for i in range(comb(len(function.inputs), 2)):
                y.append(m.addVar(vtype=GRB.INTEGER, name = function.name + "_y_" + str(i)))
            bm.add_local_tables(function.name, y)

# init decision variable x for each function for each input
def init_x(m, bm):
    for function in bm.functions:
        x = []
        for i in range(len(function.inputs)):
            x.append(m.addVar(vtype=GRB.INTEGER, name = function.name + "_x_" + str(i)))
        bm.add_global_table(function.name, x)

# adjust activity level for inhibiting edge
def get_a(m, bm, function, input):
    if input in function.inhibitors:
        input_values = []
        for e in range(bm.nr_of_experiments):
            y = m.addVar(vtype=GRB.INTEGER, name = input + "-_a_e_" + str(e))
            m.addConstr(y == 1 - bm.activity(input).values[e])
            input_values.append(y)
        m.update()
        return input_values
    else:
        return bm.activity(input).values

# allow selection of literals if literal is 1 and activity level of function is 1
def add_constraints_1(m, bm):
    for function in bm.functions:
        nr_inputs = len(function.inputs)
        for e in range(bm.nr_of_experiments):
            for input in range(nr_inputs):
                a = get_a(m, bm, function, function.inputs[input])
                x = function.x[input]
                v = m.addVar(vtype=GRB.INTEGER, name = "ax_e_" + str(e))
                m.addConstr(v == min_(a[e], x))
                m.addConstr(v <= bm.activity(function.name).values[e])
    m.update()
    #add_constraints_1a(m, bm)

# x <= -(a - c) + 1
def add_constraints_1b(m, bm):
    for function in bm.functions:
        nr_inputs = len(function.inputs)
        for input in range(nr_inputs):
            a = get_a(m, bm, function, function.inputs[input])
            for e in range(bm.nr_of_experiments):
                x = function.x[input]
                m.addConstr(x <= -1 * (a[e] - bm.activity(function.name).values[e]) + 1)
    m.update()
    #add_constraints_1a(m, bm)

# allow selection of and pairs if and-pair is 1 and activity level of function is 1
def add_constraints_2(m, bm, t_pairs):
    for function in bm.functions:
        # if function has more than 1 inputs
        if function.name in t_pairs:
            pair_names = list(itertools.combinations(function.inputs, 2))
            for e in range(bm.nr_of_experiments):
                for i in range(len(pair_names)):
                    t = t_pairs[function.name][e][i]
                    v = m.addVar(vtype=GRB.INTEGER, name = "ax_e_" + str(e))
                    m.addConstr(v == min_(t, function.y[i]))
                    m.addConstr(v <= bm.activity(function.name).values[e])
    m.update()
    #add_constraints_2a(m, bm, t_pairs)

def add_constraints_2b(m, bm, t_pairs):
    for function in bm.functions:
        if function.name in t_pairs:
            pair_names = list(itertools.combinations(function.inputs, 2))
            for i in range(len(pair_names)):
                for e in range(bm.nr_of_experiments):
                    t = t_pairs[function.name][e][i]
                    y = function.y[i]
                    m.addConstr(y <= -1 * (t - bm.activity(function.name).values[e]) + 1)
    m.update()

    #add_constraints_1a(m, bm)
def add_constraints_1a(m, bm):
    for function in bm.functions:
        nr_inputs = len(function.inputs)
        for input in range(nr_inputs):
            x = function.x[input]
            for e in range(bm.nr_of_experiments):
                a = get_a(m, bm, function, function.inputs[input])
                m.addConstr(x <= a[e])
    m.update()

# allow selection of and pairs if and-pair is 1 and activity level of function is 1
def add_constraints_2a(m, bm, t_pairs):
    for function in bm.functions:
        # if function has more than 1 inputs
        if function.name in t_pairs:
            pair_names = list(itertools.combinations(function.inputs, 2))
            for i in range(len(pair_names)):
                for e in range(bm.nr_of_experiments):
                    t = t_pairs[function.name][e][i]
                    m.addConstr(function.y[i] <=t)
    m.update()

# force at least one allowed 1 to 1 if function is 1
def add_constraints_3(m, bm, t_pairs):
    for function in bm.functions:
        inputs = len(function.inputs)
        pair_names = list(itertools.combinations(function.inputs, 2))
        for e in range(bm.nr_of_experiments):
            p = []
            # add all a * x to p
            for input in range(inputs):
                a = get_a(m, bm, function, function.inputs[input])
                x = function.x[input]
                v = m.addVar(vtype=GRB.INTEGER, name = "ax_e_" + str(e))
                m.addConstr(v == min_(a[e], x))
                p.append(v)

            # if we have input pairs check pairs and literals
            if function.name in t_pairs:
                # add all ab * y to q
                q = []
                for i in range(len(pair_names)):
                    t = t_pairs[function.name][e][i]
                    u = m.addVar(vtype=GRB.INTEGER, name = "ax_e_" + str(e))
                    m.addConstr(u == min_(t, function.y[i]))
                    q.append(u)
                m.addConstr(sum(p[i] for i in range(inputs)) +
                            sum(q[j] for j in range(len(pair_names)))
                            >= bm.activity(function.name).values[e])
            # otherwise literals only
            else:
                m.addConstr(sum(p[i] for i in range(inputs)) >= bm.activity(function.name).values[e])
    m.update()

# if we already take the single literal, we don't need and gates containing that literal
def add_constraints_4(m, bm):
    for function in bm.functions:
        pair_names = list(itertools.combinations(function.inputs, 2))
        for i in range(len(function.inputs)):
            for j in range(len(pair_names)):
                if function.inputs[i] in pair_names[j]:
                    m.addConstr(1 - function.x[i] >= function.y[j])
    m.update()

# prevent x being set to 1 if none of the a's is 1: -x OR a_e1, ..., a_en
def add_constraints_5(m, bm, t_pairs):
    for function in bm.functions:
        for input in range(len(function.inputs)):
            a = get_a(m, bm, function, function.inputs[input])
            #a = bm.activity(function.inputs[input]).values
            x = function.x[input]
            #m.addConstr(function.x[input] <= sum(a[e] for e in range(bm.nr_of_experiments)))
            m.addConstr(x <= sum(a[e] for e in range(bm.nr_of_experiments)))
            #if function.inputs[input] in function.inhibitors:
            #    m.addConstr(x <= sum(a[e] for e in range(bm.nr_of_experiments)))
            #else:
            #    m.addConstr(function.x[input] <= sum(a[e] for e in range(bm.nr_of_experiments)))
        if function.name in t_pairs:
            t = t_pairs[function.name]
            for pair in range(len(t[0])):
                m.addConstr(function.y[pair] <= sum(t[e][pair] for e in range(bm.nr_of_experiments)))
                #m.addConstr(function.y[pair] <= sum(t[e][pair] * bm.activity(function.name).values[e] for e in range(bm.nr_of_experiments)))
    m.update()

def add_constraints_6(m, bm, t_pairs):
    for function in bm.functions:
        for lit in function.x:
            m.addConstr(lit <=1)
            m.addConstr(lit >=0)
        for lit in function.y:
            m.addConstr(lit <=1)
            m.addConstr(lit >=0)
        nr_inputs = len(function.inputs)
    for activity in bm.a:
        for e in range(bm.nr_of_experiments):
                m.addConstr(activity.values[e] <=1)
                m.addConstr(activity.values[e] >=0)

## prevent x being set to 1 if none of the a's is 1: -x OR a_e1, ..., a_en
#def add_constraints_5(m, bm, t_pairs):
#    for function in bm.functions:
#        for input in range(len(function.inputs)):
#            a = get_a(m, bm, function, function.inputs[input])
#    #        for input in range(len(function.inputs)):
#                #m.addConstr(function.x[input] <= sum(a[e] * bm.activity(function.name).values[e] for e in range(bm.nr_of_experiments)))
#            m.addConstr(function.x[input] <= sum(a[e] for e in range(bm.nr_of_experiments)))
#        if function.name in t_pairs:
#            t = t_pairs[function.name]
#            for pair in range(len(t[0])):
#                m.addConstr(function.y[pair] <= sum(t[e][pair] for e in range(bm.nr_of_experiments)))
#                #m.addConstr(function.y[pair] <= sum(t[e][pair] * bm.activity(function.name).values[e] for e in range(bm.nr_of_experiments)))
#    m.update()

def add_constraints(m, bm, t_pairs):
    # allow selection of literals if literal is 1 and activity level of function is 1
    print("add contraints 1...")
    add_constraints_1(m, bm)
    #add_constraints_1b(m, bm)
    #add_constraints_1a(m, bm)
    # allow selection of and pairs if and-pair is 1 and activity level of function is 1
    print("add contraints 2...")
    add_constraints_2(m, bm, t_pairs)
    #add_constraints_2b(m, bm, t_pairs)
    #add_constraints_2a(m, bm, t_pairs)
    ## force allowed 1 to 1 if function is 1
    print("add contraints 3...")
    add_constraints_3(m, bm, t_pairs)
    # if a as literal, then all a AND b must be 0
    print("add constraints 4...")
    add_constraints_4(m, bm)
    ## ADD
    print("add constraints 5...")
    #add_constraints_5(m, bm, t_pairs)
    ## set all values 0,1
    print("add constraints 6...")
    add_constraints_6(m, bm, t_pairs)


def init_model(m, bm, nodes):
    init_activity_levels(m, bm, nodes)
    init_x(m, bm)
    init_y(m, bm)

def init_2dnf_cas_ilp(m, bm, gn):
    print("Initializing model...")
    init_model(m, bm, gn.metabolites)
    set_stimuli(m, bm, gn)
    t_pairs = set_t_pairs(m, bm)
    add_constraints(m, bm, t_pairs)
