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
        if len(list(set(function.inputs))) > 1:
#            function.create_pair_names()
            #pair_names = list(itertools.combinations(list(set(function.inputs)), 2))
            pair_names = function.pair_names
            t_pairs[function.name] = []
            t_exp = []
            for e in range(bm.nr_of_experiments):
                ts = []
                for i in range(len(pair_names)):
                    index_1 = function.get_input_index(pair_names[i][0])
                    index_2 = function.get_input_index(pair_names[i][1])
                    a_1 = get_a(m, bm, function, index_1)[e]
                    a_2 = get_a(m, bm, function, index_2)[e]
                    t = m.addVar(vtype=GRB.BINARY, name = function.name + "_t_" + pair_names[i][0] + "_" + pair_names[i][1] + str(e))
                    m.addConstr(t == min_(a_1, a_2))
                    ts.append(t)
                t_exp.append(ts)
            t_pairs[function.name] = t_exp
    m.update()
    return t_pairs

# Set the value of nodes that are not stimuli and do not have any inputs to 0
def set_non_input_nodes(m, bm, gn):
    #for node in gn.metabolites:
    for node in bm.nodes:
        if (not bm.has_function(node.name)):
            if (not node.name in gn.setup["stimuli"]):
                for i in range(len(gn.treatments)):
                    a = bm.activity_values(node.name)[i]
                    m.addConstr(a == 0)

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
                if stimulus.name in gn.setup["inhibitors"]:
                    if stimulus.value == 1:
                        m.addConstr(a == 0)
                # If a node is stimulated it is 1
                else:
                    if stimulus.value == 1:
                        m.addConstr(a == 1)
                        #if bm.has_function(stimulus.name):
                        #    print("stimulus nm")
                        #    function = bm.get_function(stimulus.name)
                        #    for x in function.x:
                        #        m.addConstr(x == 0)
                    if stimulus.value == 0:
                        m.addConstr(a == 0)

def init_activity_levels(m, bm):
    for node in bm.nodes:
        a = ActivityLevels(node.name)
        for e in range(bm.nr_of_experiments):
            x = m.addVar(vtype=GRB.BINARY, name = "act_" + a.name + "_" + str(e))
            a.add_level(x)
        bm.add_activity_levels(a)

# adjust activity level for inhibiting edge
def get_a(m, bm, function, input):
    #if function.inputs[input] in function.inhibitors:
    if function.is_inhibitor(input):
        #if input == len(function.inputs) -1 or function.inputs[input+1] != function.inputs[input]:
        if bm.has_inh_activity(function.inputs[input]) :
            return bm.get_inh_activity(function.inputs[input])
        else:
            a_inh = ActivityLevels(function.inputs[input])
            #input_values = []
            for e in range(bm.nr_of_experiments):
                y = m.addVar(vtype=GRB.BINARY, name = function.inputs[input] + "_inv_" + str(e))
                m.addConstr(y == 1 - bm.activity(function.inputs[input]).values[e])
                #input_values.append(y)
                a_inh.add_level(y)
            bm.add_inh_activity(a_inh)
            m.update()
            return a_inh.values
        #else:
        #    return bm.activity(function.inputs[input]).values
    else:
        return bm.activity(function.inputs[input]).values

## adjust activity level for inhibiting edge
#def get_a(m, bm, function, input):
#    if input in function.inhibitors:
#        input_values = []
#        for e in range(bm.nr_of_experiments):
#            y = m.addVar(vtype=GRB.BINARY, name = "-" + input + "_" + str(e))
#            m.addConstr(y == 1 - bm.activity(input).values[e])
#            input_values.append(y)
#        m.update()
#        return input_values
#    else:
#        return bm.activity(input).values

# init decision variable y for each function for each possible input pair
def init_y(m, bm):
    for function in bm.functions:
        function.create_pair_names()
        # Check if inputs > 1
        if len(function.inputs) > 1:
            y = []
       #     for i in range(comb(len(function.inputs), 2)):
            for i in range(len(function.pair_names)):
                y.append(m.addVar(vtype=GRB.BINARY, name = function.name + "_y_" + str(i)))
            bm.add_local_tables(function.name, y)

# init decision variable x for each function for each input
def init_x(m, bm):
    for function in bm.functions:
        x = []
        for i in range(len(function.inputs)):
            x.append(m.addVar(vtype=GRB.BINARY, name = function.name + "_x_" + str(i)))
        bm.add_global_table(function.name, x)


# allow selection of literals if literal is 1 and activity level of function is 1
def add_constraints_1(m, bm, gn):
    for function in bm.functions:
        #if not function.name in gn.setup["inhibitors"]:
        nr_inputs = len(function.inputs)
        e_ax = []
        for e in range(bm.nr_of_experiments):
            if not gn.stimulus_on(function.name, e):
                ax = []
                for input in range(nr_inputs):
                    #a = get_a(m, bm, function, function.inputs[input])
                    a = get_a(m, bm, function, input)
                    x = function.x[input]
                    v = m.addVar(vtype=GRB.BINARY, name = function.name + "x_" + function.inputs[input] + "_"  + str(input) + str(e))
                    m.addConstr(v == min_(a[e], x))
                    m.addConstr(v <= bm.activity(function.name).values[e])
                    ax.append(v)
                e_ax.append(ax)
            else:
                e_ax.append(None)
        bm.add_e_ax(function.name, e_ax)
    m.update()

# allow selection of and pairs if and-pair is 1 and activity level of function is 1
def add_constraints_2(m, bm, t_pairs, gn):
    for function in bm.functions:
        # if function has more than 1 inputs
        if function.name in t_pairs:
            #if not function.name in gn.setup["inhibitors"]:
            #pair_names = list(itertools.combinations(function.inputs, 2))
            pair_names = function.pair_names
            e_aby = []
            for e in range(bm.nr_of_experiments):
                if not gn.stimulus_on(function.name, e):
                    aby = []
                    for i in range(len(pair_names)):
                        t = t_pairs[function.name][e][i]
                        v = m.addVar(vtype=GRB.BINARY, name = function.name + "y_"+ pair_names[i][0] + "_" + pair_names[i][1] +  str(e))
                        m.addConstr(v == min_(t, function.y[i]))
                        m.addConstr(v <= bm.activity(function.name).values[e])
                        aby.append(v)
                    e_aby.append(aby)
                else:
                    e_aby.append(None)
            bm.add_e_aby(function.name, e_aby)

    m.update()

def add_constraints_3(m, bm, t_pairs, gn):
    for function in bm.functions:
        inputs = len(function.inputs)
        #pair_names = list(itertools.combinations(function.inputs, 2))
        pair_names = function.pair_names
        for e in range(bm.nr_of_experiments):
            # In case the function has its value set as stimulus, the inputs are allowed to be 0
            if not gn.stimulus_on(function.name, e):
                p = function.e_ax[e]
                #p = []
                # add all a * x to p
                #for input in range(inputs):
                #    a = get_a(m, bm, function, function.inputs[input])
                #    x = function.x[input]
                #    v = m.addVar(vtype=GRB.BINARY, name = "ax_e_" + str(e))
                #    m.addConstr(v == min_(a[e], x))
                #    p.append(v)


                # if we have input pairs check pairs and literals
                if function.name in t_pairs:
                    q = function.e_aby[e]
                #    q = []
                    # add all ab * y to q
                    #for i in range(len(pair_names)):
                    #    t = t_pairs[function.name][e][i]
                    #    u = m.addVar(vtype=GRB.BINARY, name = "ax_e_" + str(e))
                    #    m.addConstr(u == min_(t, function.y[i]))
                    #    q.append(u)
                    #m.addConstr(sum(p[i] for i in range(inputs)) + sum(q[j] for j in range(len(pair_names))) >= bm.activity(function.name).values[e])
                    m.addConstr(sum(p[i] for i in range(inputs)) + sum(q[j] for j in range(len(pair_names))) >= bm.activity(function.name).values[e])
                # otherwise literals only
                else:
                    m.addConstr(sum(p[i] for i in range(inputs)) >= bm.activity(function.name).values[e])
    m.update()
# force at least one allowed 1 to 1 if function is 1
#def add_constraints_3(m, bm, t_pairs, gn):
#    for function in bm.functions:
#        inputs = len(function.inputs)
#        pair_names = list(itertools.combinations(function.inputs, 2))
#        for e in range(bm.nr_of_experiments):
#            # In case the function has its value set as stimulus, the inputs are allowed to be 0
#            if not gn.stimulus_on(function.name, e):
#                p = []
#                # add all a * x to p
#                for input in range(inputs):
#                    a = get_a(m, bm, function, function.inputs[input])
#                    x = function.x[input]
#                    v = m.addVar(vtype=GRB.BINARY, name = "ax_e_" + str(e))
#                    m.addConstr(v == min_(a[e], x))
#                    p.append(v)
#
#                # if we have input pairs check pairs and literals
#                if function.name in t_pairs:
#                    # add all ab * y to q
#                    q = []
#                    for i in range(len(pair_names)):
#                        t = t_pairs[function.name][e][i]
#                        u = m.addVar(vtype=GRB.BINARY, name = "ax_e_" + str(e))
#                        m.addConstr(u == min_(t, function.y[i]))
#                        q.append(u)
#                    m.addConstr(sum(p[i] for i in range(inputs)) +
#                                sum(q[j] for j in range(len(pair_names)))
#                                >= bm.activity(function.name).values[e])
#                # otherwise literals only
#                else:
#                    m.addConstr(sum(p[i] for i in range(inputs)) >= bm.activity(function.name).values[e])
#    m.update()
#
# if we already take the single literal, we don't need and gates containing that literal
def add_constraints_4(m, bm):
    for function in bm.functions:
        #pair_names = list(itertools.combinations(function.inputs, 2))
        pair_names = function.pair_names
        for i in range(len(function.inputs)):
            for j in range(len(pair_names)):
                if function.inputs[i] in pair_names[j]:
                    m.addConstr(1 - function.x[i] >= function.y[j])
    m.update()

# prevent x being set to 1 if none of the a's is 1: -x OR a_e1, ..., a_en
#def add_constraints_5(m, bm, t_pairs):
#    for function in bm.functions:
#        for input in range(len(function.inputs)):
#            #a = get_a(m, bm, function, function.inputs[input])
#            a = get_a(m, bm, function, input)
#            #a = bm.activity(function.inputs[input]).values
#            x = function.x[input]
#            #m.addConstr(function.x[input] <= sum(a[e] for e in range(bm.nr_of_experiments)))
#            m.addConstr(x <= sum(a[e] for e in range(bm.nr_of_experiments)))
#            #if function.inputs[input] in function.inhibitors:
#            #    m.addConstr(x <= sum(a[e] for e in range(bm.nr_of_experiments)))
#            #else:
#            #    m.addConstr(function.x[input] <= sum(a[e] for e in range(bm.nr_of_experiments)))
#        if function.name in t_pairs:
#            t = t_pairs[function.name]
#            for pair in range(len(t[0])):
#                m.addConstr(function.y[pair] <= sum(t[e][pair] for e in range(bm.nr_of_experiments)))
#                #m.addConstr(function.y[pair] <= sum(t[e][pair] * bm.activity(function.name).values[e] for e in range(bm.nr_of_experiments)))
#    m.update()

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

def add_constraints(m, bm, t_pairs, gn):
    # allow selection of literals if literal is 1 and activity level of function is 1
    #print("add contraints 1...")
    add_constraints_1(m, bm, gn)
    # allow selection of and pairs if and-pair is 1 and activity level of function is 1
    #print("add contraints 2...")
    add_constraints_2(m, bm, t_pairs, gn)
    ## force allowed 1 to 1 if function is 1
    #print("add contraints 3...")
    add_constraints_3(m, bm, t_pairs, gn)
    # if a as literal, then all a AND b must be 0
    #print("add constraints 4...")
    add_constraints_4(m, bm)
    ## ADD
    #print("add constraints 5...")
    #add_constraints_5(m, bm, t_pairs)


def init_model(m, bm):
    init_activity_levels(m, bm)
    init_x(m, bm)
    init_y(m, bm)

def init_2dnf_model_ilp(m, bm, gn):
    print("Initializing model...")
    init_model(m, bm)
    set_stimuli(m, bm, gn)
    set_non_input_nodes(m, bm, gn)
    t_pairs = set_t_pairs(m, bm)
    add_constraints(m, bm, t_pairs, gn)
