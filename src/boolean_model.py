from math import comb
import itertools

class BooleanModel:
    def __init__(self, nr_of_experiments):
        self.functions = []
        self.a = []
        self.a_inh = []
        self.nr_of_experiments = nr_of_experiments
        self.total_models = 0
        self.nodes = []
        self.stimuli = []

    def concat_doubles(self):
        for function in self.functions:
            function.concat_doubles()

    def update_stimuli_target(self, stimuli, function, old, new):
        for stim in stimuli:
            if stim.name == function:
                stim.update_target(old, new)

    #def update_function_input(self, function, old, new, sign):
    #    for f in self.functions:
    #        if f.name == function:
    #            f.update_input(old, new, sign)
    #            break

    def update_function_input(self, function, old, new):
        for f in self.functions:
            if f.name == function:
                f.update_input(self.get_function(old), self.get_function(new))
                break

    def update_function_target(self, function, old, new):
        for f in self.functions:
            if f.name == function:
                f.update_target(old, new)
                break

    def remove_function(self, function):
        for f in self.functions:
            if f.name == function.name:
                for input in f.inputs:
                    self.get_function(input).remove_target(f.name)
                for target in f.targets:
                    self.get_function(target).remove_input(f.name)
                self.functions.remove(f)
                for node in self.nodes:
                    if node.name == function.name:
                        self.nodes.remove(node)
                        break
                break
        for s in self.stimuli:
            if s.name == function.name:
                for target in s.targets:
                    self.get_function(target).remove_input(f.name)
                self.stimuli.remove(s)
                for node in self.nodes:
                    if node.name == function.name:
                        self.nodes.remove(node)
                        break

    def set_function_inhibitors(self, function, inhibitors):
        print("set fuction inhibitors")
        for f in self.functions:
            if function == f.name:
                f.add_inhibitors(inhibitors)

    def set_function_stimuli(self, function, stimuli):
        for f in self.functions:
            if function == f.name:
                f.add_stimuli(stimuli)

    def add_function(self, function):
        self.functions.append(function)
        #self.functions.sort()
        self.functions.sort(key=lambda x:x.name)

    def add_stimulus(self, function):
        self.stimuli.append(function)
        #self.functions.sort()
        self.stimuli.sort(key=lambda x:x.name)

    def has_function(self, name):
        for function in self.functions:
            if function.name == name:
                return True
        return False

    def has_stimulus(self, name):
        for stim in self.stimuli:
            if stim.name == name:
                return True
        return False

    def get_function(self, name):
        for function in self.functions:
            if function.name == name:
                return function
        for stim in self.stimuli:
            if stim.name == name:
                return stim
        return None

    def add_activity_levels(self, activity_levels):
        self.a.append(activity_levels)

    def add_inh_activity(self, activity):
        self.a_inh.append(activity)

    def get_inh_activity(self, name):
        for a in self.a_inh:
            if name == a.name:
                return a.values
        return None

    def has_inh_activity(self, name):
        for a in self.a_inh:
            if name == a.name:
                return True
        return False

    def add_local_tables(self, name, table):
        for function in self.functions:
            if function.name == name:
                for t in table:
                    function.add_local_table(t)
                break

    def add_global_table(self, name, table):
        for function in self.functions:
            if function.name == name:
                function.add_global_table(table)
                break

    def add_known_flags(self, name, table):
        for function in self.functions:
            if function.name == name:
                function.add_known_flag(table)
                break

    def activity(self, name):
        for level in self.a:
            if level.name == name:
                return level

    def activity_values(self, name):
        for level in self.a:
            if level.name == name:
                return level.values

    def unknown_gates(self):
        unknown_gates = 0
        for function in self.functions:
            if "+" not in function.name:
                unknown_gates += 1
        return unknown_gates

    def add_e_ax(self, name, e_ax):
        for function in self.functions:
            if function.name == name:
                function.e_ax = e_ax

    def add_e_aby(self, name, e_aby):
        for function in self.functions:
            if function.name == name:
                function.e_aby = e_aby
class Function:
    #def __init__(self, name, inputs):
    def __init__(self, name, inputs, inhibitors):
        self.name = name
        self.inputs = sorted(inputs, key=str.lower)
        self.targets = []
        self.inhibitors = sorted(inhibitors, key=str.lower)
        self.stimuli = []
        # truth table global
        self.x = []
        # truth table known gate flag
        self.x_flags = []
        # truth table local, 2dnf single
        self.y = []
        # threshold sat , 2dnf and
        self.z = []
        # threhold ilp
        self.threshold = None
        # for each exp, for each row, for each input: (act == b_val)
        self.selector = []
        self.experimental_row_ands = []
        # pairs of ax for dnf per experiment
        self.e_ax = []
        # pairs of aby for dnf per experiment
        self.e_aby = []
        self.double = []
        self.pair_names = []

    def create_pair_names(self):
        #pairs = list(set(self.inputs))
        pairs = self.get_unique_inputs()
        for name in self.double:
            pairs.append("!" + name)
        self.pair_names = list(itertools.combinations(pairs, 2))
        for pair in self.pair_names:
            if pair[0][1:] == pair[1] or pair[0] == pair[1][1:]:
                self.pair_names.remove(pair)

    def get_unique_inputs(self):
        if not self.double:
            return self.inputs
        else:
            return self.inputs[:(len(self.inputs) - len(self.double))]

    def get_input_index(self, name):
        if name not in self.double and name[1:] not in self.double:
            return self.inputs.index(name)
        else:
            if name[0] == "!":
                return len(self.inputs) - 1 - self.inputs[::-1].index(name[1:])
            else:
                return self.inputs.index(name)

    def add_target(self, target):
        if target not in self.targets:
            self.targets.append(target)
            self.targets.sort()

    def remove_target(self, target):
        if target in self.targets:
            self.targets.remove(target)

    def update_target(self, old, new):
        if old in self.targets:
            self.targets.remove(old)
        self.targets.append(new)

    def update_input(self, old, new):
        #if old.name in self.inputs:
        #    self.inputs.remove(old.name)
        #if new != None and new.name not in self.inputs:
        if new != None:
            if new.name in old.inhibitors:
                if old.name in self.inhibitors:
                    self.add_input(new.name)
                    #self.inputs.append(new.name)
                    #self.inhibitors.remove(old.name)
                else:
                    #self.inhibitors.append(new.name)
                    self.add_inhibitor(new.name)
            else: # new activiating in old
                if old.name in self.inhibitors:
                    #self.inhibitors.append(new.name)
                    self.add_inhibitor(new.name)
                else:
                    self.add_input(new.name)
                    #self.inputs.append(new.name)
        self.remove_input(old.name)


    def add_inhibitors(self, inhibitors):
        print("add inhibitors")
        for inhibitor in inhibitors:
            self.add_inhibitor(inhibitor)

    def add_stimuli(self, stimuli):
        for stimulus in stimuli:
            self.add_stimulus(stimulus)

    def add_inhibitor(self, name):
        if name in self.inputs and name not in self.inhibitors:
            self.inhibitors.append(name)
            self.double.append(name)
        else:
            if name not in self.inputs and name not in self.inhibitors:
                self.inhibitors.append(name)
                self.inputs.append(name)

    def add_input(self, name):
        if name not in self.inputs and name not in self.inhibitors:
            self.inputs.append(name)
        else:
            if name in self.inhibitors and name in self.inputs:
                self.double.append(name)

    def remove_input(self, name):
        if name in self.inputs:
            self.inputs.remove(name)
        if name in self.inhibitors:
            self.inhibitors.remove(name)
        if name in self.double:
            self.double.remove(name)

    def add_stimulus(self, name):
        if name in self.inputs:
            self.stimuli.append(name)

    def is_inhibitor(self, index):
        name = self.inputs[index]
        if name not in self.inhibitors:
            return False
        if name not in self.double and name in self.inhibitors:
            return True
        if name in self.double:
            for i in range(index):
                if self.inputs[i] == name:
                    return True
                else:
                    return False

    def add_local_table(self, t):
        self.y.append(t)

    def add_global_table(self, t):
        self.x = t

    def add_known_flag(self, t):
        self.x_flags = t

    def tablesize(self):
        if len(list(set(self.inputs))) == 1:
            return 2
        return pow(2, len(list(set(self.inputs))))

    def add_threshold_function(self, z):
        self.z = z

    def set_threshold(self, threshold):
        self.threshold = threshold

    def concat_doubles(self):
        self.inputs = self.inputs + self.double

class ActivityLevels:
    def __init__(self, name):
        self.name = name
        self.values = []

    def add_level(self, value):
        self.values.append(value)
