#! /usr/bin/python3
# coding=utf-8

# Text files required:
# students-enc.txt
# model.tbl
# sol.txt
# projects-quoted.txt
import sys
import getopt
import os
import codecs
import string
import csv
import pandas as pd
from collections import defaultdict
from collections import OrderedDict
from adsigno.load_data import Problem
import functools
from adsigno.solution_report import read_solution, make_popularity, load_all
import adsigno.cml_parser as cml_parser


studieretninger = False
# global constants:
studentfile = "students.txt"
projectfile = "projects.txt"
studentfileseparator = ";"
projectfileseparator = ";"
output4 = "out/output4.csv"
output5 = "out/output5.txt"
# solfile = "./sol.txt"

retning2inst = {'Biologi': "Biologisk Institut",
                "Datalogi": 'Institut for Matematik og Datalogi',
                "Matematik": 'Institut for Matematik og Datalogi',
                'Anvendt Matematik': 'Institut for Matematik og Datalogi',
                "BMB": "Institut for Biokemi og Molekylær Biologi",
                "Biokemi og Molekylær Biologi": "Institut for Biokemi og Molekylær Biologi",
                "Biomedicin": "Institut for Biokemi og Molekylær Biologi",
                "Nanobioscience": "Institut for Fysik, Kemi og Farmaci",
                'Farmaci': "Institut for Fysik, Kemi og Farmaci",
                'Kemi': "Institut for Fysik, Kemi og Farmaci",
                        'Fysik': "Institut for Fysik, Kemi og Farmaci",
                        'NAT': "Placeholder"}

for k in list(retning2inst.keys()):
    retning2inst.update({k.lower(): retning2inst[k]})


# reads the solution
# needs two files:
# model.tbl and sol.txt

# dismissed
def scansol(tablefile):
    maps = {}
    f = open(tablefile)
    lines = f.readlines()
    f.close()
    for l in lines:
        l = l.replace("\"", "")
        l = l.replace("#", "$")
        if l.find("x$") >= 0:
            l = l.replace("\n", "")
            parts = l.split("\t")
            names = parts[3].split("$")
            # print parts,names;
            maps[parts[2].strip()] = [names[1], names[2], names[3]]

    for a in list(maps.keys()):
        ass_team2std[maps[a][1]+maps[a][2]] = set()

    f = open("zpl/sol.txt")
    lines = f.readlines()
    f.close()
    for l in lines:
        l = l.replace("#", "$")
        parts = l.split()
#                print parts;
        ass[maps[parts[0]][0]] = [maps[parts[0]][1], maps[parts[0]][2]]
        ass_team2std[maps[parts[0]][1]+maps[parts[0]][2]].add(maps[parts[0]][0])


def write_txt_4_admin(ass_std2team, ass_team2std, prob, popularity, max_p, out_dir):  # tablefile=''):
    # Print per project in std
    # and collect studnet assigned for later output    
    f1 = open(os.path.join(out_dir, "output1.txt"), "w")
    f2 = open(os.path.join(out_dir, "output2.txt"), "w")
    studentassignments = []
    for i in sorted(prob.teams_per_topic.keys()):
        for team in prob.teams_per_topic[i]:
            pID = str(int(i))+team.team_id.strip()
            s = "ProjectID: "+prob.team_details[pID]["prj_id"]+prob.team_details[pID]["team"]+"\n"
            s = s + "Project title: \""+prob.team_details[pID]["title"]+"\""+"\n"
            s = s + "Popularity: (tot. "+str(popularity[i][0])+") " + \
                str(popularity[i][1:(max_p+1)])+"\n"
            s = s + "Project type: "+prob.team_details[pID]["title"]+"\n"
            s = s + "Min participants: "+str(prob.team_details[pID]["min_cap"])+"\n"
            s = s + "Max participants: "+str(prob.team_details[pID]["max_cap"])+"\n"
            std_assigned = pID in ass_team2std and len(ass_team2std[pID]) or 0
            prob.team_details[pID]["LedigePladser"] = prob.team_details[pID]["max_cap"]-std_assigned
            s = s + "Available places: "+str(prob.team_details[pID]["LedigePladser"])+"\n"
            if (prob.team_details[pID]["LedigePladser"] < 0):
                sys.exit('project %s has LedigePladser %s ' %
                         (pID, prob.team_details[pID]["LedigePladser"]))
            s = s + "Assigned students IDs:"+"\n"
            if std_assigned == 0:
                prob.team_details[pID]["ProjektStatus"] = "Not open"
            elif prob.team_details[pID]["min_cap"] > std_assigned:
                prob.team_details[pID]["ProjektStatus"] = "Underfull"
            else:
                prob.team_details[pID]["ProjektStatus"] = "Not underfull"

            f1.write(s)

            if (std_assigned > 0):
                f2.write("%s: %s\n" %
                         (str(prob.team_details[pID]["ID"])+prob.team_details[pID]["team"],
                          prob.team_details[pID]["title"])
                         )

            if (prob.team_details[pID]["instit"] == "IMADA"):
                print("\n "+str(prob.team_details[pID]["ID"]) +
                      ": "+prob.team_details[pID]["title"])
                print("Popularity: (tot. "+str(popularity[i]
                                               [0])+") "+str(popularity[i][1:(max_p+1)]))

            if std_assigned > 0:
                for sID in sorted(ass_team2std[pID]):
                    f1.write("   "+sID+" "+str(functools.reduce(lambda a,b: a+b, prob.priorities[sID]))+"\n")
                    wishlist = prob.priorities[sID]
                    sType = prob.std_type[sID]
                    f2.write("%s, %s\n" %
                             (prob.student_details[sID]["full_name"],
                              # prob.student_details[sID]["Efternavn"],
                              prob.student_details[sID]["email"]))
                    if (prob.team_details[pID]["instit"] == "IMADA"):
                        print(str(prob.student_details[sID]["full_name"])+" "+prob.student_details[sID]
                              ["email"]+" "+str(functools.reduce(lambda a,b: a+b, prob.student_details[sID]["priority_list"])))
                # studentassignments.append([sID,sType,pID,ptitle,ptype,
                #                                                   underfull,wishlist])
            f1.write("Underfull? ")
            s = prob.team_details[pID]["min_cap"] > std_assigned and "Yes" or "No"
            s += (std_assigned > 0 and " " or " (Not open)")
            f1.write(str(s)+"\n")
            f1.write("\n")
            if (std_assigned > 0):
                f2.write("\n")

    f1.close()
    f2.close()
    return studentassignments
    # sys.exit(0)



def write_csv_per_student_4_admin(studentassignments, ass_std2team, ass_team2std, prob, popularity, max_p, out_dir):  # tablefile=''):
    # Now output to a file the info per student
    #
    # Info is:
    #   StudentID, StudentType, ProjectID, ProjectTitle, ProjectType,
    #   isProjectUnderfull?, wishlistOfStudent

    # put into sID order (as sID is first element of list for each student):
    studentassignments.sort()

    # output:
    output3 = "out/output3.csv"
    f = open(os.path.join(out_dir, "output3.csv"), "w")
    #        for [sID,sType,pID,ptitle,ptype,underfull,wishlist] in studentassignments:
    #                wlist = ",".join(wishlist)
    #                f.write("%s;%s;%s;%s;%s;%s;%s\n" %
    #                                (sID,sType,pID,ptitle,ptype,underfull,wlist))
    #        f.close()
    students = list(prob.student_details.keys())
    for s in students:  # problem.groups.keys():
        prob.student_details[s]["DerfraIkkeTilladt"] = []
        peek = prob.student_details[s]["type"]
        # d={'biologi': ["alle", "natbidat"],"farmaci": ["alle","farmaci"],"natbidat": ["alle","natbidat"]} # which projects for students
        #{x: [y.team_id for y in item] for x, item in problem.teams_per_topic.items()}
        valid_prjs = [x for x in sorted(prob.teams_per_topic.keys()) if prob.teams_per_topic[x][0].type in prob.valid_prjtype[peek]]
        # valid_prjs=filter(lambda x: prob.team_details[str(x)+prob.topics[x][0]]["MinProjektType"]==peek or prob.team_details[str(x)+prob.topics[x][0]]["ProjektType"]=='alle', sorted(prob.topics.keys()))
        # print set(prob.student_details[s]["prob.prioritiesiteringsliste"])
        diff = set(functools.reduce(lambda a,b: a+b, prob.student_details[s]["priority_list"])) - set(valid_prjs)
        if len(diff) > 0:
            tmp = []
            for p in diff:
                tmp.append(p)
            prob.student_details[s]["DerfraIkkeTilladt"] = tmp

    f.write("username;std_type;topic;team;title;prj_type;ProjektStatus;TildeltPrio;priority_list;DerfraIkkeTilladt;min_cap;max_cap;")
    f.write("LedigePladser;full_name;email;grp_id;timestamp;instit;")
    f.write("institute;mini;wl\n")
    students.sort()
    for s in students:
        pID = str(int(ass_std2team[s][0]))+ass_std2team[s][1]
        # print pID;
        #print(prob.student_details[s])
        #print(prob.team_details[pID])
        priolist = prob.student_details[s]["priority_list"]
        valgt = [x for x in range(1, len(priolist)+1) if int(prob.team_details[pID]["ID"]) in priolist[x-1]]
        gottenprio = '%s' % ', '.join(map(str, valgt))
        f.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
                (
                    prob.student_details[s]["username"],
                    prob.student_details[s]["type"],
                    prob.team_details[pID]["prj_id"],
                    prob.team_details[pID]["team"],
                    prob.team_details[pID]["title"],
                    prob.team_details[pID]["type"],
                    prob.team_details[pID]["ProjektStatus"],
                    gottenprio,
                    str(functools.reduce(lambda a,b: a+b,prob.student_details[s]["priority_list"])),
                    prob.student_details[s]["DerfraIkkeTilladt"],
                    prob.team_details[pID]["min_cap"],
                    prob.team_details[pID]["max_cap"],
                    prob.team_details[pID]["LedigePladser"],
                    # prob.team_details[pID]["ProjektNrBB"],
                    # prob.student_details[s]["CprNr"],
                    # prob.student_details[s]["Fornavne"],
                    prob.student_details[s]["full_name"],
                    prob.student_details[s]["email"],
                    prob.student_details[s]["grp_id"],
                    prob.student_details[s]["timestamp"],
                    prob.team_details[pID]["instit"],
                    prob.team_details[pID]["institute"],
                    prob.team_details[pID]["mini"],
                    # # prob.team_details[pID]["Minikursus_anb"],
                    prob.team_details[pID]["wl"]))
    f.close()




def per_student_old_labels(studentassignments, ass_std2team, ass_team2std, prob, popularity, max_p):  # tablefile=''):
    # Now output to a file the info per student
    #
    # Info is:
    #   StudentID, StudentType, ProjectID, ProjectTitle, ProjectType,
    #   isProjectUnderfull?, wishlistOfStudent

    # put into sID order (as sID is first element of list for each student):
    studentassignments.sort()

    # output:
    f = open(output3, "w")
    #        for [sID,sType,pID,ptitle,ptype,underfull,wishlist] in studentassignments:
    #                wlist = ",".join(wishlist)
    #                f.write("%s;%s;%s;%s;%s;%s;%s\n" %
    #                                (sID,sType,pID,ptitle,ptype,underfull,wlist))
    #        f.close()
    students = list(prob.student_details.keys())
    for s in students:  # problem.groups.keys():
        prob.student_details[s]["DerfraIkkeTilladt"] = []
        peek = prob.student_details[s]["type"]
        # d={'biologi': ["alle", "natbidat"],"farmaci": ["alle","farmaci"],"natbidat": ["alle","natbidat"]} # which projects for students
        valid_prjs = [x for x in sorted(prob.teams_per_topic.keys()) if prob.team_details[str(
            x)+prob.teams_per_topic[x][0]]["type"] in prob.valid_prjtype[peek]]
        # valid_prjs=filter(lambda x: prob.team_details[str(x)+prob.topics[x][0]]["MinProjektType"]==peek or prob.team_details[str(x)+prob.topics[x][0]]["ProjektType"]=='alle', sorted(prob.topics.keys()))
        # print set(prob.student_details[s]["prob.prioritiesiteringsliste"])
        diff = set(functools.reduce(lambda a,b: a+b, prob.student_details[s]["priority_list"])) - set(valid_prjs)
        if len(diff) > 0:
            tmp = []
            for p in diff:
                tmp.append(p)
            prob.student_details[s]["DerfraIkkeTilladt"] = tmp

    f.write("Brugernavn;StudType;ProjektNr;Undergruppe;ProjektTitel;ProjektType;ProjektStatus;TildeltPrio;PrioriteringsListe;DerfraIkkeTilladt;Min;Max;")
    f.write("LedigePladser;Navn;Email;GruppeID;Tilmeldingstidspunkt;Institutforkortelse;")
    f.write("Institut;Minikursus obligatorisk;Gruppeplacering\n")
    students.sort()
    for s in students:
        pID = str(int(ass_std2team[s][0]))+ass_std2team[s][1]
        # print pID;
        #print(prob.student_details[s])
        #print(prob.team_details[pID])
        priolist = prob.student_details[s]["priority_list"]
        valgt = [x for x in range(1, len(priolist)+1) if int(prob.team_details[pID]["ID"]) in priolist[x-1]]
        gottenprio = '%s' % ', '.join(map(str, valgt))
        f.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
                (
                    prob.student_details[s]["username"],
                    prob.student_details[s]["type"],
                    prob.team_details[pID]["prj_id"],
                    prob.team_details[pID]["team"],
                    prob.team_details[pID]["title"],
                    prob.team_details[pID]["type"],
                    prob.team_details[pID]["ProjektStatus"],
                    gottenprio,
                    str(functools.reduce(lambda a,b: a+b,prob.student_details[s]["priority_list"])),
                    prob.student_details[s]["DerfraIkkeTilladt"],
                    prob.team_details[pID]["min_cap"],
                    prob.team_details[pID]["max_cap"],
                    prob.team_details[pID]["LedigePladser"],
                    # prob.team_details[pID]["ProjektNrBB"],
                    # prob.student_details[s]["CprNr"],
                    # prob.student_details[s]["Fornavne"],
                    prob.student_details[s]["full_name"],
                    prob.student_details[s]["email"],
                    prob.student_details[s]["grp_id"],
                    prob.student_details[s]["timestamp"],
                    prob.team_details[pID]["instit"],
                    prob.team_details[pID]["institute"],
                    prob.team_details[pID]["mini"],
                    # # prob.team_details[pID]["Minikursus_anb"],
                    prob.team_details[pID]["wl"]))
    f.close()



def per_student_old(ass_std2team, ass_team2std, prob, popularity, max_p):  # tablefile=''):
    # Now output to a file the info per student
    #
    # Info is:
    #   StudentID, StudentType, ProjectID, ProjectTitle, ProjectType,
    #   isProjectUnderfull?, wishlistOfStudent

    # put into sID order (as sID is first element of list for each student):
    studentassignments.sort()

    # output:
    f = open(output3, "w")
    #        for [sID,sType,pID,ptitle,ptype,underfull,wishlist] in studentassignments:
    #                wlist = ",".join(wishlist)
    #                f.write("%s;%s;%s;%s;%s;%s;%s\n" %
    #                                (sID,sType,pID,ptitle,ptype,underfull,wlist))
    #        f.close()

    for s in students:  # problem.groups.keys():
        prob.student_details[s]["DerfraIkkeTilladt"] = []
        peek = prob.student_details[s]["type"]
        # d={'biologi': ["alle", "natbidat"],"farmaci": ["alle","farmaci"],"natbidat": ["alle","natbidat"]} # which projects for students
        valid_prjs = [x for x in sorted(prob.teams_per_topic.keys()) if prob.team_details[str(
            x)+prob.teams_per_topic[x][0]]["type"] in prob.valid_prjtype[peek]]
        # valid_prjs=filter(lambda x: prob.team_details[str(x)+prob.topics[x][0]]["MinProjektType"]==peek or prob.team_details[str(x)+prob.topics[x][0]]["ProjektType"]=='alle', sorted(prob.topics.keys()))
        # print set(prob.student_details[s]["prob.prioritiesiteringsliste"])
        diff = set(prob.student_details[s]["PrioriteringsListe"]) - set(valid_prjs)
        if len(diff) > 0:
            tmp = []
            for p in diff:
                tmp.append(p)
            prob.student_details[s]["DerfraIkkeTilladt"] = tmp

    f.write("Brugernavn;StudType;ProjektNr;Undergruppe;ProjektTitel;ProjektType;ProjektStatus;TildeltPrio;PrioriteringsListe;DerfraIkkeTilladt;Min;Max;")
    f.write("LedigePladser;Navn;Email;GruppeID;Tilmeldingstidspunkt;Institutforkortelse;")
    f.write("Institut;Minikursus obligatorisk;Gruppeplacering\n")
    students.sort()
    for s in students:
        pID = str(int(ass_std2team[s][0]))+ass_std2team[s][1]
        # print pID;
        priolist = prob.student_details[s]["priority_list"]
        valgt = [x for x in range(1, len(priolist)+1) if int(priolist[x-1])
                 == int(prob.team_details[pID]["ProjektNr"])]
        gottenprio = '%s' % ', '.join(map(str, valgt))
        f.write("%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s\n" %
                (
                    prob.student_details[s]["Brugernavn"],
                    prob.student_details[s]["StudType"],
                    prob.team_details[pID]["ProjektNr"],
                    prob.team_details[pID]["Undergruppe"],
                    prob.team_details[pID]["ProjektTitle"],
                    prob.team_details[pID]["ProjektType"],
                    prob.team_details[pID]["ProjektStatus"],
                    gottenprio,
                    str(prob.student_details[s]["PrioriteringsListe"]),
                    prob.student_details[s]["DerfraIkkeTilladt"],
                    prob.team_details[pID]["Min"],
                    prob.team_details[pID]["Max"],
                    prob.team_details[pID]["LedigePladser"],
                    # prob.team_details[pID]["ProjektNrBB"],
                    # prob.student_details[s]["CprNr"],
                    # prob.student_details[s]["Fornavne"],
                    prob.student_details[s]["Navn"],
                    prob.student_details[s]["Email"],
                    prob.student_details[s]["GruppeID"],
                    prob.student_details[s]["Tilmeldingstidspunkt"],
                    prob.team_details[pID]["InstitutForkortelse"],
                    # prob.team_details[pID]["Institut"],
                    prob.team_details[pID]["Minikursus_obl"],
                    # # prob.team_details[pID]["Minikursus_anb"],
                    prob.team_details[pID]["Gruppeplacering"]))
    f.close()


def count_popularity_old(prob):
    f = open(output4, "w")
    popularity = {}
    max_p = 0
    students = list(prob.student_details.keys())
    for s in students:
        if (len(prob.priorities[s]) > max_p):
            max_p = len(prob.priorities[s])
    for i in sorted(prob.teams_per_topic.keys()):
        popularity[i] = [0]*(max_p+1)
    for s in students:
        for i in range(len(prob.priorities[s])):
            pId = prob.priorities[s][i]
            if pId not in prob.teams_per_topic:
                continue  # pId = int(prob.priorities[s][i])
            popularity[pId][0] += 1
            popularity[pId][i+1] += 1
    for i in sorted(prob.teams_per_topic.keys()):
        pID = str(int(i))+prob.teams_per_topic[i][0]
        f.write(str(i)+";\""+prob.team_details[pID]["title"]+"\";")
        f.write(prob.team_details[pID]["type"]+";" +
                prob.team_details[pID]["instit"]+";")
        for j in range(0, (max_p+1)):
            f.write(str(popularity[i][j])+";")
        f.write("\n")
    f.close()
    return popularity, max_p


def institute_wise(prob):
    f = open(output5, "w")
    pIDs_per_institute = {}
    pIDs = []
    for i in sorted(prob.teams_per_topic.keys()):
        for team in prob.teams_per_topic[i]:
            pIDs += [str(int(i))+team.team_id]

    institutes = set([prob.team_details[x]["Institut"] for x in pIDs])
    # print institutes
    pIDs_per_institute = {i: [x for x in pIDs if prob.team_details[x]
                              ["Institut"] == i] for i in institutes}
    topics_per_institute = {i: [x for x in sorted(prob.teams_per_topic.keys()) if prob.team_details[str(
        x)+prob.teams_per_topic[x][0]]["Institut"] == i] for i in institutes}
    print(pIDs_per_institute)
    print(topics_per_institute)

    for i in sorted(institutes):
        tot_per_institute = 0
        istr = "\n"+"["+i+"] "
        tmp = istr
        f.write("##########################################################################################\n")
        for pID in pIDs_per_institute[i]:
            std_assigned = pID in ass_team2std and len(ass_team2std[pID]) or 0
            if std_assigned > 0:
                s = istr+prob.team_details[pID]["ProjektNrBB"] + \
                    ": "+prob.team_details[pID]["ProjektTitle"]
                # # print "Popularity: (tot. "+str(popularity[i][0])+") "+str(popularity[i][1:(max_p+1)]);
                f.write(s+"\n")
                assigned = 0
                for sID in sorted(ass_team2std[pID]):
                    s = str(prob.student_details[sID]["Brugernavn"])+" " + \
                        str(prob.student_details[sID]["prob.prioritiesiteringsListe"])
                    # f.write(s+"\n")
                    assigned = assigned+1
                    if i != retning2inst[prob.student_details[sID]["Studieretning"]]:
                        tmp += "\nX\t"+sID+" "+pID+" "+prob.student_details[sID]["Studieretning"]
                f.write("Std assigned: "+str(assigned)+"\n")
                tot_per_institute = tot_per_institute+assigned
        f.write(istr + "Tot std assigned: "+str(tot_per_institute)+"\n\n")
        print((tmp + " \nTot std assigned: "+str(tot_per_institute)))
    f.close()        #
    print("Written "+output5)

    # 'Institut for Matematik og Datalogi': [2, 3, 15, 28, 52, 58, 62, 68, 72, 77, 80, 92],
    #del topics_per_institute['Institut for Matematik og Datalogi']
    #topics_per_institute['IMADA Mat'] = [27, 86, 52, 4, 63, 71, 31, 55, 13, 92]
    #topics_per_institute['IMADA Dat'] = [15, 78, 95, 1, 81, 26, 40, 12, 17, 14, 77, 60]
    fields = set([prob.student_details[s]["Studieretning"] for s in prob.student_details])
    # fields=topics_per_institute.keys()
    print(topics_per_institute)
    shorten = {"Biologisk Institut": "Biologi",
               "IMADA Dat": "IMADA-Dat",
               "IMADA Mat": "IMADA-Mat",
               "Institut for Biokemi og Molekylær Biologi": "BMB",
               "Institut for Fysik, Kemi og Farmaci": "FKF",
               "Institut for Sundhedstjenesteforskning": "Sund"}
    students_per_institute = {}

    matrix = {r: {c: 0 for c in list(topics_per_institute.keys())} for r in fields}
    # print(matrix)
    for s in prob.student_details:
        # print prob.student_details[s]["prob.prioritiesiteringsliste"][:3]
        shared = {}
        lshared = {}
        for i in sorted(topics_per_institute.keys()):
            shared[i] = [v for v in topics_per_institute[i]
                         if v in prob.student_details[s]["prob.prioritiesiteringsListe"][:5]]
            lshared[i] = len(shared[i])
            # print s+" "+', '.join(map(str,shared[i]))+" "+i
            # print s+" "+str(len(shared[i]))+" "+i
        m = max([len(shared[x]) for x in shared])
        std_retning = prob.student_details[s]["Studieretning"] if "Studieretning" in prob.student_details[s] else filter(
            lambda x: len(shared[x]) == m, fields)[0]
        # print m,std_retning
        for k in topics_per_institute:
            matrix[std_retning][k] = matrix[std_retning][k]+lshared[k]
        students_per_institute.update({std_retning: {s: lshared}})
    # print students_per_institute
    print(matrix)
    # print map(lambda k: ', '.join(map(lambda x : str(matrix[k][x]), matrix.keys())) ,  matrix.keys())
    f = open("www/data/pref.csv", "w")
    f.write("From,To,count\n")
    for k in fields:
        for c in list(topics_per_institute.keys()):
            # print '\"'+shorten[k]+'\",\"'+shorten[c]+'\",'+str(matrix[k][c])
            f.write('\"'+k+'\",\"'+shorten[c]+'\",'+str(matrix[k][c])+"\n")
    f.close()

    stds_per_retning = {
        f: len([s for s in prob.student_details if prob.student_details[s]["Studieretning"] == f]) for f in fields}
    print(stds_per_retning)


def solution_report_4_admin(options):    
    problem, ass_std2team, ass_team2std, out_dir = load_all(options)
    
    popularity, max_p = make_popularity(problem)
    studentassignments = write_txt_4_admin(ass_std2team, ass_team2std, problem, popularity, max_p, out_dir)  # tablefile)
    write_csv_per_student_4_admin(studentassignments, ass_std2team, ass_team2std, problem, popularity, max_p, out_dir)  
    #institute_wise(problem)




if __name__ == "__main__":
    options = cml_parser.cml_parse()
    solution_report_4_admin(options)
