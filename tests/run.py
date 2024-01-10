import os
import adsigno

from collections import defaultdict

class AttributeDict(defaultdict):
	"""
	A dictionary in which values can be accessed using dot notation
	e.g. dict.key == dict[key]
	"""
	def __init__(self):
		super(AttributeDict, self).__init__(AttributeDict)
		self.set_defaults()

	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(key)

	def __setattr__(self, key, value):
		self[key] = value

	def set_defaults(self):
		self.data_dirname = None
		self.output_dir = None
		self.script_dir = "scripts/"
		self.allsol = False
		self.instability = False
		self.expand_topics = False
		self.groups = 'post'
		self.Wmethod = 'owa'
		self.cut_off = 10
		self.cut_off_type = None
		self.prioritize_all = False
		self.allow_unassigned = False
		self.min_preferences = 3
		self.solution_file = None



options = AttributeDict()
options.data_dirname = "data/2021-example"
options.output_dir = options.data_dirname

try:
    adsigno.solve(options) # writes output in output_dir
except (SystemError,SystemExit) as e:
    print(e)

options.solution_file = os.path.join(options.output_dir,'sln/sol_001.txt') # path to the solution

adsigno.solution_report(options) # outputs files in 'out'
adsigno.make_gtables(options) # using files in 'out' and outputting there too
adsigno.solution_report_4_admin(options) # outputs files in 'out'
