from utils import *
from load_data import *
import time
from gurobipy import *
from functools import reduce
from typing import Dict

def model_ip(prob, config):
    start = time.perf_counter()
    m = Model('leximin')

    grp_ranks = {}
    max_rank = 0
    cal_G = list(prob.groups.keys())
    cal_P = list(prob.teams_per_topic.keys())
    for g in cal_G:
        s = prob.groups[g][0]  # we consider only first student, the other must have equal prefs
        #if len(prob.std_ranks_av[s])==len(prob.topics):
        #    grp_ranks[g] = {}
        #else:
        grp_ranks[g] = prob.std_ranks_av[s]
        if len(grp_ranks[g]) > max_rank:
            max_rank = len(grp_ranks[g])

    a = dict()  # the size of the group
    for g in cal_G:
        a[g] = len(prob.groups[g])
    ############################################################
    # Create variables
    x = {}  # assignment vars
    for g in cal_G:
        for p in cal_P:
            for t in range(len(prob.teams_per_topic[p])):
                x[g, p, t] = m.addVar(lb=0.0, ub=1.0,
                                      vtype=GRB.BINARY,
                                      obj=0.0,
                                      name='x_%s_%s_%s' % (g, p, t))

    y = {}  # is team t of project p used?
    for p in cal_P:
        for t in range(len(prob.teams_per_topic[p])):
            y[p, t] = m.addVar(lb=0.0, ub=1.0,
                               vtype=GRB.BINARY,
                               obj=0.0,
                               name='y_%s_%s' % (p, t))

    u = {}  # rank assigned per group
    for g in cal_G:
        u[g] = m.addVar(lb=0.0, ub=max_rank,
                        vtype=GRB.INTEGER,
                        obj=0.0,
                        name='u_%s' % (g))

    v = m.addVar(lb=0.0, ub=max_rank,
                 vtype=GRB.INTEGER,
                 obj=1.0,
                 name='v_%s' % (g))

    m.update()
    ############################################################
    # Assignment constraints
    # for g in prob.groups.keys():
    #working=[x[g,p,t] for p in prob.teams_per_topic.keys() for t in range(len(prob.teams_per_topic[p]))]
    #m.addConstr(quicksum(working) == 1, 'grp_%s' % g)
    # Assignment constraints
    for g in cal_G:
        print(prob.teams_per_topic)
        print(cal_P)
        print( prob.valid_prjtype)
        
        peek = prob.std_type[prob.groups[g][0]]
        print(peek)

        for yyy in cal_P:
            print(prob.teams_per_topic[yyy])
        valid_prjs = [x for x in cal_P if prob.teams_per_topic[x][0].type in prob.valid_prjtype[peek]]
        #valid_prjs=filter(lambda x: prob.teams_per_topic[x][0][2]==peek or prob.teams_per_topic[x][0][2]=='alle', prob.teams_per_topic.keys())        
        working = [x[g, p, t] for p in valid_prjs for t in range(len(prob.teams_per_topic[p]))]
        m.addConstr(quicksum(working) == 1, 'grp_%s' % g)       
        for p in cal_P:
            if not p in valid_prjs:
                for t in range(len(prob.teams_per_topic[p])):
                    m.addConstr(x[g, p, t] == 0, 'not_valid_%s_%s' % (g,p))
            if not p in grp_ranks[g]: # prob.std_ranks_av[prob.groups[g][0]]:
                for t in range(len(prob.teams_per_topic[p])):
                    m.addConstr(x[g, p, t] == 0, 'not_ranked_%s_%s' % (g,p))
    # Capacity constraints
    for p in cal_P:
        for t in range(len(prob.teams_per_topic[p])):
            m.addConstr(quicksum(a[g]*x[g, p, t] for g in cal_G) <=
                        prob.teams_per_topic[p][t].max * y[p, t], 'ub_%s' % (t))
            m.addConstr(quicksum(a[g]*x[g, p, t] for g in cal_G) >=
                        prob.teams_per_topic[p][t].min * y[p, t], 'lb_%s' % (t))
            if config.groups=="pre":
                m.addConstr(quicksum(x[g, p, t] for g in cal_G) <= 1, 'max_one_grp_%s%s' % (p, t))

    # put in u the rank assigned to the group
    for g in cal_G:
        m.addConstr(u[g] ==
                    quicksum(grp_ranks[g][p] * x[g, p, t] for p in list(grp_ranks[g].keys())
                             for t in range(len(prob.teams_per_topic[p]))),
                    'u_%s' % (g))
        m.addConstr(v >= u[g], 'v_%s' % g)
    
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
        m.addConstr(quicksum(a[g]*x[g, p, t] for g in cal_G for p in rest["topics"] for t in range(
            len(prob.teams_per_topic[p]))) <= rest["capacity_max"], "rstr_nstds_max_%s" % rest["username"])

    
    # Symmetry breaking on the teams
    for p in cal_P:
        for t in range(len(prob.teams_per_topic[p])-1):
            m.addConstr(quicksum(x[g, p, t] for g in cal_G)
                        >= quicksum(x[g, p, t+1] for g in cal_G))

    ############################################################
    # Compute optimal solution
    m.setObjective(v, GRB.MINIMIZE)
    m.write("model_ip.lp")
    m.optimize()
    if m.status == GRB.status.INFEASIBLE:  # do IIS
        if config.allow_unassigned:
            raise ProblemInfeasible
        else:
            print('The model is infeasible; computing IIS')
            m.computeIIS()
            m.write(os.path.join("optprj_IIS.ilp"))
            print('\nThe following constraint(s) cannot be satisfied:')
            for c in m.getConstrs():
                if c.IISConstr:
                    print(('%s' % c.constrName))
            print("\nSee optexam_IIS.ilp for explicit constraints.\n")
            raise SystemExit
    
    # Print solution
    teams = {}
    topics = {}
    if m.status == GRB.status.OPTIMAL:
        for g in prob.groups:
            for p in cal_P:
                for t in range(len(prob.teams_per_topic[p])):
                    if x[g, p, t].x > 0:
                        for s in prob.groups[g]:
                            teams[s] = t
                            topics[s] = p
    elapsed = (time.perf_counter() - start)
    solution = []
    
    solution.append(Solution(topics=topics, teams=teams, solved=[elapsed]))
    return v.x, solution


def lex_ip_procedure(prob, options: Dict):
    v = model_ip(prob, options)[0]
    print(v)
    h = int(v)
    z = []
    solved = [0]*(h+1)
    while h > 0:
        start = time.perf_counter()
        (z, sol) = model_lex(prob, int(v), h, z, options, direction="bottomup")
        elapsed = (time.perf_counter() - start)
        solved[h] = elapsed
        h -= 1
        print(z)

    return [Solution(topics=sol["topics"], teams=sol["teams"], solved=[sum(solved)])]


def greedy_maximum_matching_ip_procedure(prob, minimax, options):
    MR = 40
    if minimax:
        v = prob.minimax_sol  # model_ip(prob)[0]
    else:
        v = MR
    print(v)
    h = 1
    z = []
    solved = [0]*(MR+1)
    while h < int(v):
        start = time.perf_counter()
        (z, sol) = model_lex(prob, int(v), h, z, options, "topdown")
        elapsed = (time.perf_counter() - start)
        solved[h] = elapsed
        h += 1
        print(reduce((lambda x, y: x + y), z))
        if reduce((lambda x, y: x + y), z) >= len(list(prob.std_type.keys())): break

    return [Solution(topics=sol["topics"], teams=sol["teams"], solved=[sum(solved)])]


def model_lex(prob, v, h, z, options: Dict, direction: str):
    start = time.perf_counter()
    m = Model('leximin')

    cal_P = list(prob.teams_per_topic.keys())
    cal_G = list(prob.groups.keys())

    grp_ranks = {}
    max_rank = 0
    grp_x_ranks = {}
    for g in list(prob.groups.keys()):
        s = prob.groups[g][0]  # we consider only first student, the other must have equal prefs
        grp_ranks[g] = prob.std_ranks_av[s]
        if len(grp_ranks[g]) > max_rank:
            max_rank = len(grp_ranks[g])
        for p in grp_ranks[g]:
            r = grp_ranks[g][p]
            if r in grp_x_ranks:
                grp_x_ranks[r].append((g, p))
            else:
                grp_x_ranks[r] = [(g, p)]

    a = dict()  # the size of the group
    for g in list(prob.groups.keys()):
        a[g] = len(prob.groups[g])

    ############################################################
    # Create variables
    x = {}  # assignment vars
    for g in list(prob.groups.keys()):
        for p in list(prob.teams_per_topic.keys()):
            for t in range(len(prob.teams_per_topic[p])):
                x[g, p, t] = m.addVar(lb=0.0, ub=1.0,
                                      vtype=GRB.BINARY,
                                      obj=0.0,
                                      name='x_%s_%s_%s' % (g, p, t))

    y = {}  # is team t of project p used?
    for p in list(prob.teams_per_topic.keys()):
        for t in range(len(prob.teams_per_topic[p])):
            y[p, t] = m.addVar(lb=0.0, ub=1.0,
                               vtype=GRB.BINARY,
                               obj=0.0,
                               name='y_%s_%s' % (p, t))

    slack = {}  # slack in team t of project p
    for p in list(prob.teams_per_topic.keys()):
        for t in range(len(prob.teams_per_topic[p])):
            slack[p, t] = m.addVar(lb=0.0, ub=10.0,
                                   vtype=GRB.CONTINUOUS,
                                   obj=0.0,
                                   name='slack_%s_%s' % (p, t))

    u = {}  # rank assigned per group
    for g in list(prob.groups.keys()):
        u[g] = m.addVar(lb=0.0, ub=max_rank,
                        vtype=GRB.INTEGER,
                        obj=0.0,
                        name='u_%s' % (g))

    z_h = m.addVar(lb=0.0, ub=len(prob.std_type),
                   vtype=GRB.INTEGER,
                   obj=0.0,
                   name='z_%s' % (h))

    ############################################################
    if options.instability:
        z2 = {}  # binary variable to indicate whether there is space left in a team
        q = {}  # counts if space free in some better project
        for p in list(prob.teams_per_topic.keys()):
            for t in range(len(prob.teams_per_topic[p])):
                for g in list(prob.groups.keys()):
                    z2[g, p, t] = m.addVar(lb=0.0, ub=1.0,
                                           vtype=GRB.BINARY,
                                           obj=0.0,
                                           name='z2_%s_%s_%s' % (g, p, t))
                    q[g, p, t] = m.addVar(lb=0.0, ub=max_rank,
                                          vtype=GRB.CONTINUOUS,
                                          obj=0.0,
                                          name='q_%s_%s_%s' % (g, p, t))

        # the total instability
        tot_instability = m.addVar(lb=0.0, ub=len(list(prob.groups.keys()))*max_rank,
                                   vtype=GRB.CONTINUOUS,
                                   obj=1.0,
                                   name='instability')
    else:
        tot_instability = 0
        W_instability = 0

    m.update()
    ############################################################
    # Assignment constraints
    # for g in prob.groups.keys():
    #working=[x[g,p,t] for p in prob.teams_per_topic.keys() for t in range(len(prob.teams_per_topic[p]))]
    #m.addConstr(quicksum(working) == 1, 'grp_%s' % g)

    # Assignment constraints
    for g in cal_G:
        peek = prob.std_type[prob.groups[g][0]]
        valid_prjs = [x for x in cal_P if prob.teams_per_topic[x]
                      [0].type in prob.valid_prjtype[peek]]
        # valid_prjs=filter(lambda x: prob.teams_per_topic[x][0][2]==peek or prob.teams_per_topic[x][0][2]=='alle', prob.teams_per_topic.keys())

        working = [x[g, p, t]
                   for p in valid_prjs for t in range(len(prob.teams_per_topic[p]))]
        m.addConstr(quicksum(working) == 1, 'grp_%s' % g)
        for p in cal_P:
            if not p in valid_prjs:
                for t in range(len(prob.teams_per_topic[p])):
                    m.addConstr(x[g, p, t] == 0, 'not_valid_%s' % g)
            if not p in prob.std_ranks_av[prob.groups[g][0]]:
                for t in range(len(prob.teams_per_topic[p])):
                    m.addConstr(x[g, p, t] == 0, 'not_ranked_%s' % g)

    # Capacity constraints
    for p in cal_P:
        for t in range(len(prob.teams_per_topic[p])):
            m.addConstr(quicksum(a[g] * x[g, p, t] for g in list(prob.groups.keys())) + slack[p, t]
                        == prob.teams_per_topic[p][t][1] * y[p, t], 'ub_%s_%d' % (p, t))
            m.addConstr(quicksum(a[g] * x[g, p, t] for g in list(prob.groups.keys()))
                        >= prob.teams_per_topic[p][t][0] * y[p, t], 'lb_%s_%d' % (p, t))
            if options.groups == "pre":
                m.addConstr(quicksum(x[g, p, t] for g in cal_G)
                            <= 1, 'max_one_grp_%s%s' % (p, t))
    
    # enforce restrictions on number of teams open across different topics:
    if 'nteams' in prob.restrictions:
        for rest in prob.restrictions['nteams']:
            m.addConstr(quicksum(y[p, t] for p in rest["topics"] for t in range(
                len(prob.teams_per_topic[p]))) <= rest["groups_max"], "rest_%s" % rest["username"])


    # enforce restrictions on number of students assigned across different topics:
    if 'nteams' in prob.restrictions:
        for rest in prob.restrictions['nteams']:
            m.addConstr(quicksum(a[g]*x[g, p, t] for g in cal_G for p in rest["topics"] for t in range(
                len(prob.teams_per_topic[p]))) <= rest["capacity_max"], "rest_nstds_%s" % rest["username"])

    ############################################################
    # Symmetry breaking on the teams
    for p in cal_P:
        for t in range(len(prob.teams_per_topic[p]) - 1):
            m.addConstr(quicksum(x[g, p, t] for g in list(prob.groups.keys())) >= quicksum(
                x[g, p, t + 1] for g in list(prob.groups.keys())), "symbreak_%s" % (p))

    ############################################################
    # instability
    if options.instability:
        # u={} # rank assigned per group
        # for g in cal_G:
        #	u[g]=m.addVar(lb=0.0,ub=max_rank,
        #		   vtype=GRB.INTEGER,
        #		   obj=0.0,
        #		   name='u_%s' % (g))
        # f=m.addVar(lb=0.0,ub=len(prob.groups.keys())*max_rank,
        #	   vtype=GRB.CONTINUOUS,
        #	   obj=0.0,
        #	   name='minimax')
        # put in u the rank assigned to the group
        #
        for g in list(prob.groups.keys()):
            m.addConstr(u[g] ==
                        quicksum(grp_ranks[g][p] * x[g, p, t] for p in list(grp_ranks[g].keys())
                                 for t in range(len(prob.teams_per_topic[p]))),
                        'u_%s' % (g))
            m.addConstr(v >= u[g], 'v_%s' % g)
    ############################################################
    if direction == "bottomup":
        l = v
        while l > h:
            # print z,v,l
            m.addConstr(z[v-l] >= quicksum(a[g] * x[g, p, t] for (g, p) in grp_x_ranks[l]
                                           for t in range(len(prob.teams_per_topic[p]))), 'z_%s' % l)
            l -= 1
        m.addConstr(z_h >= quicksum(a[g] * x[g, p, t] for (g, p) in grp_x_ranks[l]
                                    for t in range(len(prob.teams_per_topic[p]))), 'z_%s' % h)
    elif direction == "topdown":
        l = 1
        while l < h:
            # print z,v,l
            m.addConstr(z[l-1] <= quicksum(a[g] * x[g, p, t] for (g, p) in grp_x_ranks[l]
                                           for t in range(len(prob.teams_per_topic[p]))), 'z_%s' % l)
            l += 1
        m.addConstr(z_h <= quicksum(a[g] * x[g, p, t] for (g, p) in grp_x_ranks[l]
                                    for t in range(len(prob.teams_per_topic[p]))), 'z_%s' % h)
    else:
        sys.exit("something wrong in model_lex")

    # Symmetry breaking on the teams
    for p in list(prob.teams_per_topic.keys()):
        for t in range(len(prob.teams_per_topic[p])-1):
            m.addConstr(quicksum(x[g, p, t] for g in list(prob.groups.keys()))
                        >= quicksum(x[g, p, t+1] for g in list(prob.groups.keys())))

    ############################################################
    # instability
    if options.instability:
        for p in cal_P:
            for t in range(len(prob.teams_per_topic[p])):
                for g in list(prob.groups.keys()):
                    if a[g] <= prob.teams_per_topic[p][t][1]:
                        m.addConstr(slack[p, t]+1-a[g] <= prob.teams_per_topic[p][t]
                                    [1]*z2[g, p, t], 'c30_%s_%s_%s' % (g, p, t))
                        m.addConstr(a[g]+1-(1-y[p, t])*prob.teams_per_topic[p][t][0] <= prob.teams_per_topic[p][t][1]
                                    * z2[g, p, t]+(prob.teams_per_topic[p][t][1]+1)*y[p, t], 'c31_%s_%s_%s' % (g, p, t))
                    else:
                        m.addConstr(z2[g, p, t] == 0, 'c3031_%s_%s_%s' % (g, p, t))
        for g in cal_G:
            for p in list(grp_ranks[g].keys()):
                for p2 in list(grp_ranks[g].keys()):
                    if (grp_ranks[g][p2] < grp_ranks[g][p]):
                        for t in range(len(prob.teams_per_topic[p])):
                            for t2 in range(len(prob.teams_per_topic[p2])):
                                m.addConstr(q[g, p, t] >= (grp_ranks[g][p] - grp_ranks[g][p2])
                                            * (x[g, p, t] + z2[g, p2, t2] - 1), 'c32_%s_%s_%s' % (g, p, t))
        #m.addConstr(tot_instability >= quicksum(q[g,p,t] for g in prob.groups.keys() for p in prob.teams_per_topic.keys() for t in range(len(prob.teams_per_topic[p]) ) ), 'instability')
        m.addConstr(0 == quicksum(q[g, p, t] for g in list(prob.groups.keys()) for p in list(
            prob.teams_per_topic.keys()) for t in range(len(prob.teams_per_topic[p]))), 'instability')
        # W_instability = max_rank*len(prob.std_type.keys()) #max_rank*len(prob.groups)*len(prob.groups) ##2^7 * len(prob.groups)*
    ############################################################
    # Compute optimal solution
    if direction == "bootomup":
        m.setObjective(z_h, GRB.MINIMIZE)
    elif direction == "topdown":
        m.setObjective(z_h, GRB.MAXIMIZE)

    m.setParam("MIPGap", 0)
    m.setParam("MIPGapAbs", 0)
    m.setParam("OptimalityTol", 1e-09)
    m.setParam("Threads", 1)
    m.update()
    m.write("model.lp")
    m.optimize()
    # m.write("model-"+str(h)+".lp")
    # Print solution
    teams = {}
    topics = {}
    if m.status == GRB.status.OPTIMAL:
        for g in prob.groups:
            for p in list(prob.teams_per_topic.keys()):
                for t in range(len(prob.teams_per_topic[p])):
                    if x[g, p, t].x > 0.5:
                        for s in prob.groups[g]:
                            teams[s] = t
                            topics[s] = p

    z.append(z_h.x)
    return z, dict(topics=topics, teams=teams)
