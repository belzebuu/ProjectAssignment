from adsigno.utils import *
from time import perf_counter
from gurobipy import *

def model_ip_instability(prob):
	start = perf_counter()
	m = Model('instability')

	allsolutions=False

	cal_P = list(prob.teams_per_topic.keys())
	cal_G = list(prob.groups.keys())
	array_ranks={}
	grp_ranks={}
	max_rank=0
	for g in cal_G:
		s=prob.groups[g][0] # we consider only first student, the other must have equal prefs
		grp_ranks[g]=prob.std_ranks[s]
		if len(grp_ranks[g]) > max_rank:
			max_rank=len(grp_ranks[g])

	a=dict() # the size of the group
	for g in cal_G:
		a[g] = len(prob.groups[g])

	# Create variables
	x = {} ## assignment vars
	for g in list(prob.groups.keys()):
		for p in list(prob.teams_per_topic.keys()):
			for t in range(len(prob.teams_per_topic[p])):
				x[g,p,t] = m.addVar(lb=0.0,ub=1.0,
						  vtype=GRB.BINARY,
						  obj=0.0,
						  name='x_%s_%s_%s' % (g, p, t))

	y={} ## is team t of project p used?
	for p in list(prob.teams_per_topic.keys()):
		for t in range(len(prob.teams_per_topic[p])):
			y[p,t] = m.addVar(lb=0.0,ub=1.0,
					  vtype=GRB.BINARY,
					  obj=0.0,
					  name='y_%s_%s' % (p,t))

	slack={} ## slack in team t of project p
	for p in cal_P:
		for t in range(len(prob.teams_per_topic[p])):
			slack[p,t] = m.addVar(lb=0.0,ub=10.0,
					      vtype=GRB.CONTINUOUS,
					      obj=0.0,
					      name='slack_%s_%s' % (p,t))

	############################################################
	z={} # z: binary variable to indicate whether there is space left in a team
	q={} # d: counts if space free in some better project
	for p in list(prob.teams_per_topic.keys()):
		for t in range(len(prob.teams_per_topic[p])):
			for g in list(prob.groups.keys()):
				z[g,p,t] = m.addVar(lb=0.0,ub=1.0,
								vtype=GRB.BINARY,
								obj=0.0,
								name='z_%s_%s_%s' % (g,p,t))
				q[g,p,t]=m.addVar(lb=0.0,ub=max_rank,
							 vtype=GRB.CONTINUOUS,
							 obj=0.0,
							 name='q_%s_%s_%s' % (g,p,t))

	# the total instability
	tot_instability=m.addVar(lb=0.0,ub=len(list(prob.groups.keys()))*max_rank,
		   vtype=GRB.CONTINUOUS,
		   obj=1.0,
		   name='tot_instability')
	############################################################
	m.update()
	############################################################
	# Assignment constraints
	#for g in prob.groups.keys():
		#working=[x[g,p,t] for p in prob.teams_per_topic.keys() for t in range(len(prob.teams_per_topic[p]))]
		#m.addConstr(quicksum(working) == 1, 'grp_%s' % g)

	# Assignment constraints
	for g in cal_G:
		peek=prob.std_type[prob.groups[g][0]]
		valid_prjs=[x for x in list(prob.teams_per_topic.keys()) if prob.teams_per_topic[x][0][2] in prob.valid_prjtype[peek]]
		#valid_prjs=filter(lambda x: prob.teams_per_topic[x][0][2]==peek or prob.teams_per_topic[x][0][2]=='alle', prob.teams_per_topic.keys())

		working=[x[g,p,t] for p in valid_prjs for t in range(len(prob.teams_per_topic[p]))]
		m.addConstr(quicksum(working) == 1, 'grp_%s' % g)
		for p in list(prob.teams_per_topic.keys()):
			if not p in valid_prjs:
				for t in range(len(prob.teams_per_topic[p])):
					m.addConstr(x[g,p,t] == 0, 'ngrp_%s' % g)
			if not p in prob.std_ranks[prob.groups[g][0]]:
				for t in range(len(prob.teams_per_topic[p])):
					m.addConstr(x[g,p,t] == 0, 'ngrp_%s' % g)


	# Capacity constraints
	for p in cal_P:
		for t in range(len(prob.teams_per_topic[p])):
			m.addConstr(quicksum(a[g]*x[g,p,t] for g in list(prob.groups.keys())) + slack[p,t]
				    == prob.teams_per_topic[p][t][1]*y[p,t], 'ub_%s' % (t))
			m.addConstr(quicksum(a[g]*x[g,p,t] for g in list(prob.groups.keys()))
				    >= prob.teams_per_topic[p][t][0]*y[p,t], 'lb_%s' % (t))

	# enforce restrictions on number of teams open across different topics:
	for rest in prob.restrictions:
		m.addConstr(quicksum(y[p,t] for p in rest["topics"] for t in range(len(prob.teams_per_topic[p]))) <= rest["cum"], "rest_%s" % "-".join(map(str,rest["topics"])))

	############################################################
	# Symmetry breaking on the teams
	for p in list(prob.teams_per_topic.keys()):
		for t in range(len(prob.teams_per_topic[p])-1):
			m.addConstr(quicksum(x[g,p,t] for g in list(prob.groups.keys())) >= quicksum(x[g,p,t+1] for g in list(prob.groups.keys()))   )

############################################################
# weighted
	#m.addConstr(v>=quicksum(weights[grp_ranks[g][p]] * a[g] * x[g,p,t] for g in prob.groups.keys() for p in grp_ranks[g].keys() for t in range(len(prob.teams_per_topic[p]))),  'v')

	############################################################
	# instability
	for p in list(prob.teams_per_topic.keys()):
		for t in range(len(prob.teams_per_topic[p])):
			for g in list(prob.groups.keys()):
				if a[g]<=prob.teams_per_topic[p][t][1]:
					m.addConstr(slack[p,t]+1-a[g] <= prob.teams_per_topic[p][t][1]*z[g,p,t], 'c30_%s_%s_%s' % (g,p,t))
					m.addConstr(a[g]+1-(1-y[p,t])*prob.teams_per_topic[p][t][0] <= prob.teams_per_topic[p][t][1]*z[g,p,t]+(prob.teams_per_topic[p][t][1]+1)*y[p,t], 'c31_%s_%s_%s' % (g,p,t))
				else:
					m.addConstr(z[g,p,t]==0, 'c3031_%s_%s_%s' % (g,p,t))
	for g in list(prob.groups.keys()):
		for p in list(grp_ranks[g].keys()):
			for p2 in list(grp_ranks[g].keys()):
				if (grp_ranks[g][p2] < grp_ranks[g][p]):
					for t in range(len(prob.teams_per_topic[p])):
						for t2 in range(len(prob.teams_per_topic[p2])):
							m.addConstr(q[g,p,t] >= (grp_ranks[g][p] - grp_ranks[g][p2]) * (x[g,p,t] + z[g,p2,t2] - 1), 'c32_%s_%s_%s' % (g,p,t))
	m.addConstr(tot_instability >= quicksum(a[g]*q[g,p,t] for g in list(prob.groups.keys()) for p in list(prob.teams_per_topic.keys()) for t in range(len(prob.teams_per_topic[p]) ) ), 'instability')
	#m.addConstr(0 == quicksum(q[g,p,t] for g in prob.groups.keys() for p in prob.teams_per_topic.keys() for t in range(len(prob.teams_per_topic[p]) ) ), 'instability')
	#W_instability = max_rank*len(prob.std_type.keys()) #max_rank*len(prob.groups)*len(prob.groups) ##2^7 * len(prob.groups)*
	############################################################
	# Compute optimal solution
	m.setObjective(tot_instability, GRB.MINIMIZE)
	#m.setObjective(W_v*v + W_f * f, GRB.MINIMIZE)
	#m.setObjective(W_v*v, GRB.MINIMIZE)

	m.setParam("MIPGap",0)
	m.setParam("MIPGapAbs",0)
	m.setParam("OptimalityTol",1e-09)
	m.setParam("Threads",1)
	m.setParam("TimeLimit", 3600)
	m.update()
	m.write("model.lp")
	m.optimize()

	# Print solution
	optimal_value=tot_instability.x
	solutions = []
	i=1;
	while optimal_value==tot_instability.x:
		teams={}
		topics={}
		expr=LinExpr()
		for g in prob.groups:
			for p in list(prob.teams_per_topic.keys()):
				for t in range(len(prob.teams_per_topic[p])):
					if x[g,p,t].x > 0.5:
						for s in prob.groups[g]:
							teams[s]=t
							topics[s]=p
						expr += 1-x[g,p,t]
					else:
						expr += x[g,p,t]
		print("solution "+str(i)+" found\n");
		elapsed = (perf_counter() - start)
		solutions.append(Solution(topics=topics,teams = teams, solved=[elapsed]))
		if m.status != GRB.status.OPTIMAL or not allsolutions:
			break;
		m.addConstr(expr, GRB.GREATER_EQUAL, 1.0, "no_good"+str(i) );
		m.update()
		m.optimize()
		i+=1

	return optimal_value,solutions
