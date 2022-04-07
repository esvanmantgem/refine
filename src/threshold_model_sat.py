import itertools
from sat_solver import *
from boolean_model import *

def add_and_tseytin(s, elements):
    q = s.add_lit()
    tseytin_clause = [q]
    for element in elements:
        s.add_clause([-q, element])

        tseytin_clause.append(-element)
    s.add_clause(tseytin_clause)
    return q

def add_or_tseytin(s, elements):
    q = s.add_lit()
    tseytin_clause = [-q]
    for element in elements:
        s.add_clause([q, -element])

        tseytin_clause.append(element)
    s.add_clause(tseytin_clause)
    return q

# Let z be the threshold function: an array of lenght nr of inputs with the
# index representing the number of activated (resp. inhibited) inputs. If the
# number of activated inputs is above the threshold, the value of
# z[nr_of_activated_iputs] is 1, otherwise 0. By default threshold 1 is always
# 1.This can be put to 0 (i.e., turning off the influence of the function
# completely) by setting the bool zero_inclusive to true

# TODO check if all i / k as written down is necessary: subset size 3 voor i is 1>
def add_clauses(s, bm):
    for function in bm.functions:
        z = function.z

        # z[0], threshold >= 0 is always true
        s.add_clause([z[0]])
        for e in range(bm.nr_of_experiments):
            # Get the activity values for this experiment
            a = bm.activity_values(function.name)[e]
            inputs_activity = []
            for input in function.inputs:
                #if input has an inhibiting influence we adjust the value accordingly
                if input in function.inhibitors:
                    inputs_activity.append(-bm.activity_values(input)[e])
                else:
                    inputs_activity.append(bm.activity_values(input)[e])

            # Create all possible subsets of activity value of inputs
            for i in range(1, len(function.inputs)+1):
                sets = set(itertools.combinations(inputs_activity, i))
                # Create tseytin_encoding variable if |subset| > 1
                tsey_subsets = []
                for subset in sets:
                    # only add tsey vars if more than 1 subset
                    tsey_var = add_and_tseytin(s, subset) if len(subset) > 1 else subset[0]
                    tsey_subsets.append(tsey_var)
                subset_or = add_or_tseytin(s, tsey_subsets) if len(tsey_subsets) > 1 else tsey_subsets[0]

                #s.add_clause([z[0]])
                # TODO add t = 1 min, excluding t = 0
                #s.add_clause([z[1]])
                # Add clause SKILP (1)
                if i < len(z) - 1:
                    s.add_clause([a, -subset_or, z[i+1]])
                else:
                    s.add_clause([a, -subset_or, -z[i]])

                #  Add clause SKILP (2)
                s.add_clause([-a, -z[i], subset_or])
                # Add if threshold is i+1, then it is also i: if z[i+1] then z[i]
        # TODO check indentation, moved this out of i in range loop to here, seems to work
            for i in range(len(z)-1):
                s.add_clause([-z[i+1], z[i]])
            # If only threshold 0 (so if not threshold 1), value of func is alwyas 1
            s.add_clause([z[1], a])
            #s.add_clause([~z[0], z[1], a])

def init_z(s, bm, zero_inclusive):
    for function in bm.functions:
        z = [s.add_lit()]
        for input in function.inputs:
            z.append(s.add_lit())
        # If zero_inclusive threshold 1 can be 0, otherwise, threshold 1 is set to 1
        if not zero_inclusive: s.add_clause([z[0]])
        function.z = z
        # Set the known gates (i.e., the AND gates (having + in their names))
        # Known AND gate, set last value to true, others to false
        if "+" in function.name:
            for size in range(len(z)):
                s.add_clause([z[size]])

def init_activity_levels(s, bm, nodes):
    #TODO: add not if signed
    for node in nodes:
        a = ActivityLevels(node.name)
        for e in range(bm.nr_of_experiments):
            x = s.add_lit()
            a.add_level(x)
        bm.add_activity_levels(a)

        #Add the !nodes to the activity levels if the node is negated or a composite node contains negated nodes
        #if "!" in node.name:
        #    print("wodan?")
        #    neg = node.name.split("+")
        #    for neg_node in neg:
        #        if neg_node.startswith("!"):
        #            not_a = ActivityLevels(neg_node)
        #            for e in range(bm.nr_of_experiments):
        #                y = s.add_lit()
        #                s.add_clause([bm.activity(neg_node[1:]).values[e], y])
        #                s.add_clause([-bm.activity(neg_node[1:]).values[e], -y])
        #                not_a.add_level(y)
        #            bm.add_activity_levels(not_a)

#def set_stimuli(s, bm, gn):
#    for i in range(len(gn.treatments)):
#        for stimulus in gn.treatments[i].stimuli:
#            a = bm.activity_values(stimulus.name)[i]
#            if stimulus.value == 0:
#                s.add_clause([-a])
#            else:
#                s.add_clause([a])
#def set_stimuli(s, bm, gn):
#    for i in range(len(gn.treatments)):
#        for stimulus in gn.treatments[i].stimuli:
#            if bm.activity_values(stimulus.name) != None:
#                a = bm.activity_values(stimulus.name)[i]
#                # handle inhibitors
#                if stimulus.name in gn.setup["inhibitors"]:
#                    if stimulus.value == 1:
#                        s.add_clause([-a])
#                # handle stimuli
#                else:
#                    if stimulus.value == 0:
#                        s.add_clause([-a])
#                    else:
#                        s.add_clause([a])
#
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
                if stimulus.value == 0:
                    s.add_clause([-a])

def init_model(s, bm, nodes, zero_inclusive):
    init_z(s, bm, zero_inclusive)
    init_activity_levels(s, bm, nodes)

def init_threshold_model_sat(s, bm ,gn):
    print("Initializing model...")
    # Dummy var to turn zero inclusive feature off: threshold 1 is always 1
    #zero_inclusive = False
    zero_inclusive = True
    init_model(s, bm, gn.metabolites, zero_inclusive)
    set_stimuli(s, bm, gn)
    add_clauses(s, bm)

