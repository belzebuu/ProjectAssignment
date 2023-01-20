#! /usr/bin/python3
# coding=utf-8

import sys
#import getopt
import os
import codecs
import string
import csv
import json
import pandas as pd
from collections import defaultdict
from collections import OrderedDict
from load_data import Problem
import functools
import cml_parser

def read_solution(solfile):
    ass_std2team = {}
    ass_team2std = defaultdict(set)
    with open(solfile) as f:
        lines = f.readlines()
    for l in lines:
        l = l.replace("\n", "")
        parts = l.split("\t")
        ass_std2team[parts[0]] = (int(parts[1]), parts[2])
        ass_team2std[parts[1]+parts[2]].add(parts[0])

    print(ass_std2team, ass_team2std)
    return ass_std2team, ass_team2std


def check_sol(ass_std2team, ass_team2std, prob, max_p):  # tablefile=''):
    isok = True
    for s in prob.student_details.keys():
        if s not in ass_std2team:
            isok = False
            print(s+" not assigned!")
        elif ass_std2team[s][0] not in prob.flatten_list_of_lists(prob.priorities[s]): # functools.reduce(lambda x,y: x+y, prob.priorities[s])):
            isok = False
            print(s+" assigned to smth not in his priorities!")

    groups = {i: g for g in prob.groups for i in prob.groups[g]}

    # verify "same group" constraint is satisfied
    for s1 in list(ass_std2team.keys()):
        for s2 in list(ass_std2team.keys()):
            if (groups[s1] == groups[s2]):
                if (ass_std2team[s1][0] != ass_std2team[s2][0] or ass_std2team[s1][1] != ass_std2team[s2][1]):
                    isok = False
                    print(s1, " and ", s2, "not same group:",
                          ass_std2team[s1][0], ass_std2team[s1][1], ass_std2team[s2][0], ass_std2team[s2][1])

    return isok


def project_table(ass_std2team, ass_team2std, popularity, max_p, prob):
    # start reporting

    # Print per project in std
    # and collect student assigned for later output
    output1=os.path.join("out","projects")
    
    filehandle = open(output1+".txt", "w")
    studentassignments = []
    team_details = OrderedDict()
    for i in sorted(prob.teams_per_topic.keys()):
        for team in prob.teams_per_topic[i]:
            pID = str(int(i))+team.team_id
            team_details[pID] = prob.team_details[pID]
            team_details[pID]["popularity_tot"] = sum(popularity[i])
            team_details[pID]["popularity_details"] = str(popularity[i])
            std_assigned = len(ass_team2std[pID]) if pID in ass_team2std else 0
            team_details[pID]["assigned_stds"] = std_assigned
            team_details[pID]["places_left"] = prob.team_details[pID]["max_cap"]-std_assigned
            if (team_details[pID]["places_left"] < 0):
                sys.exit('project %s has places_left %s ' %
                         (pID, team_details[pID]["places_left"]))
            if std_assigned == 0:
                team_details[pID]["team_status"] = "Not used"
            elif prob.team_details[pID]["max_cap"] > std_assigned:
                team_details[pID]["team_status"] = "Underfull"
            else:
                team_details[pID]["team_status"] = "Full"

            team_details[pID]["assigned"] = []
            if (std_assigned > 0):
                if "teachers" in team_details[pID]:
                    filehandle.write("%s: %s (advisors: %s; contact: %s) \n" %
                        (#pID,
                        team_details[pID]["prj_id"],
                        team_details[pID]["title"],
                        team_details[pID]["teachers"],
                        team_details[pID]["email"],
                        )
                        )
                else:
                    filehandle.write("%s: %s\n" %
                        (#pID,
                        team_details[pID]["prj_id"],
                        team_details[pID]["title"]
                        )
                        )
                for sID in sorted(ass_team2std[pID]):
                    team_details[pID]["assigned"].append(sID)
                    filehandle.write("%s, %s, %s\n" %
                             (prob.student_details[sID]["email"],
                              # prob.student_details[sID]["Efternavn"],
                              prob.student_details[sID]["full_name"],
                              prob.student_details[sID]["priority_list"]))
                filehandle.write("\n")
            team_details[pID]["assigned"] = ", ".join(team_details[pID]["assigned"])
    filehandle.close()

    with codecs.open(output1+".json",  "w", "utf-8") as filehandle:
        json.dump(team_details, fp=filehandle, sort_keys=True,
                  indent=4, separators=(',', ': '),  ensure_ascii=False)
    # "prj_id"
    columns = ["ID","team","title","teachers","email","type","instit","mini","wl","popularity_tot","popularity_details",
                "min_cap","max_cap","assigned_stds","places_left","team_status","assigned"]
    table = pd.DataFrame.from_dict(team_details, orient='index', columns=columns)
    table.to_csv(output1+".csv", sep=";",index=False)


def student_table(ass_std2team, ass_team2std, prob):
    # Now output to a file the info per student
    # output:
    outfile = os.path.join("out", "students")
  
    student_details=OrderedDict()
    for g in prob.groups.keys():
        for s in prob.groups[g]:
            student_details[s]=(prob.student_details[s]).copy()
            student_details[s]["topic_assigned"]=ass_std2team[s][0]
            student_details[s]["team_assigned"]=ass_std2team[s][1] #"".join(map(str, ass_std2team[s]) )            
            student_details[s]["priority_assigned"]=prob.std_ranks_min[s][ass_std2team[s][0]]
  
    with codecs.open(outfile+".json",  "w", "utf-8") as filehandle:
        json.dump(student_details, fp=filehandle, sort_keys=True,
                  indent=4, separators=(',', ': '),  ensure_ascii=False)
  
    table = pd.DataFrame.from_dict(student_details, orient='index')
    table.to_csv(outfile+".csv", sep=";",index=False,columns=["username","type","stype","grp_id","topic_assigned","team_assigned","priority_assigned","priority_list_wties"])

    #filehandle = open(outfile+".csv", "w")
    #filehandle.close()


def summarize(ass_std2team, ass_team2std, max_p, prob):
    # Now summarise
    # in std output

    count_teams = 0
    count_prj = 0

    wload_topic = {}
    for i in sorted(prob.teams_per_topic.keys()):
        prj = 0
        std_topic = 0
        teams = 0
        for team in prob.teams_per_topic[i]:
            pID = str(int(i))+team.team_id
            std_assigned = len(ass_team2std[pID]) if pID in ass_team2std else 0
            if std_assigned > 0:
                teams += 1
                std_topic += std_assigned
                count_teams += 1
                prj = 1
        count_prj += prj
        wload_topic[i] = (teams, std_topic)

    counter = [0]*max_p
    unprioritized = 0
    unassigned = 0

    for s in prob.student_details.keys():
        if s not in ass_std2team:
            unassigned = unassigned+1
            continue
        if ass_std2team[s][0] in prob.flatten_list_of_lists(prob.priorities[s]): #functools.reduce(lambda x,y: x+y, prob.priorities[s])):
            for i in range(len(prob.priorities[s])):
                if ass_std2team[s][0] in prob.priorities[s][i]:
                    counter[i] += 1
                    break
        else:
            unprioritized += 1

    s = "\n\nNumb. of students: "+str(len(prob.student_details))
    s = s+"\nNumb. of active topics/topics offered: "+str(count_prj)+"/"+str(len(prob.teams_per_topic))
    s = s+"\nNumb. of active teams/teams offered: " + \
        str(count_teams)+"/"+str(len(prob.team_details))
    s = s+"\nStudents unassigned: "+str(unassigned)
    s = s+"\nStudents assigned outside of preference: "+str(unprioritized)+"\n"
    for i in range(max_p):
        out = str(i+1)+". priority: students "+str(counter[i])
        s = s+out+"\n"

    print(s)
    print("{Topic: (n_teams, n_stds)}")
    print(wload_topic)
    outfile = os.path.join("out", "summary.txt")
    f = open(outfile, "w")
    f.write(s)
    f.close()


def count_popularity(prob):
    outfile = os.path.join("out", "popularity")
    
    popularity = {}
    max_p = 0
    students = list(prob.student_details.keys())
    for s in students:
        if (len(prob.priorities[s]) > max_p):
            max_p = len(prob.priorities[s])
    for i in sorted(prob.teams_per_topic.keys()):
        popularity[i] = [0]*(max_p)
    for s in students:
        for i in range(len(prob.priorities[s])):
            for pId in prob.priorities[s][i]:
                if pId not in prob.teams_per_topic.keys():
                    continue  # pId = int(prob.priorities[s][i])            
                popularity[pId][i] += 1
    
    topic_popularity=OrderedDict()
    for item in sorted(popularity.items(), key = lambda x: x[1][0], reverse=True ):
        i = item[0]
        pID = str(i)+prob.teams_per_topic[i][0].team_id
        topic_popularity[i] = (prob.team_details[pID]).copy()
        for j in range(max_p):
            topic_popularity[i][str(j+1)+". prio."]=popularity[i][j]
        topic_popularity[i]["tot_popularity"]=sum(popularity[i])

    table = pd.DataFrame.from_dict(topic_popularity, orient='index')
    columns = ["title","type","instit","tot_popularity"]+[str(j+1)+". prio." for j in range(max_p)]
    table.to_csv(outfile+".csv", sep=";",index=True,index_label="ID",columns=columns)

    return popularity, max_p

def advisor_table(ass_std2team, ass_team2std, problem):
    outfile = os.path.join("out", "advisors")
    print(ass_std2team)
    print(ass_team2std)
    
    for _, rest in problem.advisors.items():
        groups=0
        stds=0
        for topic in rest["topics"]:
            if topic in problem.teams_per_topic:
                for team in problem.teams_per_topic[topic]:
                    team_id = str(topic)+team.team_id
                    if team_id in ass_team2std:
                        groups+=1
                        stds+=len(ass_team2std[team_id])
        #rest["full_name"]=problem.advisors[rest["username"]]["full_name"] if rest["username"] in problem.advisors else ""
        rest["assigned_groups"]=groups
        rest["capacity_left_grps"]=rest["groups_max"]-groups
        rest["assigned_stds"]=stds
        rest["capacity_left_stds"]=rest["capacity_max"]-stds

    advisors_dict = {k: problem.advisors[k] for k in problem.advisors}
    table = pd.DataFrame.from_dict(advisors_dict, orient='index')
    print(table)
    columns = ["full_name", "groups_min", "groups_max", "assigned_groups", "capacity_left_grps", 
                "capacity_min", "capacity_max", "assigned_stds", "capacity_left_stds"]
    table[columns].to_csv(outfile+".csv", sep=";",index=True,index_label="username")#,columns=columns)
    
    raise SystemExit

def main(argv):
    options, dirname = cml_parser.cml_parse()
    
    problem = Problem(dirname,options)
    ass_std2team, ass_team2std = read_solution(options.solution_file)    
    S = set(ass_team2std.keys()) - set(problem.team_details.keys())
    
    if len(S) > 0:
        if options.allow_unassigned:
            N = max(problem.teams_per_topic.keys())
            for t in S:
                problem.add_fake_project(N+1)
            problem.recalculate_ranks_values()
            print(problem.team_details)
        else:
            raise SystemExit("Some team assigned not among those available")
    
    popularity, max_p = count_popularity(problem)
    if not check_sol(ass_std2team, ass_team2std, problem, max_p):
        print("WARNING: Solution infeasible")
    project_table(ass_std2team, ass_team2std, popularity, max_p, problem)
    # institute_wise()
    student_table(ass_std2team, ass_team2std, problem)
    advisor_table(ass_std2team, ass_team2std, problem)
    summarize(ass_std2team, ass_team2std, max_p, problem)


def usage():
    print("Check sol and writes three output files\n")
    print("Usage: [\"help\", \"dir=\"]\n")
    sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
