#! /usr/bin/python

from adsigno.utils import *
from adsigno.models_ip import *
#from models_ip_scip import *
from adsigno.models_ip_weighted import *
from adsigno.check_sol import *
import adsigno.cml_parser

from subprocess import *

# sys.path.append("../tags/PA2013/src/")
from adsigno.lottery import *
from adsigno.models_ip_instability import *
from adsigno.models_ip_envyfree import *
from adsigno.models_hooker import *



def solve(dirname, options):
    problem = Problem(dirname, options)
    max_topic = max(problem.teams_per_topic.keys())

    sln = dirname+"/sln"
    os.makedirs(sln,exist_ok=True)
    
    model = "minimax"
    print(problem.teams_per_topic)
    if options.Wmethod in ["identity", "owa", "powers"]:
        while True:
            try:
                minimax, solutions = model_ip(problem, options)
            except ProblemInfeasible:
                problem.add_fake_project(max_topic+1)
                problem.recalculate_ranks_values()
            else:
                break
        stat = check_sol(solutions, problem, soldirname=sln)
        
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




    stat = check_sol(solutions, problem, soldirname=sln)
    for st in stat:
        log = ['x']+[model]+[elapsed]+[os.path.basename(dirname)]+st
        print('%s' % ' '.join(map(str, log)))

# print '%s' % ' '.join(map(str, solutions[0].solved))


if __name__ == "__main__":
    options, dirname = cml_parser.cml_parse()
    solve(dirname, options)
