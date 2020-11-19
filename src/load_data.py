#! /usr/bin/python
# coding=utf-8

import sys
import os
import csv
import json
import codecs
import pandas as pd
from collections import defaultdict
from collections import OrderedDict
from collections import namedtuple


class Problem:
    def __init__(self, dirname):
        self.study_programs = set()
        self.project_details, self.topics, self.projects = self.read_projects(dirname)
        self.student_details, self.priorities, self.groups, self.std_type = self.read_students(
            dirname)
        self.check_tot_capacity()
        self.std_values, self.std_ranks = self.calculate_ranks_values()

        # self.minimax_sol = self.minimax_sol(dirname),
        self.valid_prjtype = self.type_compliance(dirname)
        self.restrictions = self.read_restrictions(dirname)
        self.minimax_sol = 0
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
        # ID;team;title;min_cap;max_cap;type;prj_id;instit;institute;mini;wl
        # OLD: ProjektNr; Underprojek; Projekttitel; Min; Max;Projekttype; ProjektNr  i BB; Institut forkortelse; Obligatorisk minikursus; Gruppeplacering
        project_table = pd.read_csv(dirname+"/projects.csv", sep=";")
        project_table.team = project_table.team.fillna('')
        project_table.instit = project_table.instit.fillna('')
        project_table.prj_id = project_table.prj_id.astype(str)
        project_table.ID = project_table.ID.astype(int)
        project_table.index = project_table["prj_id"]
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

    def read_students(self, dirname):
        students_file = dirname+"/students.csv"
        print("read ", students_file)

        # grp_id;group;username;type;priority_list;student_id;full_name;email;timestamp
        student_table = pd.read_csv(dirname+"/students.csv", sep=";")
        student_table["username"].apply(lambda x: x.lower())
        student_table.index = student_table["username"]
        student_details = student_table.to_dict("index", into=OrderedDict)

        for s in student_details:
            student_details[s]["priority_list"] = [
                int(x.strip()) for x in student_details[s]["priority_list"].split(",")]

        #reader = csv.reader(open(students_file, "r", encoding="utf8"), delimiter=";")

        # student_details = {}
        # # GruppeId; Brugernavn; StudType; Prioteringsliste; Studentnavn;  Email; Tilmeldingstidspunkt
        # for line in reader:
        #     if line[0][0] == "#":
        #         continue
        #     username = line[1].lower()
        #     student_details[username] = dict(
        #         GruppeID=line[0],
        #         Brugernavn=username,
        #         StudType=line[2].lower(),
        #         # Studieretning=line[3].lower(),
        #         PrioriteringsListe=[int(x) for x in line[3].split(",")],
        #         # CprNr=(len(line)>4 and line[4] or ""),
        #         # Fornavne=(len(parts)>4 and parts[5] or ""),
        #         # Efternavn=(len(parts)>4 and parts[6] or ""),
        #         Navn=(len(line) > 4 and line[4] or ""),
        #         Email=(len(line) > 4 and line[5] or ""),
        #         Tilmeldingstidspunkt=(len(line) > 4 and line[6] or "")
        #     )

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
        std_ranks = {}
        for u in self.student_details:
            priorities = self.student_details[u]["priority_list"]

            n = len(priorities)
            i = 7
            j = 1

            values = {}
            ranks = {}
            # print priorities;
            for p in priorities:
                if p not in self.topics:
                    print("WARNING:" + u + " expressed a preference for a project " +
                          str(p)+" which is not available")
                    answer = input(
                        "Continue? (y/n)\n")
                    if answer not in ['', 'Y', 'y']:
                        sys.exit("You decided to stop")
                    else:  # we increse the priorities anyway.
                        j += 1
                        if i > 0:
                            i = i-1
                        continue
                values[p] = 2**i
                ranks[p] = j
                j += 1
                if i > 0:
                    i = i-1

            # if we need to ensure feasibility we can insert a low priority for all other projects
            if prioritize_all:
                prj_set = set(self.project_details.keys()) - set(priorities)
                prj_set = list(prj_set)
                prj_list = random.sample(prj_set, k=len(prj_set))
                for p in prj_list:
                    values[p] = 2**i
                    ranks[p] = j
                    j += 1

            std_values[u] = values
            std_ranks[u] = ranks

        #print(std_ranks)
        return std_values, std_ranks

    def read_restrictions(self, dirname):
        """ reads types """
        reader = csv.reader(open(dirname+"/restrictions.csv", "r"), delimiter=";")
        restrictions = []
        try:
            for row in reader:
                restrictions += [{"cum": int(row[0]), "topics": [int(row[t])
                                                                 for t in range(1, len(row))]}]
        except csv.Error as e:
            sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))
        return restrictions

    def type_compliance(self, dirname):
        """ reads types """
        reader = csv.reader(open(dirname+"/types.csv", "r"), delimiter=";")
        valid_prjtypes = {}
        try:
            for row in reader:
                valid_prjtypes[row[0]] = [row[t] for t in range(1, len(row))]
        except csv.Error as e:
            sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))
            # return {'biologi': ["alle", "natbidat"],"farmaci": ["alle","farmaci"],"natbidat": ["alle","natbidat"]}
        print(valid_prjtypes)
        return valid_prjtypes
