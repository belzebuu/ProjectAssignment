import os
import load_data as ld
from optparse import OptionParser
import pandas as pd 
import os
from collections import OrderedDict
import string
import shutil
import json

usage = "usage: %prog [options] DIRNAME"
parser = OptionParser(usage)
(options, args) = parser.parse_args()  # by default it uses sys.argv[1:]

if not len(args) == 1:
    parser.error("Directory missing")

dirname = args[0]

problem = ld.Problem()

project_details, topics, projects = problem.read_projects(dirname)


src=os.path.join(dirname,"projects.csv")
dst=os.path.join(dirname,"projects.csv.bk")
shutil.copy2(src,dst)

#DF = pd.DataFrame.from_dict(project_details,orient="index")
#DF.to_csv(os.path.join(dirname,"projects.csv.bk"),sep=";",index=False)

""" reads restrictions """
#restrictions = problem.read_restrictions_json(dirname)
with open(dirname+"/restrictions.json", "r") as jsonfile:
    restrictions=json.load(jsonfile)
print({x["username"]:x["groups_max"] for x in restrictions["nteams"]})


OD=OrderedDict()
letters = string.ascii_lowercase[:26]
for topic in topics:
    k = str(topic)+topics[topic][0]   
    if type(project_details[k]["email"]) is str:
        advisor = project_details[k]["email"].split('@')[0]
    else:
        advisor = str(project_details[k]["email"])
    n_teams=0
    for r in restrictions["nteams"]:
        if advisor == r["username"]:
            n_teams = r["groups_max"]
            break
    if n_teams==0:
        print(f"Topic {topic} removed")
    for t in range(n_teams):
        id = str(topic)+letters[t]
        project_details[k]["team"]=letters[t]
        OD[id]=project_details[k].copy()

DF = pd.DataFrame.from_dict(OD,orient="index")
DF.to_csv(os.path.join(dirname,"projects.csv"),sep=";",index=False)