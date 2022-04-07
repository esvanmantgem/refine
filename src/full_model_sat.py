from sat_solver import *
from boolean_model import *

def print_bm(bm):
    print("functions:")
    for function in bm.functions:
        print("inputs", function.name, function.inputs)
        print("inhibs", function.name, function.inhibitors)

# Create both boolean as well as lit versions of B. B is the values of the input of functions in truthtables in lexicographic order
def create_b(s, max_size):
    # Manually create table of one input
    b = {}
    b_bool = []
    b_lits = []
    b_lits.append([])
    b_bool.append([])
    first = s.add_lit()
    second = s.add_lit()
    s.add_clause([-first])
    s.add_clause([second])
    b_bool.append([[False], [True]])
    b_lits.append([[first],[second]])

    # Automatically create all tables for inputs > 2
    for size in range(2,max_size+1):
        size_b_lits = []
        size_b_bool = []
        for row in range(pow(2, size)):
            bin_rep = "{0:b}".format(row)
            bin_rep = bin_rep.zfill(size)
            row_lits = []
            row_bool = []
            for element in bin_rep:
                #element = True if "1" in element else False
                cur_b = s.add_lit()
                row_lits.append(cur_b)
                if element == "1":
                    s.add_clause([cur_b])
                    row_bool.append(True)
                else:
                    s.add_clause([-cur_b])
                    row_bool.append(False)
            size_b_lits.append(row_lits)
            size_b_bool.append(row_bool)
        b_lits.append(size_b_lits)
        b_bool.append(size_b_bool)
    b["bool"] = b_bool
    b["lits"] = b_lits
    return b

def get_max_fan_in(bm):
    max_size = 0
    for function in bm.functions:
        if len(function.inputs) > max_size:
            max_size = len(function.inputs)
    return max_size

# Set known and gates
def set_and_xs(s, function, b_tables):
    b = b_tables[len(function.inputs)]
    result = [False for i in range(function.tablesize())]
    x_values = []
    for input in function.inputs:
        value = False if input.startswith("!") else True
        x_values.append(value)
    for row in range(function.tablesize()):
        result[row] = True
        for input in range(len(function.inputs)):
            if x_values[input] != b[row][input]:
                result[row] = False
        if result[row]:
            s.add_clause([function.x[row]])
        else:
            s.add_clause([-function.x[row]])

def init_global_table(s, bm, b_tables):
    for function in bm.functions:
        x = []
        for i in range(function.tablesize()):
            x.append(s.add_lit())
        bm.add_global_table(function.name, x)

        # Set the known gates (i.e., the AND gates (having + in their names))
        if "+" in function.name:
            set_and_xs(s, function, b_tables)

def init_local_tables(s, bm):
    for function in bm.functions:
        y = []
        for e in range(bm.nr_of_experiments):
            table = []
            for i in range(function.tablesize()):
                table.append(s.add_lit())
            y.append(table)
        bm.add_local_tables(function.name, y)

def init_activity_levels(s, bm, nodes):
    #TODO: add not if signed
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
            # TODO check if not removed by compressions
            if bm.activity_values(stimulus.name) != None:
                a = bm.activity_values(stimulus.name)[i]
                # If a node is inhibited, it is knocked out and so 0
                if stimulus.name in gn.setup["inhibitors"]:
                    if stimulus.value == 1:
                        s.add_clause([-a])
                else:
                # Otherwise, if a node is stimulated it is 1
                    if stimulus.value == 1:
                        s.add_clause([a])
#def set_stimuli(s, bm, gn):
#    for i in range(len(gn.treatments)):
#        for stimulus in gn.treatments[i].stimuli:
#            a = bm.activity_values(stimulus.name)[i]
#            # handle inhibitors
#            if stimulus.name in gn.setup["inhibitors"]:
#                if stimulus.value == 1:
#                    s.add_clause([-a])
#            # handle stimuli
#            else:
#                if stimulus.value == 0:
#                    s.add_clause([-a])
#                else:
#                    s.add_clause([a])

# Return the activity level adjusted for inhibiting interactions
def get_a(bm, function, input):
    if input in function.inhibitors:
        inputs = []
        for activity in bm.activity_values(input):
            inputs.append(-activity)
        return inputs
    else:
        return bm.activity_values(input)

def get_b(function, a_name, b):
    # flip in case a_name is inhibitor of function
    if function.is_inhibitor(a_name):
        b = -b
    return b

def get_a_b(function, a_name, b):
    # if composed function with inhibitors, we already accounted for
    # inhibitors, no need to flip again
    if "+" in function.name and a_name.startswith("!"):
        a_name = a_name[1:]
        return (a_name, b)
    if a_name.startswith("!") and "+" not in a_name:
        a_name = a_name[1:]
        b = -b
    # flip in case a_name is inhibitor of function
    if function.is_inhibitor(a_name):
        b = -b
    return (a_name, b)

# y -> x:  not y or x
def add_clauses_1(s, bm):
    for function in bm.functions:
        y = function.y
        x = function.x
        for e in range(bm.nr_of_experiments):
            for row in range(function.tablesize()):
                s.add_clause([-y[e][row], x[row]])

## y -> (a <=> b):  (not a or b or not y) AND (a or not b or not y)
#def add_clauses_2(s, bm, b_map):
#    for function in bm.functions:
#        b = b_map[len(function.inputs)]
#        y = function.y
#        for e in range(bm.nr_of_experiments):
#            size = function.tablesize()
#            for row in range(size):
#                nr_inputs = len(function.inputs)
#                for input in range(nr_inputs):
#                    #(a_name, cur_b) = get_a_b(function.name, function.inputs[input], b[row][input])
#                    (a_name, cur_b) = get_a_b(function, function.inputs[input], b[row][input])
#                    cur_a = bm.activity_values(a_name)
#                    s.add_clause([-cur_a[e], cur_b, -y[e][row]])
#                    s.add_clause([cur_a[e], -cur_b, -y[e][row]])

# y -> (a <=> b):  (not a or b or not y) AND (a or not b or not y)
def add_clauses_2(s, bm, b_map):
    for function in bm.functions:
        b = b_map[len(function.inputs)]
        y = function.y
        for e in range(bm.nr_of_experiments):
            size = function.tablesize()
            for row in range(size):
                nr_inputs = len(function.inputs)
                for input in range(nr_inputs):
                    #(a_name, cur_b) = get_a_b(function.name, function.inputs[input], b[row][input])
                    cur_b = get_b(function, function.inputs[input], b[row][input])
                    cur_a = bm.activity_values(function.inputs[input])
                    #s.add_clause([-cur_a[e], b[row][input], -y[e][row]])
                    #s.add_clause([cur_a[e], -b[row][input], -y[e][row]])
                    s.add_clause([-cur_a[e], cur_b, -y[e][row]])
                    s.add_clause([cur_a[e], -cur_b, -y[e][row]])

## x AMD (A <=> B) -> Y: not x or not (A == B) or -y
#def add_clauses_3(s, bm, b_map):
#    for function in bm.functions:
#        b = b_map[len(function.inputs)]
#        y = function.y
#        x = function.x
#        for e in range(bm.nr_of_experiments):
#            size = function.tablesize()
#            for row in range(size):
#                r = s.add_lit()
#                s.add_clause([-x[row], -r, y[e][row]])
#                nr_inputs = len(function.inputs)
#                inis = []
#                for input in range(nr_inputs):
#                    ini = s.add_lit()
#                    inis.append(-ini)
#                    s.add_clause([-r, ini])
#                    #a_level = bm.activity_values(function.inputs[input])
#                    (a_name, cur_b) = get_a_b(function, function.inputs[input], b[row][input])
#                    cur_a = bm.activity_values(a_name)
#                    s.add_clause([-cur_a[e], cur_b, -ini])
#                    s.add_clause([-cur_a[e], -cur_b, ini])
#                    s.add_clause([cur_a[e], -cur_b, -ini])
#                    s.add_clause([cur_a[e], cur_b, ini])
#                inis.append(r)
#                s.add_clause(inis)
# x AMD (A <=> B) -> Y: not x or not (A == B) or -y
def add_clauses_3(s, bm, b_map):
    for function in bm.functions:
        b = b_map[len(function.inputs)]
        y = function.y
        x = function.x
        for e in range(bm.nr_of_experiments):
            size = function.tablesize()
            for row in range(size):
                r = s.add_lit()
                s.add_clause([-x[row], -r, y[e][row]])
                nr_inputs = len(function.inputs)
                inis = []
                for input in range(nr_inputs):
                    ini = s.add_lit()
                    inis.append(-ini)
                    s.add_clause([-r, ini])
                    #a_level = bm.activity_values(function.inputs[input])
                    #cur_a = get_a(bm, function, function.inputs[input])
                    #cur_b = b[row][input]
                    cur_b = get_b(function, function.inputs[input], b[row][input])
                    cur_a = bm.activity_values(function.inputs[input])
                    s.add_clause([-cur_a[e], cur_b, -ini])
                    s.add_clause([-cur_a[e], -cur_b, ini])
                    s.add_clause([cur_a[e], -cur_b, -ini])
                    s.add_clause([cur_a[e], cur_b, ini])
                inis.append(r)
                s.add_clause(inis)

# y -> a: not y or a
def add_clauses_4(s, bm):
    for function in bm.functions:
        y = function.y
        for e in range(bm.nr_of_experiments):
            size = function.tablesize()
            cur_a = bm.activity_values(function.name)
            for row in range(size):
                s.add_clause([-y[e][row], cur_a[e]])

# a -> sum y: -a or y1 or y2 or y...
def add_clauses_5(s, bm):
    for function in bm.functions:
        y = function.y
        for e in range(bm.nr_of_experiments):
            size = function.tablesize()
            cur_a = bm.activity_values(function.name)
            temp_clause = []
            for row in range(size):
                temp_clause.append(y[e][row])
            temp_clause.append(-cur_a[e])
            s.add_clause(temp_clause)

def add_clauses(s, bm, b):
    print("add clauses 1...")
    add_clauses_1(s, bm)
    print("add clauses 2...")
    add_clauses_2(s, bm, b)
    print("add clauses 3...")
    add_clauses_3(s, bm, b)
    print("add clauses 4...")
    add_clauses_4(s, bm)
    print("add clauses 5...")
    add_clauses_5(s, bm)

def init_model(s, bm, nodes, b_tables):
    init_global_table(s, bm, b_tables)
    init_local_tables(s, bm)
    init_activity_levels(s, bm, nodes)

def init_full_model_sat(s, bm, gn):
    b_tables = create_b(s, get_max_fan_in(bm))
    print("Initializing model...")
    init_model(s, bm, gn.metabolites, b_tables["bool"])
    set_stimuli(s, bm, gn)
    add_clauses(s, bm, b_tables["lits"])
