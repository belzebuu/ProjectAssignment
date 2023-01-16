Project Assignment
==================

This repository contains the software to assign students to
projects. The project is described in:

M. Chiarandini, R. Fagerberg, S. Gualandi (2017). [Handling
preferences in student-project
allocation](https://doi.org/10.1007/s10479-017-2710-1). Annals of
Operations Research.

We assume to have a given a set of project topics each with a subset
of teams available with bounded size, and a set of students with
preferences on the project topics. The task is to create teams of
students to work on the available project topics.

A further side constraint that is not discussed in the article is
included: projects and students belong to a type, for example study
programs, and there are compatibility constraints among types.


We assume that there is a local installation of
[Gurobi](http://www.gurobi.com) and that its module for python is in
the python path of the system.


Data
====

The following files are required:
- projects.csv
- students.csv
- types.csv
- restrictions.[csv|json]


See `data/2021-example` for an example of this input.


Work flow
=========

To find an assignment:
```
python3 src/main.py data/2021-example/ -g post
```
This will output a solution in the directory `sln`.

Check the options available:
```
python3 src/main.py -h
```

To produce different types of reporting:
```
python3 src/report_sol_new.py -d data/2021-example/ -s sln/sol_001.txt
```



Work flow in association with valkyrien.imada.sdu.dk/BADM500 Portal
===================================================================

First, update teams on basis of requirements. Careful it overwrites
projects.csv and eliminates topics if the supervisor has max_groups 0.

```{bash}
python3 src/update_projects.py  ${DATADIR}/${CASE}
# or
make projects
```

then solve the assignment problem with `src/main.py` and the needed parameters. For
an example, see `Makefile` targets `psy` and `badm`. The solution is
written in `sln`.

Next, generate the output in different formats in `out` with:

```
make output
```

Finally, publish online:
```
make publish
```

```
python3 db_tools/update_cap.py Assign/data/2023-badm500/capacities.tsv --commit
python3 db_tools/extract_from_db_psy.py Assign/data/2023-badm500/Assignment/ --exclude
python3 src/update_projects.py /home/marco/workspace/git/flask/Assignment/Assign/data/2023-badm500/Assignment/
python3 src/main.py /home/marco/workspace/git/flask/Assignment/Assign/data/2023-badm500/Assignment/ --Wmethod owa --groups pre --min_preferences 7  | tee /home/marco/workspace/git/flask/Assignment/Assign/data/2023-badm500/Assignment/owa.txt
python3 src/report_sol_new.py -s sln/sol_001.txt ~/workspace/git/flask/Assignment/Assign/data/2023-badm500/Assignment/
python3 src/report_sol.py -s sln/sol_001.txt -d ~/workspace/git/flask/Assignment/Assign/data/2023-badm500/Assignment/
Rscript scripts/make_gtables.R
```
