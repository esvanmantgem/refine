from pycryptosat import Solver
from sat_solver import *
from boolean_model import *
from full_model_sat import *
from threshold_model_sat import *
from dnf_model_sat import *
from multi_model_sat import *
from timer import *


def print_threshold_solution(solution, bm):
    for function in bm.functions:
        print( "Function: ", function.name)
        print( "    Inputs: ", function.inputs)
        threshold = -1
        for item in function.z:
            if solution[item]: threshold += 1
            #print("        z:", int(solution[item]))
        print("    Threshold:", threshold)

def print_2dnf_solution(solution, bm):
    for function in bm.functions:
        print( "Function: ", function.name)
        print( "    Inputs: ", function.inputs)
        print( "    2DNF")
        for i in range(len(function.x)):
            print("        x", i, ":", int(solution[function.x[i]]))
        for i in range(len(function.y)):
            print("        y", i, ":", int(solution[function.y[i]]))

def print_unknown_values_solution(solution, bm):
    for function in bm.functions:
        print( "Function: ", function.name)
        print( "    Inputs: ", function.inputs)
        for i in range(function.tablesize()):
            value = int(solution[function.x[i]]) if solution[function.x_flags[i]] else "0/1"
            print("        x", i, ":", value)

def print_table(solution, bm):
    for function in bm.functions:
        print( "Function: ", function.name)
        print( "    Inputs: ", function.inputs)
        for i in range(function.tablesize()):
            print("        x", i, ":", int(solution[function.x[i]]))

def print_solution_type(s, bm, args):
    solution = s.solution if s.sat else s.last_solution
    print("Model is SAT: ")
    for node in bm.a:
        for e in range(bm.nr_of_experiments):
            print("    ", node.name+str(e+1),":", int(solution[node.values[e]]), end="", flush=True)
        print("")
    if args.t:
        print_threshold_solution(solution, bm)
    elif args.d:
        print_2dnf_solution(solution, bm)
    elif args.m:
        print_unknown_values_solution(solution, bm)
    else:
        print_table(solution, bm)
    print("---------------------------------------------------------------")

def print_bm(s, bm, args):
    if not args.n:
        if not args.a and not s.sat:
            print("Model is UNSAT")
        else:
            print_solution_type(s, bm, args)

# Calculte: 2^(xflag(false)) rows for each function. Then function * total
def get_total_models(s, bm):
    if s.sat:
        solution = s.solution
        for function in bm.functions:
            # needs to start at 1 for 2 times multiplier. If this is not the case, will be set back to 0
            untargeted_rows = 0
            for flag in function.x_flags:
                if not solution[flag]:
                    untargeted_rows += 1
            current_models = 2 ** untargeted_rows
            bm.total_models = bm.total_models * current_models if bm.total_models > 0 else current_models
    else:
        bm.total_models = 0
    return bm.total_models

def print_solution(s, bm, args, time, nr_of_solutions):
    # Print single found model
    if not args.a: print_bm(s, bm, args)
    print("Number of solutions found: ", nr_of_solutions)
    print("Target found (max):", s.target_found, "("+str(s.max_target)+")", ", Objective value:", s.max_target - s.target_found)
    print("Time to solve: ", time.solver_time())
    if args.m and args.a: print("Total models found:", bm.total_models)
    if args.m and not args.a: print("Total models found:", get_total_models(s, bm))
    print("Total time: ", time.setup_time())

# Set g to indicate whether the  activity level per experiment is equal to the readout of that experiment so we can maximize g.
def set_objectives(s, bm, gn):
    print("Initializing optimization...")
    readouts = gn.get_readouts()
    g = []
    for readout in readouts:
        cur_a = bm.activity_values(readout)
        for e in range(len(cur_a)):
            r = s.add_lit()
            cur_q = s.add_lit()
            g.append(cur_q)

            if readouts[readout][e] == 1:
                s.add_clause([r])
            else:
                s.add_clause([-r])
            s.add_clause([-cur_a[e], r, -cur_q]);
            s.add_clause([-cur_a[e], -r, cur_q]);
            s.add_clause([cur_a[e], -r, -cur_q]);
            s.add_clause([cur_a[e], r, cur_q]);
    return g

# Ban all solutions inclusive the ones note targeted by any experemint (i.e., xflag == false -> 0/
# 1 both possible)
# Calculte: 2^(xflag(false)) rows for each function. Then function * total
def ban_selected_solutions(s, bm, model_only):
    ban = []

    for function in bm.functions:
        untargeted_rows = 0
        for row in range(function.tablesize()):
            if s.is_true(function.x_flags[row]):
                ban.append(-function.x_flags[row])
                if s.is_true(function.x[row]):
                    ban.append(-function.x[row])
                else:
                    ban.append(function.x[row])
            else:
                untargeted_rows += 1
                ban.append(function.x_flags[row])
            current_models = 2 ** untargeted_rows
        bm.total_models = bm.total_models * current_models if bm.total_models > 0 else current_models
        # TODO check if inputs should be part of ban
        if not model_only:
            for input in function.inputs:
                a = bm.activity_values(input)
                for level in a:
                    if s.is_true(level):
                        ban.append(-level)
                    else:
                        ban.append(level)
    s.add_clause(ban)

def ban_threshold_solution(s, bm, model_only):
    ban = []
    for function in bm.functions:
        for z in function.z:
            if s.is_true(z):
                ban.append(-z)
            else:
                ban.append(z)
    # TODO check if inputs should be part of ban
        if not model_only:
            for input in function.inputs:
                a = bm.activity_values(input)
                for level in a:
                    if s.is_true(level):
                        ban.append(-level)
                    else:
                        ban.append(level)
    s.add_clause(ban)

def ban_2dnf_solution(s, bm, model_only):
    ban = []
    for function in bm.functions:
        for y in function.y:
            if s.is_true(y):
                ban.append(-y)
            else:
                ban.append(y)
        for x in function.x:
            if s.is_true(x):
                ban.append(-x)
            else:
                ban.append(x)
    # TODO check if inputs should be part of ban
        if not model_only:
            for input in function.inputs:
                a = bm.activity_values(input)
                for level in a:
                    if s.is_true(level):
                        ban.append(-level)
                    else:
                        ban.append(level)
    s.add_clause(ban)

def ban_table_solution(s, bm, model_only):
    ban = []
    for function in bm.functions:
        for row in function.x:
            if s.is_true(row):
                ban.append(-row)
            else:
                ban.append(row)
        # TODO check if inputs should be part of ban
        if not model_only:
            for input in function.inputs:
                a = bm.activity_values(input)
                for level in a:
                    if s.is_true(level):
                        ban.append(-level)
                    else:
                        ban.append(level)
    s.add_clause(ban)

def ban_solution(s, bm, args):
    # Ban solutions for unknown values
    if args.m:
        ban_selected_solutions(s, bm, args.b)
    # Ban solution for threshold model
    elif args.t:
        ban_threshold_solution(s, bm, args.b)
    # Ban solution for 2DNF model
    elif args.d:
        ban_2dnf_solution(s, bm, args.b)
    # Ban solution for truth table model
    else:
        ban_table_solution(s, bm, args.b)

def find_all_solutions(s, bm, g, args):
    nr_of_solutions = 0
    # Find the max possible target
    max_target_found = s.optimize(args.l)
    if max_target_found < 1:
        print("Model is UNSAT")
    else:
        nr_of_solutions += 1
        print_bm(s, bm, args)
        ban_solution(s, bm, args)
        # Find all solutions with max target
        while(True):
            #if nr_of_solutions % 100 == 0:
            #    print("Solution found: ", nr_of_solutions)
            s.solve_with_assumptions(max_target_found)
            if not s.sat:
                break
            nr_of_solutions += 1
            if nr_of_solutions % 100 == 0:
                print("solutions found: ", nr_of_solutions)
            # Only print if output wanted
            if not args.n: print_bm(s, bm, args)
            # Quit if the number of models required is reached
            if args.p != None and nr_of_solutions >= args.p:
                break
            ban_solution(s, bm, args)
    return nr_of_solutions

def run_optimization(s, bm, gn, args):
    g = set_objectives(s, bm, gn)
    s.init_optimization(g)
    # if max number of models set or we find all solutions
    if args.a or args.p != None:
        return find_all_solutions(s, bm, g, args)
    else:
        # no experiments given
        if g == []:
            s.optimize(0)
        else:
            s.optimize(args.l)
        return 1

def setup_model(s, bm, gn, args):
    if args.m:
        init_multi_model(s, bm , gn)
    elif args.t:
        init_threshold_model_sat(s, bm, gn)
    elif args.d:
        init_2dnf_model_sat(s, bm, gn)
    else:
        init_full_model_sat(s, bm , gn)

def run_sat(args, gn, bm):
    s = SatSolver()
    time = Timer()
    time.start_setup()
    setup_model(s, bm, gn, args)
    time.start_solver()
    nr_of_solutions = run_optimization(s, bm, gn, args)
    time.stop()
    print_solution(s, bm, args, time, nr_of_solutions)
