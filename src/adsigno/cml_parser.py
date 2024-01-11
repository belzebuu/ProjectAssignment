from optparse import OptionParser
from pathlib import Path
import yaml

def cml_parse() -> dict:
    usage = "usage: %prog [options] DIRNAME"
    parser = OptionParser(usage)
    
    parser.add_option("-e", "--expand_topics", action="store_true", dest="expand_topics", default=False, 
                        help="Whether the file projects.csv contains teams or topics to be expanded into teams [default: %default]")
    parser.add_option("-m", "--min_preferences", dest="min_preferences", type="int", default=7, help="The minimum number of preferences required. [default: %default]")
    parser.add_option("-p", '--prioritize_all', dest='prioritize_all', action='store_true', default=False, help="Whether to expand students' priority lists by appending, tied up as worst priority, all non-prioritized projects. [default: %default]")
    #parser.set_defaults(prioritize_all=False)
    parser.add_option("-u", '--allow_unassigned', dest="allow_unassigned", help="handle lack of capacity by adding placeholder projects", default=False, action='store_true')
    #parser.add_argument('--no-prioritize_all', dest='prioritize_all', action='store_false')    
    
    parser.add_option("-g", "--groups", dest="groups", type="string", default="post", metavar="[pre|post]", help="Whether groups are formed pre or post, that is, if 'post' then possible to set more than one group in a team [default: %default]")
    
    parser.add_option("-w", "--Wmethod", dest="Wmethod", type="string", default="owa", metavar="[identity|owa|powers]",
                      help="The weighting scheme, eg, \"owa\". [default: %default]")    
    parser.add_option("-i", "--instability", action="store_true", dest="instability", default=False, help="Whether the constraint on instability should be included or not [default: %default]")
    parser.add_option("-a", "--allsol", action="store_true", dest="allsol", default=False,
                      help="All solutions")
    
    parser.add_option("-t", "--cut_off_type", dest="cut_off_type", type="string", default=None, help="The type of users eligible for a privileged treatment. [default: %default]")
    parser.add_option("-c", "--cut_off", dest="cut_off", type="int", default=10, help="The cut off value on preferences to favour a type of users. [default: %default]")
    
    parser.add_option("-s", "--solution_file", dest="solution_file", metavar="PATH", default=None, help="The file where the solution is stored [default: %default]")
    parser.add_option("-o", "--output_dir", dest="output_dir", type=str, metavar="PATH", default=None, help="The directory where the output directories are stored ('log/' 'sln/' 'out/'). If 'None', then same as input direcotry. [default: %default]")

    (options, args) = parser.parse_args()  # by default it uses sys.argv[1:]

    if not len(args) == 1:
        parser.error("Directory missing")
        
    options.data_dirname = Path(args[0])    
    if options.output_dir is None:
        options.output_dir = options.data_dirname
    else:
        options.output_dir=Path(options.output_dir)

    print(yaml.dump(options))
    return options