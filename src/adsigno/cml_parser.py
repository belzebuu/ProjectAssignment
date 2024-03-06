import argparse
from pathlib import Path
import yaml
import logging
import logging.config

def cml_parse() -> dict:        
    parser = argparse.ArgumentParser(prog="assign", description='Student-project assignment',
                                    usage = "assign [options] DIRNAME"
                                    )
    
    parser.add_argument("-e", "--expand_topics", action="store_true", dest="expand_topics", default=False, 
                         help="Whether the file projects.csv contains teams or topics to be expanded into teams [default: %(default)s]")
    parser.add_argument("-m", "--min_preferences", dest="min_preferences", type=int, default=7, help="The minimum number of preferences required. [default: %(default)s]")
    parser.add_argument("-p", '--prioritize_all', dest='prioritize_all', action='store_true', default=False, help="Whether to expand students' priority lists by appending, tied up as worst priority, all non-prioritized projects. [default: %(default)s]")
    #parser.set_defaults(prioritize_all=False)
    parser.add_argument("-u", '--allow_unassigned', dest="allow_unassigned", help="handle lack of capacity by adding placeholder projects", default=False, action='store_true')
    # #parser.add_argument('--no-prioritize_all', dest='prioritize_all', action='store_false')    
    
    parser.add_argument("-g", "--groups", dest="groups", default="post", choices=["pre","post"], help="Whether groups are formed pre or post, that is, if 'post' then possible to set more than one group in a team [default: %(default)s]")
    
    parser.add_argument("-w", "--Wmethod", dest="Wmethod", default="owa", choices=["identity","owa","powers"], help="The weighting scheme, eg, \"owa\". [default: %(default)s]")    
    parser.add_argument("-i", "--instability", action="store_true", dest="instability", default=False, help="Whether the constraint on instability should be included or not [default: %(default)s]")
    parser.add_argument("-a", "--allsol", action="store_true", dest="allsol", default=False, help="All solutions")
    parser.add_argument("-x", "--execution_mode", dest="execution_mode", choices=["except","interact","continue"], default="except", help="Interactive execution. [default: %(default)s]")
    
    parser.add_argument("-t", "--cut_off_type", dest="cut_off_type", default=None, help="The type of users eligible for a privileged treatment. [default: %(default)s]")
    parser.add_argument("-c", "--cut_off", dest="cut_off", type=int, default=10, help="The cut off value on preferences to favour a type of users. [default: %(default)s]")
    
    parser.add_argument("-l", "--logging_file", dest="logging_file", metavar="PATH", default=None, type=Path, help="The file where the logging is sent [default: stderr]")
    parser.add_argument("-s", "--solution_file", dest="solution_file", metavar="PATH", default=None, type=Path, help="The file where the solution is stored [default: %(default)s]")
    parser.add_argument("-o", "--output_dir", dest="output_dir", metavar="PATH", default=None, type=Path, help="The directory where the output directories are stored ('log/' 'sln/' 'out/'). If 'None', then same as input direcotry. [default: %(default)s]")
    parser.add_argument("data_dirname",nargs=1,type=Path)

    options = parser.parse_args()  # by default it uses sys.argv[1:]
        
    options.data_dirname = options.data_dirname[0]   
    if options.output_dir is None:
        options.output_dir = options.data_dirname
    else:
        options.output_dir=Path(options.output_dir)

    with open('./logging.yaml', 'r') as stream:
        lconfig = yaml.load(stream, Loader=yaml.FullLoader)
    logging.config.dictConfig(lconfig)
    #logging.config.fileConfig('logging.conf')
    
    if options.logging_file is not None:
        # Set Logging level to INFO.
        # Argument `filename` can be omitted to output -> stderr
        logging.basicConfig(filename=options.logging_file, level=logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)
        #logging.basicConfig(level=logging.ERROR)

    logging.info(yaml.dump(options))
    return options