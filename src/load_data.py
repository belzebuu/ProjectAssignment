#! /usr/bin/python
# coding=utf-8

import sys
import os
import csv
import json
import codecs
from numpy import std
import pandas as pd
from collections import defaultdict
from collections import OrderedDict
from collections import namedtuple
import random

random.seed(3)

class Problem:

    def __init__(self):
        return


    def __init__(self, dirname=None, options=None):
        if dirname is None and options is None:
            return
        self.cml_options = options
        self.study_programs = set()
        self.project_details, self.topics, self.projects = self.read_projects(dirname)
        self.student_details, self.priorities, self.groups, self.std_type = self.read_students(dirname)
        self.check_tot_capacity()
        
        self.std_values, self.std_ranks_av, self.std_ranks_min = self.calculate_ranks_values(prioritize_all=self.cml_options.prioritize_all)
        
        # self.minimax_sol = self.minimax_sol(dirname),
        self.valid_prjtype = self.type_compliance(dirname)
        
        self.restrictions = self.read_restrictions(dirname)
        self.minimax_sol = 0
        self.check_capacity(options.groups=="pre")
        print("Read instance... Done")
        # self.__dict__.update(kwds)

    def program_transform(self, program):
        # study_programs = ["anvendt matematik", "biokemi og molekylær biologi", "biologi", "biomedicin", "datalogi", "farmaci","fysik","kemi", "matematik", "psychology"]
        program = program.lower()
        self.study_programs.add(program)
        # if program not in study_programs:
        #    sys.exit("program not recognized: {}".format(program))
        return program

    def read_projects(self, dirname):
        projects_file = dirname+"/projects.csv"
        print("read ", projects_file)
        
        topics = defaultdict(list)
        # We assume header to be:
        # ID;team;title;min_cap;max_cap;type;prj_id;instit;institute;mini;wl;teachers;email
        # NEW: ProjektNr; Underprojek; Projekttitel; Min; Max;Projekttype; ProjektNr  i BB; Institut forkortelse; Institutnavn; Obligatorisk minikursus; Gruppeplacering
        # OLD: ProjektNr; Underprojek; Projekttitel; Min; Max;Projekttype; ProjektNr  i BB; Institut forkortelse; Obligatorisk minikursus; Gruppeplacering
        project_table = pd.read_csv(dirname+"/projects.csv", sep=";")
        print(project_table)
        project_table.team = project_table.team.fillna('')
        project_table.instit = project_table.instit.fillna('')
        project_table.prj_id = project_table.prj_id.astype(str)
        project_table.ID = project_table.ID.astype(int)
        project_table.index = project_table["ID"].astype(str)+project_table["team"].astype(str) # project_table["prj_id"]
        project_details = project_table.to_dict("index", into=OrderedDict)
        # topics = {x: list(map(lambda p: p["team"], project_details[x])) for x in project_details}
        topics = {k: list(v) for k, v in project_table.groupby('ID')['team']}

        # OrderedDict(
        # ProjektNr=row[],
        # Undergruppe=line[1],
        # ProjektTitle=line[2].strip("\r\n\""),
        # Min=int(line[3]),
        # Max=int(line[4]),
        # ProjektType=line[5].lower(),
        # MinProjektType=self.program_transform(row["type"]),
        # ProjektNrBB=(len(line)>6 and line[6] or ""),
        # InstitutForkortelse=(len(line) > 6 and line[6] or ""),
        # Institut=(len(line)>6 and line[8] or ""),
        # Minikursus_obl=(len(line) > 6 and line[7] or ""),
        # Minikursus_anb=(len(line)==12 and line[10] or ""),
        # Gruppeplacering=(len(line) > 6 and line[8] or "")
        # Gruppeplacering=(((len(line)>6 and len(line)==12) and line[11]) or (len(line)>6 and line[10]) or "") # to take into account format before 2012
        # )

        print(project_table.type.unique())
        filehandle = codecs.open(os.path.join("log", "projects.json"),  "w", "utf-8")
        json.dump(project_details, fp=filehandle, sort_keys=True,
                  indent=4, separators=(',', ': '),  ensure_ascii=False)

        projects = defaultdict(list)
        Team = namedtuple("Team", ("min", "max", "type"))
        for topic in topics:
            for t in topics[topic]:
                _id = str(topic)+t                
                projects[topic].append(Team(project_details[_id]["min_cap"],
                                            project_details[_id]["max_cap"],
                                            project_details[_id]["type"]
                                            )
                                       )
        #print(topics.keys())
        #print(project_details)
        #raise SystemExit
        return (project_details, topics, projects)

    def check_tot_capacity(self):
        capacity = sum([self.project_details[k]["max_cap"] for k in self.project_details])
        n_stds = len(self.student_details)
        if (capacity < n_stds):
            answer = input(
                "Not enough capacity from all projects\nHandle this by including a dummy project with the needed capacity? (y/n)\n")
            if answer in ['Y', 'y']:
                sys.exit("to implement")
                # file.write(str(len(project_dict)+1)+";;1;"+str(n_stds-capacity)+";"+program+"\n")
                #project_dict[len(project_dict)+1] = n_stds-capacity


    def flatten(self, List: list) -> list:
            return [item for sublist in List for item in sublist]

    def read_students(self, dirname):
        students_file = dirname+"/students.csv"
        print("read ", students_file)

        # grp_id;(group);username;type;priority_list;(student_id);full_name;email;timestamp
        # group is not needed
        student_table = pd.read_csv(dirname+"/students.csv", sep=";",  converters={"priority_list":str})
        
        student_table["username"] = student_table["username"].apply(str.lower)
        student_table.index = student_table["username"]
        print(student_table)
        student_details = student_table.to_dict("index", into=OrderedDict)

        #for s in student_details:
        #    student_details[s]["priority_list"] = [
        #        int(x.strip()) for x in student_details[s]["priority_list"].split(",")]
        def handle_tie(part):
            ties = [int(x.strip()) for x in part.split(",")]
            #random.shuffle(ties)
            return [ties]

        def process_string(instring):
            instring=instring.strip(",")
            #print(instring)
            if len(instring)==0:
                return []
            pos_s = instring.find("(")
            if pos_s == -1:
                return [[int(x.strip())] for x in instring.split(",")]
            else:
                pos_e = instring.find(")")
                return process_string(instring[0:pos_s]) + handle_tie(instring[pos_s+1:pos_e]) + process_string(instring[pos_e+1:]) 

        ## Note: we assume a well formed string
        for s in student_details:
            
            student_details[s]["priority_list_wties"]=student_details[s]["priority_list"]
            student_details[s]["priority_list"]=process_string(student_details[s]["priority_list"].strip())

            if len(self.flatten(student_details[s]["priority_list"])) < self.cml_options.min_preferences:
                print("WARNING: "+student_details[s]['username']+f" has less than {self.cml_options.min_preferences} preferences")

            if self.cml_options.cut_off_type is not None and student_details[s]["stype"]==self.cml_options.cut_off_type:
                student_details[s]["priority_list"]=student_details[s]["priority_list"][:self.cml_options.cut_off]
                print("WARNING: updated", student_details[s])

            for t in student_details[s]["priority_list"]:
                for p in t:
                    if p not in self.topics:
                        print("WARNING: " + s + " expressed a preference for a project " + str(p)+" which is not available")
                        answer = input("Continue? (y/n)\n")
                        if answer not in ['', 'Y', 'y']:
                            sys.exit("You decided to stop")
                        #t.remove(p)
                #if len(t)==0:
                #    remove(t)
                    

        #print(json.dumps(student_details,indent=4))

        filehandle = codecs.open(os.path.join("log", "students.json"),  "w", "utf-8")
        json.dump(student_details, fp=filehandle, sort_keys=True,
                  indent=4, separators=(',', ': '),  ensure_ascii=False)

        priorities = {u: student_details[u]["priority_list"] for u in student_details}
        
        tmp = {u: (student_details[u]["grp_id"], student_details[u]["type"])
               for u in student_details}
        group_ids = {student_details[u]["grp_id"] for u in student_details}
        groups = {g: list(
            filter(lambda u: student_details[u]["grp_id"] == g, student_details.keys())) for g in group_ids}

        student_types = {student_details[u]["type"] for u in student_details}
        print(student_types)
        std_type = {u: student_details[u]["type"] for u in student_details}

        return (student_details, priorities, groups, std_type)

    def calculate_ranks_values(self, prioritize_all=False):
        std_values = {}
        std_ranks_av = {}
        std_ranks_min = {}
        for u in self.student_details:
            priorities = self.student_details[u]["priority_list"]

            i = self.cml_options.min_preferences
            j = 1

            values = {}
            ranks_av = {}
            ranks_min = {}
            #print(priorities)
            for p in priorities:
                r = len(p)
                av_exp = sum(range(i-r+1,i+1))/r
                av_rank = sum(range(j,j+r))/r
                for t in p:
                    values[t] = 2**av_exp
                    ranks_av[t] = av_rank
                    ranks_min[t] = j
                j=j+r
                i=max(0,i-r)

            # we handle here also cases of students who did not input a preference list
            # we assign to them a value that is the average value among all available values
            # it should later imply that they get a large enough value as weight
            
            if prioritize_all or len(priorities)==0:
                prj_set = set(self.topics.keys()).difference( set(self.flatten(priorities)) )
                prj_set = list(prj_set)
                if False: # old way decide a random order but it may lead to suboptimal sol
                    prj_list = random.sample(prj_set, k=len(prj_set))
                    for p in prj_list:
                        values[p] = 2**i
                        ranks_av[p] = j
                        ranks_min[p] = j
                        j += 1
                else:
                    print(prj_set)
                    M = self.cml_options.min_preferences+1 # sum(prj_list)/len(prj_list)  # a large enough value
                    for p in prj_set:
                        values[p] = 2**0
                        ranks_av[p] = M
                        ranks_min[p] = M

            std_values[u] = values
            std_ranks_av[u] = ranks_av
            std_ranks_min[u] = ranks_min

        #print(std_ranks,std_values)
        return std_values, std_ranks_av, std_ranks_min
    
    def read_restrictions(self, dirname):
        """ reads restrictions """
        if os.path.exists(dirname+"/restrictions.json"):
            return self.read_restrictions_json(dirname)
        elif os.path.exists(dirname+"/restrictions.csv"):
            return self.read_restrictions_csv(dirname)
        else:
            sys.exit(f"File {dirname}/restrictions.[json|csv] missing\n")
        

    def read_restrictions_json(self, dirname):
        """ reads restrictions """
        with open(dirname+"/restrictions.json", "r") as jsonfile:
            restrictions=json.load(jsonfile)
        print({x["username"]:x["groups_max"] for x in restrictions["nteams"]})
        return restrictions

    def read_restrictions_csv(self, dirname):
        """ reads restrictions """
        reader = csv.reader(open(dirname+"/restrictions.csv", "r"), delimiter=";")
        restrictions = []
        try:
            for row in reader:
                restrictions += [{"cum": int(row[0]), "topics": [int(row[t])
                                                                 for t in range(1, len(row))]}]
        except csv.Error as e:
            sys.exit('file %s, line %d: %s' % ("/restrictions.csv", reader.line_num, e))
        return restrictions

    def type_compliance(self, dirname):
        """ reads types """
        reader = csv.reader(open(dirname+"/types.csv", "r"), delimiter=";")
        valid_prjtypes = {}
        try:
            for row in reader:
                valid_prjtypes[row[0]] = [row[t] for t in range(1, len(row))]
        except csv.Error as e:
            sys.exit('file %s, line %d: %s' % ("/restrictions.csv", reader.line_num, e))
            # return {'biologi': ["alle", "natbidat"],"farmaci": ["alle","farmaci"],"natbidat": ["alle","natbidat"]}
        print(valid_prjtypes)

        ## check
        for s in self.std_type:
            t = self.std_type[s]
            
            valid_prjs =  [x for x in self.topics if self.projects[x][0].type in valid_prjtypes[t]] 
            filtered = list(filter(lambda x: x in self.flatten(self.priorities[s]),  valid_prjs ) )
            if (len(filtered)<=1):
                print( s, valid_prjtypes[t], self.std_type[s], sorted(self.priorities[s])) # prob.std_ranks_av[prob.groups[g][0]])
                print( valid_prjs, filtered, self.priorities) 
                raise SystemError

        return valid_prjtypes

    def check_capacity(self, pre):
        n_stds=len(self.student_details)
        n_groups=len(self.groups)
        teams=0
        for p in self.projects.keys():
            teams += len(self.projects[p])
        print(f"Numer of students: {n_stds}")
        print(f"Teams available: {teams}")
        print(f"Number of groups: {n_groups}")
        if pre:
            assert teams>=n_groups, "No teams enough" 
