#! /usr/bin/python

from adsigno.utils import *
from adsigno.models_ip import *
#from models_ip_scip import *
from adsigno.models_ip_weighted import *
from adsigno.check_sol import *
from adsigno import cml_parser

from subprocess import *

# sys.path.append("../tags/PA2013/src/")
from adsigno.lottery import *
from adsigno.models_ip_instability import *
from adsigno.models_ip_envyfree import *
from adsigno.models_hooker import *



def process(options):
    problem = Problem(options)
    
    sln_dir = options.output_dir / "sln"
    os.makedirs(sln_dir, exist_ok=True)
    
    model = "minimax"
    logging.info(problem.teams_per_topic)
    if options.Wmethod in ["identity", "owa", "powers"]:
        while True:
            try:
                minimax, solutions = model_ip(problem, options)
            except ProblemInfeasible:
                problem.add_fake_project()
                problem.recalculate_ranks_values()
            else:
                break
        
        write_solution(solutions, problem, options, solutions[0].solved, sln_dir)
        start = perf_counter()
        value, solutions = model_ip_weighted(problem, options, minimax)
        elapsed = (perf_counter() - start)
    elif options.Wmethod=="lexi":
        start = perf_counter()
        solutions = lex_ip_procedure(problem, options)
        elapsed = (perf_counter() - start)
    else:
        sys.exit("Wmethod not recognized")
    write_solution(solutions, problem, options, elapsed, sln_dir)


def write_solution(solutions, problem, options, time_elapsed, sln_dir):    
    stat = check_sol(solutions, problem, sln_dir)
    model = f"{options.Wmethod}-{options.instability}"
    for st in stat:
        log = ['x']+[model]+[time_elapsed]+[sln_dir]+st
    logging.info('%s' % ' '.join(map(str, log)))

    # print '%s' % ' '.join(map(str, solutions[0].solved))


if __name__ == "__main__":
    options, dirname = cml_parser.cml_parse()
    process(dirname, options)
