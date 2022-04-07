import gurobipy as gp
import time
from gurobipy import GRB
from threshold_model_ilp import *
from full_model_ilp import *
from dnf_model_ilp import *
from dnf_ilp_cas import *
from timer import *

def print_bm(model, bm, args, error_value):
    if not args.n:
        #if args.output != None:
        #    out = open(args.output, "w")
        #    for mod in range(model.SolCount):
        #        out.write("Solution" + str(mod+1) + "\n")
        #        model.setParam(GRB.Param.SolutionNumber, mod)
        #        out.write("Model:" + "\n")
        #        for node in bm.a:
        #            out.write("    Node:" + node.name + "\n")
        #            for e in range(bm.nr_of_experiments):
        #                out.write("        " + node.name +  str(e+1) + ":" + str(int(node.values[e].getAttr('Xn'))) + "\n")
        #        for function in bm.functions:
        #            out.write( "Function: " + function.name + "\n")
        #            out.write( "Inputs: " + ''.join(function.inputs) + "\n")
        #            out.write( "    Truthtable" + "\n")
        #            if args.s:
        #                out.write("        z:" + str(int(bm.z[function.name].getAttr('Xn'))) + "\n")
        #            else:
        #                for i in range(function.tablesize()):
        #                    out.write("        x" + i + ":" + int(function.x[i].getAttr('Xn')) + "\n")
        #        out.write("---------------------------------------------------------------")

        #    out.close()
        #else:
        print("")
        if args.a:
            #for function in bm.functions:
            #    print(function.name,  ": ", end=' ')
            #    inputs = function.get_unique_inputs()
            #    for input in inputs:
            #        print(input, end=' ')
            #    print(", ", end=' ')
            #print("")
            for mod in range(model.SolCount):
                print("Solution", mod+1)
                model.setParam(GRB.Param.SolutionNumber, mod)
                print_model(model, bm, args)
                # For comparison
                #for function in bm.functions:
                    #print(function.name,  ": ", end=' ')
                    #inputs = function.get_unique_inputs()
                    #for input in inputs:
                    #    print(input, end=' ')
                    #print("")
                    #if args.t:
                    #    print(int(function.threshold.getAttr('Xn')), end=' ')
                #    elif args.d:
                #        #print( "    2DNF")
                #        for i in range(len(function.x)):
                #            print(int(function.x[i].getAttr('Xn')), end=' ')
                ##        for i in range(len(function.y)):
                ##            print(int(function.y[i].getAttr('Xn')), end=' ')
                #    else:
                #        print( "    Truthtable")
                #        for i in range(function.tablesize()):
                #            print("        x", i, ":", int(function.x[i].getAttr('Xn')))
                #        #print("Number of solutions found: ", model.SolCount)
            print("")
                    #end for comparison
        else:
            print_model(model, bm, args)
    #else:
    print("nr of nodes: ", len(bm.a))
    print("Solutions found: ", model.SolCount)
    print("Error value: ", error_value)
    print("Objective value: ", model.getObjective().getValue())

def print_model(model, bm, args):
    print("Model:")
    for node in bm.a:
        print("Node:")
        for e in range(bm.nr_of_experiments):
            print("    ", node.name+str(e+1)+":", int(node.values[e].getAttr('Xn')))
    for function in bm.functions:
        print( "Function: ", function.name)
        print( "Inputs: ", function.get_unique_inputs())
        if args.t:
            print("        Threshold:", int(function.threshold.getAttr('Xn')))
        elif args.d:
            print( "    2DNF")
            for i in range(len(function.x)):
                print("        x", i, ":", int(function.x[i].getAttr('Xn')))
            for i in range(len(function.y)):
                print("        y", i, ":", int(function.y[i].getAttr('Xn')))
        else:
            print( "    Truthtable")
            for i in range(function.tablesize()):
                print("        x", i, ":", int(function.x[i].getAttr('Xn')))

    #for v in model.getVars():
    #    print('%s %g', (v.varName, v.x))
    print("---------------------------------------------------------------")

def optimize(m, args):
    m.update()
    if args.p != None:
        print("------------ optimizing with .p ------------ ")
        m.setParam(GRB.Param.PoolSolutions, args.p)
        m.setParam(GRB.Param.PoolGap, 0)
        m.setParam(GRB.Param.PoolSearchMode, 2)
        m.setParam(GRB.Param.OutputFlag, 0)
    if args.a:
        print("------------ optimizing with .a ------------ ")
        #m.setParam(GRB.Param.Presolve, -1)
        m.setParam(GRB.Param.MIPFocus, 3)
        m.setParam(GRB.Param.Cuts, 2)
        #m.write("second.lp")
        m.setParam(GRB.Param.PoolSolutions, 100000)
        m.setParam(GRB.Param.PoolGap, 0)
        m.setParam(GRB.Param.PoolSearchMode, 2)
        m.setParam(GRB.Param.OutputFlag, 0)
        #m.setParam(GRB.Param.MIPGapAbs, 0)
    m.update()
    m.optimize()

def set_objective(m, bm, gn, args):
    #print("Setting objective...")
    readouts = gn.get_readouts()

    m.ModelSense = GRB.MINIMIZE
    # optimize in one objective
    #m.setObjective(sum(sum(bm.activity(readout).values[e] + readouts[readout][e] - 2 * bm.activity(readout).values[e] * readouts[readout][e] for e in range(bm.nr_of_experiments)) for readout in readouts) + 0.1 * sum(sum(f.x[i] for i in range(len(f.x))) + 2 * sum(f.y[j] for j in range(len(f.y))) for f in bm.functions))

    m.setParam(GRB.Param.Threads, 1)
    if args.d:
        m.setParam(GRB.Param.Presolve, 2)
        m.setParam(GRB.Param.MIPFocus, 3)
        m.setParam(GRB.Param.Cuts, 2)
    if args.t:
        m.setParam(GRB.Param.Heuristics, 0.001)
        m.setParam(GRB.Param.BranchDir, -1)

    if args.v:
        m.setParam(GRB.Param.OutputFlag, 0)
    # optimize in two runs
    # optimize readouts
    readouts_clean = []
    for readout in readouts:
        if bm.activity(readout) == None:
            readouts_clean.append(readout)
    for readout in readouts_clean:
        readouts.pop(readout)

    m.setObjective(sum(sum(bm.activity(readout).values[e] + readouts[readout][e] - 2 * bm.activity(readout).values[e] * readouts[readout][e] for e in range(bm.nr_of_experiments)) for readout in readouts))
    #m.write("first.lp")
    m.optimize()
    m.addConstr(m.getObjective().getValue() == sum(sum(bm.activity(readout).values[e] + readouts[readout][e] - 2 * bm.activity(readout).values[e] * readouts[readout][e] for e in range(bm.nr_of_experiments)) for readout in readouts)) #m.setObjectiveN(sum(sum(bm.activity(readout).values[e] + readouts[readout][e] - 2 * bm.activity(readout).values[e] * readouts[readout][e] for e in range(bm.nr_of_experiments)) for readout in readouts), 0, 1)
    error_value = m.getObjective().getValue()
    # optimize model size for optimal readouts
    if not args.size:
        if args.d:
            m.setObjective(sum(sum(f.x[i] for i in range(len(f.x))) + 2 * sum(f.y[j] for j in range(len(f.y))) for f in bm.functions))
        else:
            if args.t:
                # We minimize the thresholds. First we need to put max thresholds to 0
                #quot = []
                #remain = []
                #for function in bm.functions:
                #    nr_thresholds = len(function.get_unique_inputs()) + 1
                #    #for threshold in range(1, nr_thresholds+1):
                #        # new-threshold = #inputs+1 * quotient + remainder ( == modulo, for remainder )
                #    u = m.addVar(vtype=GRB.INTEGER, name = "quotient_" + function.name)
                #    y = m.addVar(vtype=GRB.INTEGER, name = "remainder_" + function.name)
                #    m.addConstr(function.threshold == nr_thresholds * u + y)
                #    m.addConstr(0 <= y)
                #    m.addConstr(y <= nr_thresholds - 1)
                #    quot.append(u)
                #    remain.append(y)
                #m.setObjective(sum(i for i in remain))
                m.setObjective(sum(f.threshold for f in bm.functions))
            else:
                # truthtable
                #b_tables = create_b_sum(get_max(bm))

                #xb = []
                #for f in bm.functions:
                #    b = b_tables[len(f.get_unique_inputs())]
                #    xb.append(sum(f.x[i] * b[i] for i in range(len(f.x)) ))
                #m.setObjective(sum(xb[i] for i in range(len(xb))))
                m.setObjective(sum(sum(f.x[i] for i in range(len(f.x))) for f in bm.functions))
                #m.addConstr(sum(sum(f.x[i] for i in range(len(f.x))) for f in bm.functions) == 15)
        m.update()
    return error_value

def create_b_sum(max_size):
    b = []
    b.append([])
    b.append([0, 1])

    for size in range(2,max_size+1):
        size_b = []
        for row in range(pow(2, size)):
            bin_rep = "{0:b}".format(row)
            bin_rep = bin_rep.zfill(size)
            row_values = []
            for element in bin_rep:
                row_values.append(int(element))
            size_b.append(sum(row_values))
        b.append(size_b)
    return b

def get_max(bm):
    max_size = 0
    for function in bm.functions:
        if len(function.inputs) > max_size:
            max_size = len(function.inputs)
    return max_size

def setup_model(m, bm, gn, threshold, dnf):
    if threshold:
        init_threshold_model_ilp(m, bm, gn)
    elif dnf:
        init_2dnf_model_ilp(m, bm, gn)
    else:
        init_full_model_ilp(m, bm , gn)

def run_ilp(args, gn, bm):
    m = gp.Model("Refine: ILP")
    timer = Timer()
    timer.start_setup()
    setup_model(m, bm, gn, args.t, args.d)
    timer.start_solver()
    error_value = set_objective(m, bm, gn, args)
    optimize(m, args)
    timer.stop()
    # Query number of multiple objectives, and number of solutions
    #assert m.Status == GRB.Status.OPTIMAL
    #nSolutions  = m.SolCount
    #nObjectives = m.NumObj
    #print('Problem has', nObjectives, 'objectives')
    #print('Gurobi found', nSolutions, 'solutions')
    ## For each solution, print value of first three variables, and
    ## value for each objective function
    #solutions = []
    #for s in range(nSolutions):
    #  # Set which solution we will query from now on
    #  m.params.SolutionNumber = s
    #  # Print objective value of this solution in each objective
    #  print('Solution', s, ':', end='')
    #  for o in range(nObjectives):
    #    # Set which objective we will query
    #    m.params.ObjNumber = o
    #    # Query the o-th objective value
    #    print(' ',m.ObjNVal, end='')
    #for v in m.getVars():
    #    print(v, v.x)

    print_bm(m, bm, args, error_value)
    print("Time to solve: ", timer.solver_time())
    print("Total time: ", timer.setup_time())

    #m.write("out.lp")

