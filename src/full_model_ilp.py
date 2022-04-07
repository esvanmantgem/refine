from gurobipy import GRB
from boolean_model import *

# Set the truthtables of all known AND gates
def set_and_xs(function, b_tables):
    b = b_tables[len(function.inputs)]
    result = [0 for i in range(function.tablesize())]
    x_values = []
    for input in function.inputs:
        value = 0 if input.startswith("!") else 1
        x_values.append(value)
    for row in range(function.tablesize()):
        correct_row = True;
        for input in range(len(function.inputs)):
            if x_values[input] != b[row][input]:
                correct_row = False
        result[row] = 1 if correct_row else 0
    return result

def init_global_table(m, bm, b_tables):
    for function in bm.functions:
        x = []
        for i in range(function.tablesize()):
            x.append(m.addVar(vtype=GRB.BINARY, name = function.name + "_x_" + str(i)))
        bm.add_global_table(function.name, x)

        # Set the known gates (i.e., the AND gates (having + in their names))
        if "+" in function.name:
            x_values = set_and_xs(function, b_tables)
            for i in range(function.tablesize()):
                m.addConstr(x[i] == x_values[i])

def init_local_tables(m, bm):
    for function in bm.functions:
        y = []
        for e in range(bm.nr_of_experiments):
            table = []
            for i in range(function.tablesize()):
                table.append(m.addVar(vtype=GRB.BINARY, name = function.name + "_y_e_" + str(e) + "_" + str(i)))
            y.append(table)
        bm.add_local_tables(function.name, y)

def init_activity_levels(m, bm, nodes):
    #TODO: add not if signed
    for node in nodes:
        a = ActivityLevels(node.name)
        for e in range(bm.nr_of_experiments):
            x = m.addVar(vtype=GRB.BINARY, name = a.name + "_a_e_" + str(e))
            a.add_level(x)
        bm.add_activity_levels(a)

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


#TODO remove depricated cur_b arg
def get_a_b(function, index, cur_b):
    # if composed function with inhibitors, we already accounted for
    # inhibitors, no need to flip again
    #if "+" in function.name and a_name.startswith("!"):
    #    a_name = a_name[1:]
    #    return (a_name, cur_b)
    #if a_name.startswith("!") and "+" not in a_name:
    #    a_name = a_name[1:]
    #    cur_b = 1 - cur_b
    #if function.is_inhibitor(index):
    #    cur_b = 1 - cur_b
    return (function.inputs[index], cur_b)

#TODO remove depricated cur_b arg
def get_b(function, index, cur_b):
    if function.is_inhibitor(index):
        cur_b = 1 - cur_b
    return cur_b

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
    else:
        return bm.activity(function.inputs[input]).values

def add_constraints_1(m, bm):
    for function in bm.functions:
        for e in range(bm.nr_of_experiments):
            for row in range(function.tablesize()):
                m.addConstr(function.y[e][row] <= function.x[row])
    m.update()

def add_constraints_2(m, bm, b_tables):
    for function in bm.functions:
        nr_inputs = len(function.inputs)
        b = b_tables[nr_inputs]
        for e in range(bm.nr_of_experiments):
            for row in range(function.tablesize()):
                for input in range(nr_inputs):
                    cur_b = b[row][input]
                    a = bm.activity(function.inputs[input]).values
                    m.addConstr(function.y[e][row] <= (1 - cur_b) + a[e] * (2 * cur_b - 1))
    m.update()

def add_constraints_3(m, bm, b_tables):
    for function in bm.functions:
        nr_inputs = len(function.inputs)
        b = b_tables[nr_inputs]
        for e in range(bm.nr_of_experiments):
            for row in range(function.tablesize()):
                a_b = []
                for input in range(nr_inputs):
                    a_b.append([bm.activity(function.inputs[input]), b[row][input]])
                # Here a = bm.activity(function.inputs[input]).values, where function.inputs[input] is the current input name
            m.addConstr(function.y[e][row] >= function.x[row] + sum(2 * a_b[input][1] * a_b[input][0].values[e] - a_b[input][0].values[e] - a_b[input][1] for input in range(nr_inputs)))
    m.update()

#def add_constraints_2(m, bm, b_tables):
#    for function in bm.functions:
#        nr_inputs = len(function.inputs)
#        b = b_tables[nr_inputs]
#        for e in range(bm.nr_of_experiments):
#            for row in range(function.tablesize()):
#                for input in range(nr_inputs):
#                    #(a_name, cur_b) = get_a_b(function, function.inputs[input], b[row][input])
#                    #(a_name, cur_b) = get_a_b(function, input, b[row][input])
#                    a = bm.activity(function.inputs[input]).values
#                    #a = get_a(m, bm, function, input)
#                    #cur_b = get_b(function, input, b[row][input])
#                    cur_b = b[row][input]
#                    #a = bm.activity(function.inputs[input]).values
#                    m.addConstr(function.y[e][row] <= (1 - cur_b) + a[e] * (2 * cur_b - 1))
#    m.update()
#def add_constraints_3(m, bm, b_tables):
#    for function in bm.functions:
#        nr_inputs = len(function.inputs)
#        b = b_tables[nr_inputs]
#        for e in range(bm.nr_of_experiments):
#            for row in range(function.tablesize()):
#                a_b = []
#                for input in range(nr_inputs):
##                    print("function: ", function.name, " with input ", function.inputs[input])
#
#                    #a_b.append(list(get_a_b(function, function.inputs[input], b[row][input])))
#                    a_b.append(list(get_a_b(function, input, b[row][input])))
#                    #a_b.append([get_a(m, bm, function, input), b[row][input]])
#                    #a_b.append([input, get_b(function, input, b[row][input])])
#                # Here a = bm.activity(function.inputs[input]).values, where function.inputs[input] is the current input name
#                    #m.addConstr(function.y[e][row] >= function.x[row] + sum(2 * a_b[input][1] * get_a(m, bm, function, a_b[input][0])[e] - get_a(m, bm, function, a_b[input][0])[e] - a_b[input][1] for input in range(nr_inputs)))
#                m.addConstr(function.y[e][row] >= function.x[row] + sum(2 * a_b[input][1] * bm.activity(a_b[input][0]).values[e] - bm.activity(a_b[input][0]).values[e] - a_b[input][1] for input in range(nr_inputs)))
#    m.update()
#
def add_constraints_4(m, bm):
    for function in bm.functions:
        for e in range(bm.nr_of_experiments):
            for row in range(function.tablesize()):
                m.addConstr(function.y[e][row] <= bm.activity(function.name).values[e])
                m.addConstr(bm.activity(function.name).values[e] <= 1)
    m.update()

def add_constraints_5(m, bm):
    for function in bm.functions:
        for e in range(bm.nr_of_experiments):
            m.addConstr(bm.activity(function.name).values[e] <= sum(function.y[e][row] for row in range(function.tablesize())))
    m.update()

def add_constraints_6(m, bm, b_sum):
    for function in bm.functions:
        b = b_sum[len(function.get_unique_inputs())]
        indices = []
        for size in range(len(set(b))):
            #indices = [i for i, x in enumerate(my_list) if x == "whatever"]
            indices.append([i for i, x in enumerate(b) if x == size])
        for size in range(len(indices) - 1):
            for next_size in indices[size+1]:
                m.addConstr(function.x[size] <= function.x[next_size])


def add_constraints(m, bm, b, b_sum):
    #print("add contraints 1...")
    add_constraints_1(m, bm)
    #print("add contraints 2...")
    add_constraints_2(m, bm, b)
    #print("add contraints 3...")
    add_constraints_3(m, bm, b)
    #print("add contraints 4...")
    add_constraints_4(m, bm)
    #print("add contraints 5...")
    add_constraints_5(m, bm)
    #print("add contraints 6...")
    #add_constraints_6(m, bm, b_sum)

def init_model(m, bm, nodes, b_tables):
    init_global_table(m, bm, b_tables)
    init_local_tables(m, bm)
    init_activity_levels(m, bm, nodes)

def create_b(max_size):
    b = []
    b_sum = []
    b.append([])
    b.append([[0],[1]])
    b_sum.append([])
    b_sum.append([ 0, 1])

    for size in range(2,max_size+1):
        size_b = []
        sum_row_b = []
        for row in range(pow(2, size)):
            bin_rep = "{0:b}".format(row)
            bin_rep = bin_rep.zfill(size)
            row_values = []
            for element in bin_rep:
                row_values.append(int(element))
            size_b.append(row_values)
            sum_row_b.append(sum(row_values))
        b_sum.append(sum_row_b)
        b.append(size_b)
    return (b, b_sum)

def get_max_fan_in(bm):
    max_size = 0
    for function in bm.functions:
        if len(function.inputs) > max_size:
            max_size = len(function.inputs)
    return max_size

def init_full_model_ilp(m, bm, gn):
    (b_tables, b_sum) = create_b(get_max_fan_in(bm))
    print("Initializing model...")
    init_model(m, bm, gn.metabolites, b_tables)
    set_stimuli(m, bm, gn)
    add_constraints(m, bm, b_tables, b_sum)
