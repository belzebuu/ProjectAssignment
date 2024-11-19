import sys
import adsigno.utils as utils
import json

def search_unstable_students(k, sol, problem, members, soldirname="") -> int:
    # returns number of unstable students        
    unstable = 0
    out_str = "-"*60+"\nInstability:\n"    
    for g in problem.groups:
        s = problem.groups[g][0]
        grp_prioritized = utils.flatten_list_of_lists(problem.student_details[s]["priority_list"])
        if s in sol.topics:
            rank = problem.std_ranks_min[s][sol.topics[s]]
            for p in grp_prioritized:
                if (problem.std_ranks_min[s][p] < rank):
                    for t in range(len(problem.teams_per_topic[p])):
                        if len(members[p][t]) > 0:
                            if len(members[p][t])+len(problem.groups[g]) <= problem.teams_per_topic[p][t].max:
                                out_str += "student " + str(s) + " could go in "+str(p) + "\n"
                                unstable += len(problem.groups[g])
                        elif len(problem.groups[g]) >= problem.teams_per_topic[p][t].min and (len(problem.groups[g]) <= problem.teams_per_topic[p][t].max):
                            out_str+="student " + str(s) + " could go in unopened "+str(p)+"\n"
                            unstable += len(problem.groups[g])
    out_str += "-"*60
    if soldirname != "":
        filename = "%s/log_%03d.txt" % (soldirname, k)
        with open(filename, "w") as filehandle:
            filehandle.write(out_str)
    return unstable



def check_sol(solutions, problem, soldirname=""):
    logs = []
    num_solutions = len(solutions)
    print("Number of solutions: ", num_solutions)
    for k, sol in enumerate(solutions):        
        log = []
        # sol=solutions[0]
        # let's check
        unass_students = 0
        members = {}
        for p in problem.teams_per_topic:
            for t in range(len(problem.teams_per_topic[p])):
                if p in members:
                    members[p].append([x for x in list(sol.topics.keys()) if p ==
                                       sol.topics[x] and t == sol.teams[x]])
                else:
                    members[p] = [[x for x in list(sol.topics.keys())
                                   if p == sol.topics[x] and t == sol.teams[x]]]

        # students only get projects they ranked
        for s in problem.std_type:
            if s not in sol.topics:
                unass_students += 1
            elif sol.topics[s] not in list(problem.std_ranks_min[s].keys()):
                print(sol.topics[s], problem.std_ranks_min[s])
                sys.exit("%s student assigned to a project not ranked" % s)

        # group members are assigned to the same teams
        for g in problem.groups:
            for s1 in problem.groups[g]:
                for s2 in problem.groups[g]:
                    if s1 in sol.topics and s2 in sol.topics:
                        if (sol.topics[s1] != sol.topics[s2]) or (sol.teams[s1] != sol.teams[s2]):
                            sys.exit("group members assigned in different projects")

        # team creation and cardinality
        nteams = 0
        underfull = 0
        for p in problem.teams_per_topic:
            for t in range(len(problem.teams_per_topic[p])):
                nteams += 1
                # print str(len(members[p][t])) +" "+ str(problem.teams_per_topic[p][t][1])
                assert (len(members[p][t]) <= problem.teams_per_topic[p][t].max)
                if len(members[p][t]) < problem.teams_per_topic[p][t].min and len(members[p][t]) > 0:
                    underfull += 1
        # check how many students are not assigned to their area
        counter_area = 0
        for s in problem.std_type:
            if s in sol.topics:
                p = sol.topics[s]
                prj_type = problem.teams_per_topic[p][0].type
                if prj_type != problem.std_type[s] and prj_type != "alle":
                    counter_area += 1


        unstable = search_unstable_students(k+1, sol, problem, members, soldirname)

        # count classical utility
        tot_util = 0
        for s in problem.std_type:
            if s in sol.topics:
                tot_util += problem.std_ranks_min[s][sol.topics[s]]
        ############################################################
        # count envy
        tot_envy = 0
        for s in problem.std_type:
            max_envy = 0
            for s1 in problem.std_type:
                if s1 != s and s in sol.topics and s1 in sol.topics:
                    if sol.topics[s1] in problem.std_ranks_min[s]:
                        envy = max(0, problem.std_ranks_min[s][sol.topics[s]] -
                                   problem.std_ranks_min[s][sol.topics[s1]])
                        if (envy > max_envy):
                            max_envy = envy
            tot_envy += max_envy

        max_rank = 0
        for s in list(problem.std_ranks_min.keys()):
            if len(problem.std_ranks_min[s])+1 > max_rank:
                max_rank = len(problem.std_ranks_min[s])+1

# 		max_rank=0
# 		array_ranks={}
# 		grp_ranks={}
# 		for g in problem.groups.keys():
# 			s=problem.groups[g][0] # we consider only first student, the other must have equal prefs
# 			grp_ranks[g]=problem.std_ranks_min[s]
# 			if len(grp_ranks[g])+1 > max_rank:
# 				max_rank=len(grp_ranks[g])+1
#
# 		for g in problem.groups.keys():
# 			values=map(lambda x: max_rank if x not in grp_ranks[g].keys() else grp_ranks[g][x], problem.teams_per_topic.keys())
# 			array_ranks[g]=dict(zip(problem.teams_per_topic.keys(),values))
#
# 		tot_envy1=0
# 		values = map(lambda x: problem.std_ranks_min[problem.groups[x][0]], problem.groups.keys())
# 		grp_rank = dict(zip(problem.groups.keys(), values))
# 		values = map(lambda x: sol.topics[problem.groups[x][0]], problem.groups.keys())
# 		grp_sln = dict(zip(problem.groups.keys(), values))
#
#
# 		for g in problem.groups:
# 			max_envy=0
# 			for g1 in problem.groups:
# 				if g1 != g:
# 					if grp_sln[g1] in grp_rank[g]:
# 						envy = max(0,grp_rank[g][grp_sln[g]] - array_ranks[g][grp_sln[g1]])
# 						if (envy > max_envy):
# 							max_envy=envy
# 			tot_env1y += max_envy*len(problem.groups[g])
# 		assert (tot_envy1==tot_envy)
        ############################################################

        # if it passed all previous tests then solution is feasible
        print("feasible solution")
        print("Numb. of students: " + str(len(problem.std_type)))
        print("Numb. of groups: " + str(len(problem.groups)))
        print("Numb. of topics: " + str(len(problem.teams_per_topic)))
        print("\nNumb. of unassigned students: " + str(unass_students))
        print("Numb. of underfull teams: " + str(underfull))
        print("Students assigned outside of their area: ", counter_area)
        print("\nNumb. of unstable: " + str(unstable))
        print("Tot. util: " + str(tot_util))
        print("Tot. envy: " + str(tot_envy))

        log += [len(problem.std_type)]
        log += [nteams]
        log += [len(problem.teams_per_topic)]
        log += [unass_students]
        log += [underfull]
        log += [unstable]
        log += [tot_util]
        log += [tot_envy]

        ############################################
        std_group = {x: y for y in problem.groups for x in problem.groups[y]}
        counter = [0] * (max_rank+1)

        for s in problem.std_values:
            if s in sol.topics:  # used in the paper:  and len(problem.groups[std_group[s]])==3:
                rank = problem.std_ranks_min[s][sol.topics[s]]
                counter[rank] += 1

        s = "\n"
        for i in range(1, max_rank + 1):
            out = str(i) + ". prioritet: " + str(counter[i])
            s = s + out + "\n"
            log += [counter[i]]
        print(s)

        ############################################
        # print({x: [y.team_id for y in item] for x, item in problem.teams_per_topic.items()})
        if soldirname != "":
            filename = "%s/sol_%03d.txt" % (soldirname, k+1)
            with open(filename, "w") as filehandle:
                for s in problem.std_type:
                    if s in sol.topics:
                        filehandle.write(s + "\t" + str(sol.topics[s]) + "\t" + str(problem.teams_per_topic[sol.topics[s]][sol.teams[s]].team_id) + "\n")
                        #if sol.teams[s] == 0 and len(problem.teams_per_topic[sol.topics[s]]) == 1:
                        #    f.write(s + "\t" + str(sol.topics[s]) + "\t" + "" + "\n")
                        #else:
                        #    f.write(s + "\t" + str(sol.topics[s]) +
                        #            "\t" + 'abcdefghi'[sol.teams[s]] + "\n")
            # write the stats of the solution to a json file
            filename = "%s/stat_%03d.json" % (soldirname, k+1)
            stats = {
                "students_num":log[0],
                "students_unass":log[3],
                "students_outside":counter_area,
                "teams_num":log[1],
                "topics_num":log[2],
                "underfull_teams":log[4],
                "num_unstable":log[5],
                "tot_util":log[6],
                "tot_envy":log[7]
            }
            stats["priority"] = {str(i)+". priority":counter[i] for i in range(1, max_rank + 1)}
            with open(filename, "w") as filehandle:
                json.dump(stats,filehandle)
        log += sol.solved
        logs += [log]        
    return logs
