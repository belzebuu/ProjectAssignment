#! /usr/bin/python

#from matrix import *
#from dfs_example import dfs
import os
from time import perf_counter
import sys
from load_data import *
from utils import *
from models_ip import *
#from models_ip_scip import *
from models_ip_weighted import *
from check_sol import *
import cml_parser

from subprocess import *

# sys.path.append("../tags/PA2013/src/")
from lottery import *
from models_ip_instability import *
from models_ip_envyfree import *
from models_hooker import *


def main():
    options, dirname = cml_parser.cml_parse()
  
    problem = Problem(dirname, options)
    max_topic = max(problem.teams_per_topic.keys())
    
    model = "minimax"

    if options.Wmethod in ["identity", "owa", "powers"]:
        while True:
            try:
                minimax, solutions = model_ip(problem, options)
                break
            except ProblemInfeasible:
                problem.add_fake_project(max_topic+1)
                problem.recalculate_ranks_values()
                

        stat = check_sol(solutions, problem, soldirname="sln")

        for st in stat:
            log = ['x']+[model]+solutions[0].solved+[os.path.basename(dirname)]+st
            print('%s' % ' '.join(map(str, log)))

        
        start = perf_counter()
        model = "minimax_instab_weighted"
        model = model+"-"+options.Wmethod
        value, solutions = model_ip_weighted(problem, options, minimax)
        elapsed = (perf_counter() - start)
    elif options.Wmethod=="lexi":
        solutions = lex_ip_procedure(problem, options)
    else:
        sys.exit("Wmethod not recognized")




    stat = check_sol(solutions, problem, soldirname="sln")
    for st in stat:
        log = ['x']+[model]+[elapsed]+[os.path.basename(dirname)]+st
        print('%s' % ' '.join(map(str, log)))

# print '%s' % ' '.join(map(str, solutions[0].solved))


if __name__ == "__main__":
    main()
