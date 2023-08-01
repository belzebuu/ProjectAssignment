import adsigno

from collections import defaultdict

class AttributeDict(defaultdict):
	"""
	A dictionary in which values can be accessed using dot notation
	e.g. dict.key == dict[key]
	"""
	def __init__(self):
		super(AttributeDict, self).__init__(AttributeDict)

	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(key)

	def __setattr__(self, key, value):
		self[key] = value


path = "data/2021-example"

options = AttributeDict()
options.allsol = False
options.instability = False
options.expand_topics = False
options.groups = 'post'
options.Wmethod = 'owa'
options.cut_off = 10
options.cut_off_type = None
options.prioritize_all = False
options.allow_unassigned = False
options.min_preferences = 3
options.solution_file = None # this is not used, always written in 'sln'


try:
    adsigno.solve(path, options)
except (SystemError,SystemExit) as e:
    print(e)


options.solution_file = 'sln'+'/sol_001.txt' # now it must be the path to the solution
adsigno.report_sol_new(path, options) # outputs files in 'out'
adsigno.make_gtables("out") # using files in 'out' and outputting there too
adsigno.report_4_natfak(path, options) # outputs files in 'out'
