from boolean_model import *
from genetic_network import *

def set_targets(bm, setup):
    # set the targets for each function in the model
    for input in bm.functions:
        for function in bm.functions:
            if input.name != function.name:
                if input.name in function.inputs:
                    input.add_target(function.name)
    # set the targets of the stimuli in stimuli_targets
    for input in setup["stimuli"]:
        #if not bm.has_function(input) and not bm.has_stimulus(input):
        for function in bm.functions:
            if not bm.has_function(input) and not bm.has_stimulus(input):
                if input != function.name:
                    if input in function.inputs:
                        stim_function = Function(input, [], [])
                        stim_function.add_target(function.name)
                        bm.add_stimulus(stim_function)

def removal_allowed(name, setup):
    if name in setup["stimuli"]:
        return False
    if name in setup["inhibitors"]:
        return False
    if name in setup["readouts"]:
        return False
    return True


def update_stimuli_target(stimuli, function, old, new):
    for stim in stimuli:
        if stim.name == function:
            stim.update_target(old, new)

def update_target(bm, stimuli, function, old, new):
    if not bm.has_function(function):
        update_stimuli_target(stimuli, function, old, new)
    else:
        bm.update_function_target(function, old, new)

def rule_seq(bm, setup):
    u_flag = False
    updated = True
    while updated:
        updated = False
        for function in bm.functions:
            if len(function.inputs) == 1 and len(function.targets) == 1:
                # update the input
                if removal_allowed(function.name, setup):
                    # prevent self loop creation
                    if function.targets[0] not in function.inputs:
                        updated = True
                        u_flag = True
                        bm.update_function_input(function.targets[0], function.name, function.inputs[0])
                        #update_input(bm, stimuli, function.targets[0], function.name, function.inputs[0])
                        update_target(bm, bm.stimuli, function.inputs[0], function.name, function.targets[0])
                        bm.remove_function(function)
    return u_flag

def rule_fan_out(bm, setup):
    u_flag = False
    updated = True
    while updated:
        updated = False
        for function in bm.functions:
            if len(function.inputs) == 1 and len(function.targets) > 1:
                if removal_allowed(function.name, setup):
                    for i in range(len(function.targets)):
                        # prevent self loop creation
                        if function.targets[i] not in function.inputs:
                            updated = True
                            u_flag = True
                            #update_input(bm, stimuli, function.targets[i], function.name, function.inputs[0])
                            bm.update_function_input(function.targets[i], function.name, function.inputs[0])
                            update_target(bm, bm.stimuli, function.inputs[0], function.name, function.targets[i])
                    bm.remove_function(function)
    return u_flag

def rule_fan_in(bm, setup):
    flag = False
    updated = True
    while updated:
        updated = False
        for function in bm.functions:
            if len(function.inputs) > 1 and len(function.targets) == 1:
                if removal_allowed(function.name, setup):
                    # prevent self loop creation
                    if function.targets[0] not in function.inputs:
                        for i in range(len(function.inputs)):
                                updated = True
                                flag = True
                                bm.update_function_input(function.targets[0], function.name, function.inputs[i])
                                #update_input(bm, stimuli, function.targets[0], function.name, function.inputs[i])
                                update_target(bm, bm.stimuli, function.inputs[i], function.name, function.targets[0])
                        bm.remove_function(function)
    return flag


def remove_non_stimulus_root(bm, node, setup, u_flag):
    # according to caspo, removing stimuli leaves is allowed
    if not bm.has_function(node.name):
        if node.name not in setup["stimuli"]:
            for f in bm.functions:
                if node.name in f.inputs:
                    u_flag = True
                    f.remove_input(node.name)
            bm.nodes.remove(node)
    else:
        function = bm.get_function(node.name)
        if not function.inputs:
            if function.name not in setup["stimuli"]:
                for i in range(len(function.inputs)):
                    #bm.update_function_input(function.inputs[i], function.name, None)
                    remove_non_stimuli_root(bm, bm.get_function(function.targets[i]), setup, u_flag)
                u_flag = True
                bm.remove_function(function)
    return u_flag

def remove_non_stimuli_roots(bm, setup):
    u_flag = False
    s_flag = False
    for node in bm.nodes:
       s_flag = remove_non_stimulus_root(bm, node, setup, s_flag)
    #for function in bm.functions:
    #   u_flag = remove_non_stimulus_root(bm, function, setup, u_flag )
    return u_flag or s_flag

def remove_non_readout_leaf(bm, function, setup, u_flag):
    # according to caspo, removing stimuli leaves is allowed
    if not function.targets:
        if function.name not in setup["readouts"]:
            for i in range(len(function.inputs)):
                #bm.update_function_input(function.inputs[i], function.name, None)
                remove_non_readout_leaf(bm, bm.get_function(function.inputs[i]), setup, u_flag)
            u_flag = True
            bm.remove_function(function)
    return u_flag

def remove_non_readout_leaves(bm, setup):
    u_flag = False
    s_flag = False
    for function in bm.functions:
       u_flag = remove_non_readout_leaf(bm, function, setup, u_flag )
    for stim in bm.stimuli:
       s_flag = remove_non_readout_leaf(bm, stim, setup, s_flag)
    return u_flag or s_flag

def preprocess_model(bm, setup):
    set_targets(bm, setup)
    # 1.flag nodes that don't alter desginated nodes (nodes on terminal branhes with no readouts)
    # 2.flag nodes not influened by stimuli/inhibitors
    # 3.compress cascades
    u_flag = True
    while u_flag:
        u_flag = False
        #print("Removing leaves...")
        u_flag = remove_non_readout_leaves(bm, setup) or u_flag
        u_flag = remove_non_stimuli_roots(bm, setup) or u_flag
        #print("Removing limear sequences...")
        u_flag = rule_seq(bm, setup) or u_flag
        #print("Removing fan outs...")
        u_flag = rule_fan_out(bm, setup) or u_flag
        #print("Removing fan ins...")
        u_flag = rule_fan_in(bm, setup) or u_flag
    bm.concat_doubles()
