class GeneticNetwork:
    def __init__(self):
        self.metabolites = []
        self.reactions = []
        self.treatments = []
        self.nr_of_reactions = 0
        self.nr_of_metabolites = 0
        self.setup = {}

    def add_treatment(self, treatment):
        self.treatments.append(treatment)

    def add_metabolite(self, metabolite):
        self.metabolites.append(metabolite)

    def add_reaction(self, reaction):
        self.reactions.append(reaction)

    def get_readouts(self):
        readouts = {}
        for treatment in self.treatments:
            for readout in treatment.readouts:
                if readout.name not in readouts:
                    readouts[readout.name] = [readout.value]
                else:
                    readouts[readout.name].append(readout.value)
        return readouts

    def has_metabolite(self, name):
        for metabolite in self.metabolites:
            if name == metabolite.name:
                return True
        return False

    def set_nr_of_reactions(self):
        self.nr_of_reactions = len(self.reactions)

    def set_nr_of_metabolites(self):
        self.nr_of_metabolites = len(self.metabolites)

    # check if a stimulus (inhibitor) is set on (off)
    #def stimulus_on(self, stimulus, treatment):
    #    for metabolite in self.treatments[treatment].stimuli:
    #        if metabolite.name == stimulus:
    #            #if metabolite not in self.treatments[treatment].inhibited:
    #            if metabolite.value == 1:
    #                return True
    #            else:
    #                return False
    #    return False

    def stimulus_on(self, stimulus, treatment):
        for metabolite in self.treatments[treatment].stimuli:
            if metabolite.name == stimulus:
                #if metabolite not in self.treatments[treatment].inhibited:
                if metabolite.value == 1:
                    return True
                else:
                    return False
        return False

class Metabolite:
    def __init__(self, name, value):
        self.name = name
        self.value = value

class Reaction:
    def __init__(self, upstream, downstream, known_and=False, inhibiting=False):
        self.downstream =  downstream
        self.upstream = upstream
        self.known_and = known_and
        self.inhibiting = inhibiting

    def add_upstream_species(self, species):
        self.upstream.append(species)

    def is_stimulus(self):
        return not self.upstream

    def is_readout(self):
        return self.downstream == ""

class Treatment:
    def __init__(self):
        self.readouts = []
        self.stimuli = []
        self.inhibited = []

    def add_stimulus(self, metabolite):
        self.stimuli.append(metabolite)

    def add_inhibited(self, metabolite):
        self.inhibited.append(metabolite)

    def update_readout(self, metabolite):
        if metabolite.name not in self.readouts:
            self.add_readout(metabolite)
        else:
            for readout in self.readouts:
                if readout.name == metabolite.name:
                    readout.value = metabolite.value

    def add_readout(self, metabolite):
        self.readouts.append(metabolite)

    def get_readout(self, name):
        for readout in self.readouts:
            if name == readout.name:
                return readout.value
            else:
                # Error
                print("Error: ", name, "not found in readouts")
                exit(1)

    def ligand_used(self, name):
        for stimulus in self.stimuli:
            if stimulus.name == name:
                stimulus.value = 1
                break

    def inhibitor_used(self, name):
        for stimulus in self.stimuli:
            if stimulus.name == name:
                stimulus.value = 0
                break

#    # provides equality based on the stimuli name+value pairs
#    def __eq__(self, other):
#        for (stimulus, other_stim) in zip(self.stimuli, other):
#            if stimulus.name != other_stim.name: return False
#            if stimulus.value != other_stim.value: return False
#        return True
