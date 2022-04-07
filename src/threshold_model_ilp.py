from gurobipy import GRB
from boolean_model import *

def init_z(m, bm):
    for function in bm.functions:
        function.set_threshold(m.addVar(vtype=GRB.INTEGER, name=function.name+"_z_"))
    m.update()


def init_activity_levels(m, bm):
    for node in bm.nodes:
        a = ActivityLevels(node.name)
        for e in range(bm.nr_of_experiments):
            x = m.addVar(vtype=GRB.INTEGER, name = "act_" + a.name + "_" + str(e))
           # m.addConstr(x <= 1)
           # m.addConstr(x >= 0)
            a.add_level(x)
        bm.add_activity_levels(a)

def init_model(m, bm):
    init_z(m, bm)
    init_activity_levels(m, bm)

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
#
# adjust activity level for inhibiting edge
def get_a(m, bm, function, input):
    if function.is_inhibitor(input):
    #if function.inputs[input] in function.inhibitors:
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

def add_constraints(m, bm, gn):
    #print("adding contraints...")
    for function in bm.functions:
        function_inputs = []
        #for input in function.inputs:
        for input in range(len(function.inputs)):
            function_inputs.append(get_a(m, bm, function, input))
            #function_inputs.append(get_a(m, bm, function, function.get_input_index(input)))
        for e in range(bm.nr_of_experiments):
            if not gn.stimulus_on(function.name, e):
                a = bm.activity(function.name).values
               # m.addConstr(a[e] >= (sum(function_inputs[input][e] for input in range(len(function.inputs))) - function.threshold + 1)/(len(function.get_unique_inputs())+1))
               # m.addConstr(a[e] <= (sum(function_inputs[input][e] for input in range(len(function.inputs))) - function.threshold)/(len(function.get_unique_inputs())+1)+1)
                m.addConstr(a[e] >= (sum(function_inputs[input][e] for input in range(len(function.inputs))) - function.threshold + 1)/(len(function.inputs)+1))
                m.addConstr(a[e] <= (sum(function_inputs[input][e] for input in range(len(function.inputs))) - function.threshold)/(len(function.inputs)+1)+1)
                # Add min and max values for z
                # TODO: for now these are hardcoded, n+1 and 0 also have their benefits (see sharan/karp), maybe change this to variables
        #m.addConstr(function.threshold <= len(function.get_unique_inputs()) + 1)
        #m.addConstr(function.threshold <= len(function.get_unique_inputs())+1)
        m.addConstr(function.threshold <= len(function.inputs) )
        m.addConstr(function.threshold >= 1)

    m.update()

def init_threshold_model_ilp(m, bm, gn):
    #print("Initializing model...")
    init_model(m, bm)
    set_stimuli(m, bm, gn)
    set_non_input_nodes(m, bm, gn)
    add_constraints(m, bm, gn)

