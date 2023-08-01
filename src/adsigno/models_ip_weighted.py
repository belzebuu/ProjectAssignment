from adsigno.utils import *
from adsigno.load_data import *
from time import perf_counter
from gurobipy import *
from adsigno.owa import *
import numpy as np

import pprint

def calculate_weights(weight_method: str, max_rank: int):
    if weight_method == "identity":
        weights = np.arange(max_rank + 1, dtype="float")
        weights[0] = np.nan  # max_rank + 1
    elif weight_method == "owa":
        weights = owa_weights(max_rank)
        # beta=1-0.001 #1.0/max_rank - 0.001
        # f_i = [1 for x in range(1,max_rank+1)] #[1./max_rank*x for x in range(1,max_rank+1)]
        # rescale=1000
        # weights[1] = rescale*f_i[0]*beta**(max_rank-1)/(1+beta)**(max_rank-1)
        # weights[2:] = map(lambda x: rescale*f_i[x-1]*beta**(max_rank-x)/(1+beta)**(max_rank+1-x), range(2,max_rank+1))
        # weights[0] = max(weights[1:])+1
    elif weight_method == "powers":
        weights = np.array([np.nan]+[-2 ** max(8 - x, 0)
                           for x in range(1, max_rank + 1)], dtype="float")
  
    return weights


def calculate_weight(weight_method: str, max_rank: int, rank: int):
    if weight_method == "identity":
        weight = rank  # np.arange(max_rank + 1, dtype="float")
    elif weight_method == "owa":
        weight = owa_single_weight(rank, max_rank)
        # beta=1-0.001 #1.0/max_rank - 0.001
        # f_i = [1 for x in range(1,max_rank+1)] #[1./max_rank*x for x in range(1,max_rank+1)]
        # rescale=1000
        # weights[1] = rescale*f_i[0]*beta**(max_rank-1)/(1+beta)**(max_rank-1)
        # weights[2:] = map(lambda x: rescale*f_i[x-1]*beta**(max_rank-x)/(1+beta)**(max_rank+1-x), range(2,max_rank+1))
        # weights[0] = max(weights[1:])+1
    elif weight_method == "powers":
        weight = -2 ** max(8 - rank, 0)
    return weight


def model_ip_weighted(prob, config, minimax):
    print("-"*60+"\nSolving model_ip_weighted")
    start = perf_counter()
    m = Model('weighted')

    # weight_method, instability, minimax, allsol

    cal_P = list(prob.teams_per_topic.keys())
    cal_G = list(prob.groups.keys())
    
    grp_ranks = {}
    grp_prioritized = {}
    max_rank = 0
    for g in cal_G:
        # we consider only first student, the others must have equal prefs
        s = prob.groups[g][0]
        #grp_ranks[g] = prob.std_ranks_av[s]
        #if len(prob.std_ranks_av[s]) == len(prob.topics):
        #    grp_ranks[g] = {}
        #else:
        grp_ranks[g] = prob.std_ranks_min[s]
        grp_prioritized[g] = utils.flatten_list_of_lists(prob.student_details[s]["priority_list"])
    
    max_rank = max([len(grp_ranks[g]) for g in grp_ranks])
    min_rank = min([len(grp_ranks[g]) for g in grp_ranks])

    a = dict()  # the size of the group
    for g in cal_G:
        a[g] = len(prob.groups[g])
    
    ############################################################
    weights = calculate_weights(config.Wmethod, max_rank)
    #pprint.pprint(grp_ranks)
    print(f"Topics available ({len(cal_P)}): {repr(cal_P)}")
    print(f"Number of prioritized projects between {min_rank} and {max_rank}") 
    print(f"Weights ({len(weights)}): "+repr(weights))
    ############################################################
    # Create variables
    x = {}  # # assignment vars
    for g in cal_G:
        for p in cal_P:
            for t in range(len(prob.teams_per_topic[p])):
                x[g, p, t] = m.addVar(lb=0.0, ub=1.0,
                                      vtype=GRB.BINARY,
                                      obj=0.0,
                                      name='x_%s_%s_%s' % (g, p, t))

    y = {}  # # is team t of project p used?
    for p in cal_P:
        for t in range(len(prob.teams_per_topic[p])):
            y[p, t] = m.addVar(lb=0.0, ub=1.0,
                               vtype=GRB.BINARY,
                               obj=0.0,
                               name='y_%s_%s' % (p, t))

    slack = {}  # # slack in team t of project p
    for p in cal_P:
        for t in range(len(prob.teams_per_topic[p])):
            slack[p, t] = m.addVar(lb=0.0, ub=10.0,
                                   vtype=GRB.CONTINUOUS,
                                   obj=0.0,
                                   name='slack_%s_%s' % (p, t))

    v = m.addVar(lb=-GRB.INFINITY,  # -2 ** 8 * len(list(prob.std_type.keys())),
                 # len(list(prob.std_type.keys())) * max_rank,
                 ub=GRB.INFINITY,
                 vtype=GRB.CONTINUOUS, obj=1.0, name='v')

    ############################################################
    if config.instability == True:
        z = {}  # z: binary variable to indicate whether there is space left in a team
        q = {}  # d: counts if space free in some better project
        for p in cal_P:
            for t in range(len(prob.teams_per_topic[p])):
                for g in list(prob.groups.keys()):
                    z[g, p, t] = m.addVar(lb=0.0, ub=1.0,
                                          vtype=GRB.BINARY,
                                          obj=0.0,
                                          name='z_%s_%s_%s' % (g, p, t))
                    q[g, p, t] = m.addVar(lb=0.0, ub=max_rank,
                                          vtype=GRB.CONTINUOUS,
                                          obj=0.0,
                                          name='q_%s_%s_%s' % (g, p, t))

        # the total instability
        tot_instability = m.addVar(lb=0.0, ub=len(list(prob.groups.keys())) * max_rank,
                                   vtype=GRB.CONTINUOUS,
                                   obj=1.0,
                                   name='tot_instability')
    else:
        tot_instability = 0
        W_instability = 0
    ############################################################
    if minimax > 0:
        u = {}  # rank assigned per group
        for g in cal_G:
            u[g] = m.addVar(lb=0.0, ub=max_rank,
                            vtype=GRB.INTEGER, obj=0.0, name='u_%s' % (g))
        f = m.addVar(lb=0.0, ub=len(list(prob.groups.keys())) * max_rank,
                     vtype=GRB.CONTINUOUS,
                     obj=0.0,
                     name='minimax')
    else:
        f = 0
        W_f = 0

    ############################################################
    m.update()
    ############################################################
    # Assignment constraints
    # for g in prob.groups.keys():
    # working=[x[g,p,t] for p in prob.teams_per_topic.keys() for t in range(len(prob.teams_per_topic[p]))]
    # m.addConstr(quicksum(working) == 1, 'grp_%s' % g)

    # Assignment constraints
   
    for g in cal_G:
        peek = prob.std_type[prob.groups[g][0]]
        valid_prjs = [x for x in cal_P if prob.teams_per_topic[x][0].type in prob.valid_prjtype[peek]]
        # valid_prjs=filter(lambda x: prob.teams_per_topic[x][0][2]==peek or prob.teams_per_topic[x][0][2]=='alle', prob.teams_per_topic.keys())

        working = [x[g, p, t]
                   for p in valid_prjs for t in range(len(prob.teams_per_topic[p]))]
        m.addConstr(quicksum(working) == 1, 'grp_%s' % g)
        for p in cal_P:
            if not p in valid_prjs:
                for t in range(len(prob.teams_per_topic[p])):
                    m.addConstr(x[g, p, t] == 0, 'not_valid_%s' % g)
            if not p in grp_prioritized[g]: #prob.std_ranks_av[prob.groups[g][0]]:
                for t in range(len(prob.teams_per_topic[p])):
                    m.addConstr(x[g, p, t] == 0, 'not_ranked_%s' % g)

    # Capacity constraints
    for p in cal_P:
        for t in range(len(prob.teams_per_topic[p])):
            m.addConstr(quicksum(a[g] * x[g, p, t] for g in list(prob.groups.keys())) + slack[p, t]
                        == prob.teams_per_topic[p][t].max * y[p, t], 'ub_%s_%d' % (p, t))
            m.addConstr(quicksum(a[g] * x[g, p, t] for g in list(prob.groups.keys()))
                        >= prob.teams_per_topic[p][t].min * y[p, t], 'lb_%s_%d' % (p, t))
            if config.groups == "pre":
                m.addConstr(quicksum(x[g, p, t] for g in cal_G)
                            <= 1, 'max_one_grp_%s_%s' % (p, t))

    # enforce restrictions on number of teams open across different topics:
    for rest in prob.restrictions:
        m.addConstr(quicksum(y[p, t] for p in rest["topics"] for t in range(
            len(prob.teams_per_topic[p]))) >= rest["groups_min"], "rstr_max_%s" % rest["username"])
        m.addConstr(quicksum(y[p, t] for p in rest["topics"] for t in range(
            len(prob.teams_per_topic[p]))) <= rest["groups_max"], "rstr_max_%s" % rest["username"])

    # enforce restrictions on number of students assigned across different topics:
    for rest in prob.restrictions:
        m.addConstr(quicksum(a[g]*x[g, p, t] for g in cal_G for p in rest["topics"] for t in range(
            len(prob.teams_per_topic[p]))) >= rest["capacity_min"], "rstr_nstds_min_%s" % rest["username"])
        if "capacity_max" in rest:
            m.addConstr(quicksum(a[g]*x[g, p, t] for g in cal_G for p in rest["topics"] for t in range(
                len(prob.teams_per_topic[p]))) <= rest["capacity_max"], "rstr_nstds_max_%s" % rest["username"])

    ############################################################
    # Symmetry breaking on the teams
    for p in cal_P:
        for t in range(len(prob.teams_per_topic[p]) - 1):
            m.addConstr(quicksum(x[g, p, t] for g in list(prob.groups.keys())) >= quicksum(
                x[g, p, t + 1] for g in list(prob.groups.keys())), "symbreak_%s" % (p))

    ############################################################
    # weighted # weights[grp_ranks[g][p]]
    m.addConstr(v >= quicksum(calculate_weight(config.Wmethod, max_rank, grp_ranks[g][p]) * a[g] * x[g, p, t] for g in list(
        prob.groups.keys()) for p in grp_prioritized[g] for t in range(len(prob.teams_per_topic[p]))), 'weight_v')

    ############################################################
    # instability
    if config.instability == True:
        print("Post instability constraints")
        for p in cal_P:
            for t in range(len(prob.teams_per_topic[p])):
                for g in list(prob.groups.keys()):
                    if a[g] <= prob.teams_per_topic[p][t].max:
                        m.addConstr(slack[p, t] + 1 - a[g] <= prob.teams_per_topic[p][t].max * z[g, p, t], 'c30_%s_%s_%s' % (g, p, t))
                        m.addConstr(a[g] + 1 - (1 - y[p, t]) * prob.teams_per_topic[p][t].min <= prob.teams_per_topic[p][t].max
                                    * z[g, p, t] + (prob.teams_per_topic[p][t].max + 1) * y[p, t], 'c31_%s_%s_%s' % (g, p, t))
                    else:
                        m.addConstr(z[g, p, t] == 0,
                                    'c3031_%s_%s_%s' % (g, p, t))
        for g in cal_G:
            for p in grp_prioritized[g]:
                for p2 in grp_prioritized[g]:
                    if (grp_ranks[g][p2] < grp_ranks[g][p]):
                        for t in range(len(prob.teams_per_topic[p])):
                            for t2 in range(len(prob.teams_per_topic[p2])):
                                m.addConstr(q[g, p, t] >= (grp_ranks[g][p] - grp_ranks[g][p2])
                                            * (x[g, p, t] + z[g, p2, t2] - 1), 'c32_%s_%s_%s' % (g, p, t))
        # m.addConstr(tot_instability >= quicksum(q[g,p,t] for g in prob.groups.keys() for p in prob.teams_per_topic.keys() for t in range(len(prob.teams_per_topic[p]) ) ), 'instability')
        m.addConstr(0 == quicksum(q[g, p, t] for g in list(prob.groups.keys()) for p in list(
            prob.teams_per_topic.keys()) for t in range(len(prob.teams_per_topic[p]))), 'instability')
        # W_instability = max_rank*len(prob.std_type.keys()) #max_rank*len(prob.groups)*len(prob.groups) ##2^7 * len(prob.groups)*
    ############################################################
    # minimax
    if minimax > 0:
        for g in cal_G:
            m.addConstr(u[g] ==
                        quicksum(grp_ranks[g][p] * x[g, p, t] for p in grp_prioritized[g]
                                 for t in range(len(prob.teams_per_topic[p]))),
                        'u_%s' % (g))
            m.addConstr(f >= u[g], 'minimax_%s' % g)
        m.addConstr(f <= minimax, 'minimax')
        # W_f = 1.0 #max_rank*len(prob.std_type.keys())*len(prob.std_type.keys())*1000
    if False: # this is old, now dealt with in read_students
        for g in cal_G:
            if prob.student_details[prob.groups[g][0]]["stype"]==config.cut_off_type:
                m.addConstr(config.cut_off >=
                            quicksum(grp_ranks[g][p] * x[g, p, t] for p in grp_prioritized[g]
                                    for t in range(len(prob.teams_per_topic[p]))),
                            'cutoff_special_%s' % (g))
 
    ############################################################
    # Compute optimal solution
    W_v = 1.0
    # m.setObjective(W_v*v + W_instability * instability + W_f * f, GRB.MINIMIZE)
    # m.setObjective(W_v*v + W_f * f, GRB.MINIMIZE)
    m.setObjective(W_v * v, GRB.MINIMIZE)

    m.setParam("MIPGap", 0)
    m.setParam("MIPGapAbs", 0)
    m.setParam("OptimalityTol", 1e-09)
    m.setParam("Threads", 1)
    m.setParam("Method", 4)  # for deterministic behavior
    m.setParam("TimeLimit", 3600)
    m.update()
    m.write("model.lp")
    m.optimize()
    m.write("model.sol")
    if m.status == GRB.status.INFEASIBLE:  # do IIS
        print('The model is infeasible; computing IIS')
        m.computeIIS()
        m.write(os.path.join("optprj_IIS.ilp"))
        print('\nThe following constraint(s) cannot be satisfied:')
        for c in m.getConstrs():
            if c.IISConstr:
                print(('%s' % c.constrName))
        print("\nSee optexam_IIS.ilp for explicit constraints.\n")
        exit(0)

    # Print solution
    optimal_value = v.x
    solutions = []
    i = 1
    while optimal_value == v.x:
        teams = {}
        topics = {}
        expr = LinExpr()
        for g in prob.groups:
            for p in cal_P:
                for t in range(len(prob.teams_per_topic[p])):
                    if x[g, p, t].x > 0.5:
                        for s in prob.groups[g]:
                            teams[s] = t
                            topics[s] = p
                        expr += 1 - x[g, p, t]
                    else:
                        expr += x[g, p, t]
        print("solution " + str(i) + " found\n")
        elapsed = (perf_counter() - start)
        solutions.append(
            Solution(topics=topics, teams=teams, solved=[elapsed]))
        if m.status != GRB.status.OPTIMAL or not config.allsol or elapsed >= 3600:
            break
        m.addConstr(expr, GRB.GREATER_EQUAL, 1.0, "no_good" + str(i))
        m.update()
        m.optimize()
        i += 1

    return optimal_value, solutions
