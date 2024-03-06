from collections import namedtuple
import itertools
import sys
import logging

Team = namedtuple("Team", ("team_id", "min", "max", "type"))


def flatten_list_of_lists(List: list) -> list:
    # return [item for sublist in List for item in sublist]
    return list(itertools.chain.from_iterable(List))


class Stat:

	def __init__(self):
		self.propagate= 0
		self.wmp= 0 # whether a weakly monotonic propagator might has been executed
		self.fail= 0
		self.node= 0
		self.depth= 0
		self.memory= 0


	def report(self):
		print('==  propagations:\t', self.propagate)
		print('==  wmp:\t',self.wmp)
		print('==  nodes:\t',self.node)
		print('==  peak depth:\t',self.depth)
		print('==  fail:\t',self.fail)
		print('==  peak memory:\t',self.memory/1024,'KB')



class Solution:
	def __init__(self, **kwds):
		self.__dict__.update(kwds)


class ProblemInfeasible(Exception):
	"""Exception raised for models that turned out to be infeasible.

    Attributes:
        message -- explanation of the error
    """

	def __init__(self, message="Problem infeasible. Maybe insufficient capacity?"):
		self.message = message
		super().__init__(self.message)



class MissingCapacity(Exception):
	"""Exception raised for models that turned out to be infeasible.

    Attributes:
        message -- explanation of the error
    """

	def __init__(self, message="Problem infeasible. Maybe insufficient capacity?"):
		self.message = message
		super().__init__(self.message)



class DataIssueStop(Exception):
	"""Exception raised when there are problems with data

    Attributes:
        message -- explanation of the error
    """

	def __init__(self, message="Data issue"):
		self.message = message
		super().__init__(self.message)


class TypeComplianceError(Exception):
	"""Exception raised when there are problems with data

    Attributes:
        message -- explanation of the error
    """

	def __init__(self, message="Type Complianace Error"):
		self.message = message
		super().__init__(self.message)



def data_issue_continue(msg: str, execution_mode: bool) -> None:	
	logging.debug(msg)
	match execution_mode:
		case "interactive":
			msg1 = msg + " Continue? (y/n)\n"
			answer = input(msg1)
			if answer not in ['Y', 'y']:
				sys.exit("You decided to stop")
		case "exception":
			raise DataIssueStop(msg) 
		case "yes":
			pass