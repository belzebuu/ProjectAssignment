#! /usr/bin/python
# coding=utf-8

import sys
import os
import csv
import json
import os
import codecs
import pandas as pd
from collections import defaultdict
from collections import OrderedDict
import adsigno.utils as utils

import itertools
import random
import numpy
import pprint
import adsigno.ravel_topics_1 as ravel_topics_1
import adsigno.ravel_topics_2 as ravel_topics_2
import logging

random.seed(3)


class Problem:
    options: dict

    def __init__(self, options=None, keep_original_priorities=False):
        if options is None and keep_original_priorities is False:
            return 
        if options is None and options.data_dirname is None:
            raise SystemError("Missing info to 'process'.")
        self.options=options
        data_dirname = options.data_dirname
        if not os.path.exists(data_dirname):
            raise SystemError(f"The path '{data_dirname}' does not exist.")
        self.cml_options = options
        self.study_programs = set()

        self.student_details, self.priorities, self.groups, self.std_type = self.read_students(
            data_dirname)
        self.restrictions = self.read_restrictions(data_dirname)
        self.team_details, self.teams_per_topic, self.advisors = self.read_projects(data_dirname)
        #print(self.advisors)
        #print(self.restrictions)
        for k in self.restrictions:
            logging.info(k)
            self.advisors[k["username"].lower()].update(k)
        
        #DF = pd.DataFrame.from_dict(self.team_details,orient="index")
        #print(DF)
        #raise SystemError
        self.valid_prjtype = self.type_compliance(data_dirname)

        self.restrictions = self.tighten_restrictions()
        

        # self.check_tot_capacity()
        try:
            self.check_capacity(options.groups == "pre")
        except utils.MissingCapacity as e:
            if options.allow_unassigned:
                self.add_capacity(options.groups == "pre")
                logging.warning("Missing capacity and but unssiagnments allowed: capacity added and grouping set to 'pre' prior to assignement")
            else:
                logging.warning(e)
                #raise SystemExit

        self.std_values, self.std_ranks_av, self.std_ranks_min = self.calculate_ranks_and_values()
        if not keep_original_priorities:
            self.tighten_student_priorities()

        
        self.write_logs(options.output_dir)
        # self.minimax_sol = self.minimax_sol(data_dirname)
        self.minimax_sol = 0

        logging.info("Read instance... Done")
        # self.__dict__.update(kwds)

    def program_transform(self, program):
        # study_programs = ["anvendt matematik", "biokemi og molekylær biologi", "biologi", "biomedicin", "datalogi", "farmaci","fysik","kemi", "matematik", "psychology"]
        program = program.lower()
        self.study_programs.add(program)
        # if program not in study_programs:
        #    sys.exit("program not recognized: {}".format(program))
        return program


    def read_projects(self, data_dirname):
        '''It must come after restrictions'''
        if self.cml_options.expand_topics:
            topic_details = self.read_topics(data_dirname)
            team_details = ravel_topics_1.expand_topics(topic_details, self.restrictions)
            teams_per_topic, advisors = self.arrange_teams_per_topic(team_details)
        else:
            team_details = self.read_teams(data_dirname)
            teams_per_topic, advisors = self.arrange_teams_per_topic(team_details)
        return team_details, teams_per_topic, advisors




    def read_teams(self, data_dirname):
        '''already expanded topics'''
        projects_file = data_dirname / "projects.csv"
        logging.info("read "+str(projects_file))
        # We assume header to be:
        # ID;team;title;size_min;size_max;type;prj_id;instit;institute;mini;wl;teachers;email
        # NEW: ProjektNr; Underprojek; Projekttitel; Min; Max;Projekttype; ProjektNr  i BB; Institut forkortelse; Institutnavn; Obligatorisk minikursus; Gruppeplacering
        # OLD: ProjektNr; Underprojek; Projekttitel; Min; Max;Projekttype; ProjektNr  i BB; Institut forkortelse; Obligatorisk minikursus; Gruppeplacering
        project_table = pd.read_csv(projects_file, sep=";")
        logging.debug(project_table)
        if "team" in project_table:
            project_table.team = project_table.team.fillna('')
        elif "number_of_teams" in project_table:
            project_table.number_of_teams = project_table.number_of_teams.fillna('')
        else:
            raise("team or number_of_teams missing in topics")
        project_table.instit = project_table.instit.fillna('')
        project_table.advisor_main=project_table.advisor_main.astype(str)
        if "email" in project_table.columns:
            project_table.email = project_table.email.apply(lambda x: str(x).lower())
        else:
            project_table.email = project_table.ID.apply(lambda x: str(x).lower())
        if "proj_id" in project_table.columns:
            project_table.rename(columns={"proj_id":"prj_id"},inplace=True)
        if "prj_id" in project_table:
            project_table.prj_id = project_table.prj_id.astype(str)
        else:
            project_table.prj_id = project_table.ID
    
        project_table.ID = project_table.ID.astype(str)
        project_table.index = project_table["ID"].astype(
            str)+project_table["team"].astype(str)  # project_table["prj_id"]
        team_details = project_table.to_dict("index", into=OrderedDict)
        # topics = {x: list(map(lambda p: p["team"], team_details[x])) for x in team_details}

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

        logging.debug(project_table.type.unique())
        return team_details

    def arrange_teams_per_topic(self, team_details):
        teams_per_topic_short = defaultdict(list)
        for k, v in team_details.items():
            label = v["team"] if len(v["team"])>0 else " "
            teams_per_topic_short[v["ID"]] += list(label) 
            #    k: list(v) for k, v in project_table.groupby('ID')['team']}

        # full_details_dict = {k: v.to_dict("records") for k, v in project_table.groupby("ID")}
        # print(exam_dict)
        #print(teams_per_topic_short)
        
        teams_per_topic = defaultdict(list)
        
        for topic in teams_per_topic_short.keys():
            for t in teams_per_topic_short[topic]:
                _id = str(topic)+t.strip()
                teams_per_topic[topic].append(utils.Team(t,
                                                         team_details[_id]["size_min"],
                                                         team_details[_id]["size_max"],
                                                         team_details[_id]["type"]
                                                         )
                                              )
        
        advisors=dict()
        for _, x in team_details.items(): # doubles should just be overwritten
            advisor_id = x["email"].split("@")[0].strip().lower()
            d={"teams_id": [_]}
            if "teachers" in x:
                d.update( {"full_name": x["teachers"].split(",")[0]} )
            if advisor_id not in advisors:
                advisors[advisor_id] = d
            else:
                advisors[advisor_id]["teams_id"]+=[_]

        #print(team_details.keys())
        #print(teams_per_topic.keys())
        #raise SystemExit
        return dict(teams_per_topic), dict(sorted(advisors.items()))


    def read_topics(self, data_dirname):
        '''Topics to expand in teams'''
        projects_file = data_dirname / "projects.csv"
        logging.info("read " + str(projects_file))
        
        project_table = pd.read_csv(data_dirname / "projects.csv", sep=";")
        logging.debug(project_table)
        if "team" in project_table:
            project_table.team = project_table.team.fillna('')
        elif "number_of_teams" in project_table:
            project_table.number_of_teams = project_table.number_of_teams.fillna('')
        else:
            raise("team or number_of_teams missing in topics")
        project_table.instit = project_table.instit.fillna('')
        project_table.email = project_table.email.apply(lambda x: str(x).lower())
        project_table.ID = project_table.ID.astype(str)
        if "prj_id" in project_table:
            project_table.prj_id = project_table.prj_id.astype(str)
        else:
            project_table.prj_id = project_table.ID
        
        project_table.index = project_table.prj_id.astype(str)# project_table["ID"].astype(str) #+project_table["team"].astype(str)  # project_table["prj_id"]
        
        topic_details = project_table.to_dict("index", into=OrderedDict)
        # topics = {x: list(map(lambda p: p["team"], team_details[x])) for x in team_details}
        logging.debug(project_table.type.unique())
        
        return topic_details

        

    def read_students(self, data_dirname):
        students_file = data_dirname / "students.csv"
        logging.debug("read " + str(students_file))

        # grp_id;(group);username;type;priority_list;(student_id);full_name;email;timestamp
        # group is not needed
        student_table = pd.read_csv(
            data_dirname / "students.csv", sep=";",  converters={"priority_list": str})

        student_table["username"] = student_table["username"].apply(str.lower)
        student_table.index = student_table["username"]
        logging.debug(student_table)
        student_details = student_table.to_dict("index", into=OrderedDict)

        # for s in student_details:
        #    student_details[s]["priority_list"] = [
        #        int(x.strip()) for x in student_details[s]["priority_list"].split(",")]
        def handle_tie(part):
            ties = [x.strip() for x in part.split(",")]
            # random.shuffle(ties)
            return [ties]

        def process_string(instring):
            instring = instring.strip(",")
            # print(instring)
            if len(instring) == 0:
                return []
            pos_s = instring.find("(")
            if pos_s == -1:
                return [[x.strip()] for x in instring.split(",")]
            else:
                pos_e = instring.find(")")
                return process_string(instring[0:pos_s]) + handle_tie(instring[pos_s+1:pos_e]) + process_string(instring[pos_e+1:])

        # Note: we assume a well formed string
        for s in student_details:

            student_details[s]["priority_list_wties"] = student_details[s]["priority_list"]
            student_details[s]["priority_list"] = process_string(
                student_details[s]["priority_list"].strip())
            prj_prioritized = len(utils.flatten_list_of_lists(student_details[s]["priority_list"]))
            if prj_prioritized < self.cml_options.min_preferences:
                logging.warning(f" {prj_prioritized} < {self.cml_options.min_preferences} preferences for "+student_details[s]['username'])
                #raise SystemExit(
                #    "Found a student who declared less priorities than requested. The case needs handling.")

            if self.cml_options.cut_off_type is not None and str(student_details[s]["stype"]) == self.cml_options.cut_off_type:
                # We need to ensure all students have the exact same number of priorities
                # we cut off and if a group of ties exceeds the cut off size, we select
                # remaining at random
                tmp = []
                size = 0
                for _ in student_details[s]["priority_list"]:
                    tmp += [_]
                    size += len(_)
                    if size >= self.cml_options.cut_off:
                        break
                    #if len(_) + size <= self.cml_options.cut_off:
                    #    tmp += [_]
                    #    size += len(_)
                    #elif len(_) + size > self.cml_options.cut_off:
                    #    tmp += [random.choices(_,
                    #                           k=self.cml_options.cut_off - size)]
                    #    break
                    #else:
                    #    break
                # student_details[s]["priority_list"][:self.cml_options.cut_off]
                student_details[s]["priority_list"] = tmp
                logging.warning("updated", student_details[s])

        # print(json.dumps(student_details,indent=4))

        priorities = {u: student_details[u]["priority_list"]
                      for u in student_details}

        tmp = {u: (student_details[u]["grp_id"], student_details[u]["type"])
               for u in student_details}
        group_ids = {student_details[u]["grp_id"] for u in student_details}
        groups = {g: list(
            filter(lambda u: student_details[u]["grp_id"] == g, student_details.keys())) for g in group_ids}

        student_types = {student_details[u]["type"] for u in student_details}
        # print(student_types)
        std_type = {u: student_details[u]["type"] for u in student_details}

        return (student_details, priorities, groups, std_type)


    def write_logs(self,output_dirname):
        log = output_dirname / "log"
        os.makedirs(log, exist_ok=True)
        with codecs.open(os.path.join(log, "projects.json"),  "w", "utf-8") as filehandle:
            json.dump(self.team_details, fp=filehandle, sort_keys=True,
                    indent=4, separators=(',', ': '),  ensure_ascii=False)
        with codecs.open(os.path.join(log, "students.json"),  "w", "utf-8") as filehandle:
            json.dump(self.student_details, fp=filehandle, sort_keys=True,
                    indent=4, separators=(',', ': '),  ensure_ascii=False)
        with codecs.open(os.path.join(log, "ranks.json"),  "w", "utf-8") as filehandle:
            sorted_computed_ranks = {x: sorted(
                self.std_ranks_av[x].items(), key=lambda item: item[1]) for x in self.std_ranks_av}
            json.dump(sorted_computed_ranks, fp=filehandle, sort_keys=True,
                    indent=4, separators=(',', ': '),  ensure_ascii=False)


    def calculate_ranks_and_values(self):
        std_values = {}
        std_ranks_av = {}
        std_ranks_min = {}
        for u in self.student_details:
            priorities = self.student_details[u]["priority_list"]

            # self.cml_options.min_preferences
            i = len(utils.flatten_list_of_lists(priorities))
            j = 1

            values = {}
            ranks_av = {}
            ranks_min = {}
            # print(priorities)
            for p in priorities:
                r = len(p)
                av_exp = sum(range(i-r+1, i+1))/r
                av_rank = sum(range(j, j+r))/r
                for t in p:
                    values[t] = 2**av_exp
                    ranks_av[t] = av_rank
                    ranks_min[t] = j
                j = j+r
                i = max(0, i-r)

            # we handle here also cases of students who did not input a preference list
            # we assign to them a value that is the average value among all available values
            # it should later imply that they get a large enough value as weight

            if self.cml_options.prioritize_all or len(priorities) == 0:
                prj_set = set(self.teams_per_topic.keys()).difference(
                    set(utils.flatten_list_of_lists(priorities)))
                prj_set = list(prj_set)
                if False:  # old way decide a random order but it may lead to suboptimal sol
                    prj_list = random.sample(prj_set, k=len(prj_set))
                    for p in prj_list:
                        values[p] = 2**i
                        ranks_av[p] = j
                        ranks_min[p] = j
                        j += 1
                else:
                    # print(prj_set)
                    # sum(prj_list)/len(prj_list)  # a large enough value
                    M = self.cml_options.min_preferences + 1
                    for p in prj_set:
                        values[p] = 2**0
                        ranks_av[p] = M
                        ranks_min[p] = M

            std_values[u] = values
            std_ranks_av[u] = ranks_av
            std_ranks_min[u] = ranks_min

        # print(std_ranks_av,std_values)
        # pprint.pprint()
        #raise SystemError
        return std_values, std_ranks_av, std_ranks_min

    def recalculate_ranks_values(self) -> None:
        self.std_values, self.std_ranks_av, self.std_ranks_min = self.calculate_ranks_and_values()

    def read_restrictions(self, data_dirname):
        """ reads restrictions """
        restrictions=dict()
        if os.path.exists(data_dirname / "restrictions.json"):
            restrictions = self.read_restrictions_json(data_dirname)
        elif os.path.exists(data_dirname / "restrictions.csv"):
            restrictions = self.read_restrictions_csv(data_dirname)
        else:
            sys.exit(f"File {data_dirname}/restrictions.[json|csv] missing\n")
        for x in restrictions:
            if "teams_min" not in x:
                x["teams_min"]=0
            if "teams_max" not in x:
                x["teams_max"]=float("inf")
            if "students_min" not in x:
                x["students_min"]=0  
            if "students_max" not in x:
                x["students_max"]=float("inf")     
        return restrictions

    def read_restrictions_json(self, data_dirname):
        """ reads restrictions """
        with open(data_dirname / "restrictions.json", "r") as jsonfile:
            restrictions = json.load(jsonfile)
        for r in restrictions["nteams"]:
            r["username"] = r["username"].lower()
        #print({x["username"]: x["teams_max"] for x in restrictions["nteams"]})        
        return restrictions["nteams"] 

    def tighten_restrictions(self):
        # Adjust for topics not available
        processed = []
        for (i, r) in enumerate(self.restrictions):
            topics = [t for t in r["topics"]
                      if t in self.teams_per_topic.keys()]
            if len(topics) != 0:
                r["topics"] = topics
                processed += [r]
        return processed

    def read_restrictions_csv(self, data_dirname):
        """ reads restrictions """
        reader = csv.reader(
            open(data_dirname / "restrictions.csv", "r"), delimiter=";")
        restrictions = []
        try:
            for row in reader:
                restrictions += [{"cum": int(row[0]),
                                  "topics": [int(row[t]) for t in range(1, len(row))]}]

        except csv.Error as e:
            sys.exit('file %s, line %d: %s' %
                     ("/restrictions.csv", reader.line_num, e))
        
        return restrictions

    def type_compliance(self, data_dirname):
        """ reads types """
        reader = csv.reader(open(data_dirname / "types.csv", "r"), delimiter=";")
        valid_prjtypes = {}
        try:
            for row in reader:
                valid_prjtypes[row[0]] = [row[t] for t in range(1, len(row))]
        except csv.Error as e:
            sys.exit('file %s, line %d: %s' %
                     ("/types.csv", reader.line_num, e))
            # return {'biologi': ["alle", "natbidat"],"farmaci": ["alle","farmaci"],"natbidat": ["alle","natbidat"]}
        logging.debug("In students:" + str({x for _,x in self.std_type.items()}))
        logging.debug("In projects:" + str({x["type"] for _,x in self.team_details.items()}))
        logging.debug("In types: " + str(valid_prjtypes))

        # check
        for s in self.std_type:
            t = self.std_type[s]

            valid_prjs = [x for x, item in self.teams_per_topic.items() if item[0].type in valid_prjtypes[t]]
            filtered = list(filter(lambda x: x in utils.flatten_list_of_lists(self.priorities[s]),  valid_prjs))
            if (len(filtered) < 1):
                # prob.std_ranks_av[prob.groups[g][0]])                
                logging.debug(s, self.std_type[s],  valid_prjtypes[t])
                logging.debug(sorted(utils.flatten_list_of_lists(self.priorities[s])), sorted(valid_prjs), filtered) #, self.priorities)
                logging.debug([item[0].type for x, item in self.teams_per_topic.items()])
                logging.debug(self.teams_per_topic.keys())
                #raise utils.TypeComplianceError("Type compliance error: priority list empty after type filtering\n%s" % s)

        return valid_prjtypes

    def add_fake_project(self) -> None:
        """Must occurr before calculating ranks and values"""
        new_id="Unassigned"
        #Team = namedtuple("Team", ("team_id", "min", "max", "type"))
        letters = "abcdefghi"

        # copy the type of the first team
        type = self.teams_per_topic[list(self.teams_per_topic.keys())[0]][0].type

        n=0
        if new_id not in self.teams_per_topic:
            self.teams_per_topic[new_id]=[utils.Team(letters[n], 0, 5, type)]
        else:
            n = len(self.teams_per_topic[new_id]) 
            self.teams_per_topic[new_id].append(utils.Team(letters[n], 0, 5, type))

        _id = str(new_id)+letters[n]
        self.team_details[_id] = {'ID': new_id, 'team': letters[n],
                                  'title': 'Unassigned', 'size_min': 0, 'size_max': 5, 'type': type,
                                  'prj_id': _id, 'instit': 'IMADA', 'institute': 'IMADA', 'mini': numpy.nan, 'wl': numpy.nan,
                                  'teachers': 'Nobody', 'email': 'nobody@sdu.dk'}

        for s in self.priorities:
            if self.cml_options.cut_off_type is not None and str(self.student_details[s]["stype"]) == self.cml_options.cut_off_type:
                continue
            if not any([new_id in x for x in self.priorities[s]]):
                self.priorities[s] += [[new_id]]
        #print(json.dumps(self.priorities,indent=4))
        
        for s in self.student_details:
            if self.cml_options.cut_off_type is not None and str(self.student_details[s]["stype"]) == self.cml_options.cut_off_type:
                continue
            if not any([new_id in x for x in self.student_details[s]["priority_list"]]):
                self.student_details[s]["priority_list"] += [[new_id]]
            # print(self.student_details[s]["priority_list"])

    def add_capacity(self, pre_grouping: bool) -> None:
        """Must occurr before calculating ranks and values"""

        n_stds = len(self.student_details)
        n_groups = len(self.groups)
        n_teams = 0
        for x in self.restrictions:  # self.teams_per_topic.keys():
            n_teams += x["teams_max"]  # len(self.teams_per_topic[p])
        n_places = 0
        for x in self.restrictions:
            n_places += x["students_max"]
        
        if n_stds > n_places:
            missing_places = n_stds - n_places
            topic_nr = max(map(lambda x : int(x), self.teams_per_topic.keys()))+1
            for _ in range(missing_places):
                self.add_fake_project(topic_nr)
        if n_groups > n_teams and pre_grouping:
            missing_teams = n_groups - n_teams + 3
            topic_nr = max(map(lambda x : int(x), self.teams_per_topic.keys()))+1
            for _ in range(missing_teams):
                self.add_fake_project(topic_nr)

    def check_capacity(self, pre_grouping: bool) -> None:
        n_stds = len(self.student_details)
        n_groups = len(self.groups)
        n_teams = 0
        for x in self.restrictions:  # self.teams_per_topic.keys():
            n_teams += x["teams_max"]  # len(self.teams_per_topic[p])
        n_places = 0
        ignore_capacity=False
        for x in self.restrictions:
            if "students_max" in x:
                n_places += x["students_max"] 
            else:
                ignore_capacity=True
        
        logging.info(f"Number of students: {n_stds} on number of places available: {n_places}")
        logging.info(f"Number of student groups: {n_groups} on number of teams available: {n_teams}")
        
        if n_stds > n_places and not ignore_capacity:
            raise utils.MissingCapacity("After restrictions, potential places not enough for all students. Ignore if restictions not globally set.")
        elif n_groups > n_teams and pre_grouping:
            raise utils.MissingCapacity("After restrictions, no teams enough to cover all groups. Ignore if restrictions not globally set.")

    def check_tot_capacity(self) -> None:
        capacity = sum([self.team_details[k]["size_max"]
                       for k in self.team_details])
        n_stds = len(self.student_details)
        if (capacity < n_stds):
            raise utils.MissingCapacity("Not enough capacity from all projects. A possible workaround could be to include a placeholder project with the needed capacity.")
            # file.write(str(len(project_dict)+1)+";;1;"+str(n_stds-capacity)+";"+program+"\n")
            #project_dict[len(project_dict)+1] = n_stds-capacity

    def tighten_student_priorities(self) -> None:
        
        def remove_absent_prj(plist: list):
            for sub_list in plist: #self.student_details[s]["priority_list"]:
                for p in sub_list:
                    if p not in self.teams_per_topic.keys():
                        msg = "WARNING: " + s + " expressed a preference for a project " + str(p)+" which is not available\n<br/>"
                        msg += str(self.student_details[s]["priority_list"])
                        utils.data_issue_continue(msg, self.options.execution_mode)                        
                        logging.warning(self.student_details[s]["priority_list"])
                        sub_list.remove(p)
                        if len(sub_list)==0:
                            self.student_details[s]["priority_list"].remove(sub_list)                        
                        return True                    
            return False

        for s in self.student_details.keys():            
            while remove_absent_prj(self.student_details[s]["priority_list"]):
                pass