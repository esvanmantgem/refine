import json
from genetic_network import *

ALLOWED_HEADINGS = ['ID', 'TR', 'DA', 'DV']

def print_gn(gn):
    print("Metabolites")
    for metabolite in gn.metabolites:
        print(metabolite.name, metabolite.value)
    for reaction in gn.reactions:
        print(reaction.upstream, reaction.downstream)

def check_heading_validity(heading):
    for head in heading:
        if len(head) < 2:
            print("Heading", head, "missing information, exiting")
            exit(0)
        if len(head) > 3:
            print("Heading", head, "contains too many fields, exiting")
            exit(0)
        if head[0] not in ALLOWED_HEADINGS:
            print("Heading type", head[0], "not allowed, exiting")
            exit(0)

# Find the first occurrence of a "DA" field in the heading and return the index
def find(heading, field):
    for i, head in enumerate(heading):
        try:
            head.index(field)
            break
        except ValueError:
            continue
    return i

def read_midas_experiments(file, gn):
    split_heading = file.readline().strip().split(",")
    heading = [y.split(":") for y in split_heading]
    # remove first column from heading with name of dataset
    heading = heading[1:]
    check_heading_validity(heading)

    da_index = find(heading, 'DA')
    dv_index = find(heading, 'DV')

    experiments = []
    for line in file.readlines():
        experiment = line.strip().split(",")
        # remove first column from experiment, standard 1 from dataset name
        experiments.append(experiment[1:])
    half_index = int(len(experiments)/2)
    for exp in range(half_index):
        exp_indexes = []
        # Check if file is nicely structured to prevent having to loop
        if experiments[exp][:da_index] == experiments[half_index+exp][:da_index]:
            exp_indexes = [exp, half_index+exp]
        else:
            # it's not, so find the readouts by hand
            for readout_index in range(half_index, len(experiments)):
                if experiments[exp][:da_index] == experiments[readout_index][:da_index]:
                    exp_indexes = [exp, readout_index]

        # maak complete treatment en add to gn
        stimuli = experiments[exp_indexes[0]]
        readouts = experiments[exp_indexes[1]]
        treatment = Treatment()
        for metabolite in range(da_index):
            # if value expresses if inhibitor is present
            #if heading[metabolite][1].endswith("i") and stimuli[metabolite] == "1":
            #    treatment.add_stimulus(Metabolite(heading[metabolite][1][:-1], 0))
            #elif heading[metabolite][1].endswith("i") and stimuli[metabolite] == "0":
            #    # inhibitor not present, value is 1 (TODO check)
            #    treatment.add_stimulus(Metabolite(heading[metabolite][1][:-1], 1))
            # stimuli not set
            #elif stimuli[metabolite] == "0":
            #    treatment.add_stimulus(Metabolite(heading[metabolite][1], 0))
            #else:
            #    treatment.add_stimulus(Metabolite(heading[metabolite][1], 1))
            if stimuli[metabolite] == "0":
                if heading[metabolite][1].endswith("i"):
                    treatment.add_stimulus(Metabolite(heading[metabolite][1][:-1], 0))
                else:
                    treatment.add_stimulus(Metabolite(heading[metabolite][1], 0))
            else:
                if heading[metabolite][1].endswith("i"):
                    #TODO is inhibitor
                    treatment.add_stimulus(Metabolite(heading[metabolite][1][:-1], 1))
                    treatment.add_inhibited(Metabolite(heading[metabolite][1][:-1], 1))
                else:
                    treatment.add_stimulus(Metabolite(heading[metabolite][1], 1))
        # readouts: assume that if the first DA > 0, then all DA on that line are > 0
        for metabolite in range(dv_index, len(heading)):
            # Set unknown values to -1
            #if readouts[metabolite] == "NaN":
            if readouts[metabolite] != "NaN":
                #value = -1
            #else:
                # TODO hardocde threshold to 0.5 + no check on if value is actual float
                value = 0 if float(readouts[metabolite]) < 0.5 else 1
            treatment.add_readout(Metabolite(heading[metabolite][1], value))
        gn.add_treatment(treatment)

    #for stim in gn.treatments[0].stimuli:
    #    print(stim.name, stim.value)

def read_sif_reactions(file, gn):
    for line in file.readlines():
        #reaction = file.readline().strip().split()
        reaction = line.strip().split()
        inhibiting = True if reaction[1] == "-1" else False
        gn.add_reaction(Reaction(reaction[0], reaction[2], False, inhibiting))
        if not gn.has_metabolite(reaction[0]):
            gn.add_metabolite(Metabolite(reaction[0], -1))
        if not gn.has_metabolite(reaction[2]):
            gn.add_metabolite(Metabolite(reaction[2], -1))
    gn.set_nr_of_reactions()

def read_jason_setup(file, gn):
        setup = file.read()
        gn.setup = json.loads(setup)

# TODO rewrite the entire thing: make clean input handling, setting uop: start with jason etc
def read_midassif(f_metabolites, f_reactions, f_setup, gn):
    read_midas_experiments(open(f_metabolites), gn)
    read_jason_setup(open(f_setup), gn)
    read_sif_reactions(open(f_reactions), gn)
    #print_gn(gn)
    return gn

