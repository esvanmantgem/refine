from pycryptosat import Solver

class SatSolver:
    def __init__(self):
        self.solver = Solver()
        self.lits = [0]
        self.nr_of_lits = 0
        self.sat = None
        self.solution = None
        self.last_solution = None
        self.t = None
        self.max_target = 0
        self.target_found = 0

    # Create a new literal
    def add_lit(self):
        self.nr_of_lits += 1
        self.lits.append(self.nr_of_lits)
        return self.nr_of_lits

    # Add a clause
    def add_clause(self, clause):
        self.solver.add_clause(clause)

    # Solve the current CNF
    def solve(self):
        (self.sat, self.solution) = self.solver.solve()
        return self.sat

    # Solve the current CNF with a target as assumption
    def solve_with_assumptions(self, target = 1):
        if target == None: target = 1
        #(self.sat, self.solution) = self.solver.solve([self.t[len(self.t)-1][1]])
        (self.sat, self.solution) = self.solver.solve([self.t[len(self.t)-1][target]])
        if self.sat: self.last_solution = self.solution
        return self.sat

    # Maximizing ptimization function
    def optimize(self, target):
        # if l = none set initial target to 1 else target is value of l
        if target == None: target = 1
        while(True):
            # If SAT, increase target or stop if max reached
            if self.solve_with_assumptions(target):
                print("Target: ", target, "is sat")
                if target >= self.max_target:
                    break
                target += 1
            # Target is unsat, recover last solution found with previous target
            else:
                print("Target", target, "is unsat")
                target -= 1
                # Set solution to last found solution
                if target >=1:
                    self.solution = self.last_solution
                    self.sat = True
                break
        self.target_found = target
        return self.target_found

    def init_optimization(self, g):
        self.max_target = len(g)
        self.init_t(len(g)+1)
        self.add_optimization_clauses(g)

    # We examine the value of each q[i], with |q| = n.
    # For each s from 1 to n + 1 we create s vars T(s,d), where d runs from 0 to s-1.
    # So we have one var T(1,0) for s = 1 and for s = n we have n vars T(n, 0), ..., T(n, n-1)
    def init_t(self, m):
        # t = t[s][d] with s = set size, d = nr of vars true
        # s = s[d] with d = nr of vars true for s
        self.t = []
        for size in range(1, m+1):
            s = []
            for i in range(size):
                s.append(self.add_lit())
            self.t.append(s)

    def add_optimization_clauses(self, g):
        # Add sets with 0 true
        for opt_set in self.t:
            self.solver.add_clause([opt_set[0]])

        # Add if T(s, d) then T(s+1, d)
        for s in range(len(self.t) - 1):
            for d in range(len(self.t[s])):
                self.solver.add_clause([-self.t[s][d], self.t[s+1][d]]);

        # If T(s, d) and g(s), then T(s+1, d+1)
        for s in range(len(self.t)-1):
            for d in range(len(self.t[s])):
                self.solver.add_clause([self.t[s+1][d+1], -self.t[s][d], -g[s]]);

        # Prevent overshooting
        for s in range(1, len(self.t)):
            for d in range(1, len(self.t[s])):
                p = self.add_lit()
                # if statment has to do with the s-1 part. If s == d is a special case
                if s != d:
                    self.solver.add_clause([self.t[s-1][d], -self.t[s][d], p]);
                else:
                    self.solver.add_clause([-self.t[s][d], p]);

                self.solver.add_clause([-g[s-1], p, -self.t[s-1][d-1]]);
                self.solver.add_clause([g[s-1], -p]);
                self.solver.add_clause([-p, self.t[s-1][d-1]]);

    def is_true(self, index):
        return self.solution[index]

