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


Work flow as python module
==========================

Install for editing:
```
pip install -e .
```

```
python3 -m pip freeze
```


Work flow in association with valkyrien.imada.sdu.dk/BADM500 Portal
===================================================================

Solve the assignment problem with `src/__main__.py` and the needed parameters. 

Check the options available:
```
python3 src/adsigno/__main__.py -h
```
In particular, the `-e` option is to distinguish between a `projects.csv` file that already contains the teams or not.

For example:
```
python3 src/adsigno/__main__.py -i -g post -w owa -m 3 -o tmp data/2021-example
python3 src/adsigno/__main__.py -i --groups post --min_preferences 7 -x except /Users/march/workspace/git/TT/apps/adsigno/student_alloc/media/20240304_004053/
```

This writes in the directory `tmp` the directories `sln` and `log` containing the solutions and the log files.

To generate the various kind of reports in `tmp/out`:  
```
python3 src/adsigno/solution_report.py -m 3 -s tmp/sln/sol_001.txt -o tmp data/2021-example
```
To generate even more output for the administration:
```
python3 src/adsigno/solution_report_admin.py -m 3 -s tmp/sln/sol_001.txt -o tmp data/2021-example
```

## 2025 FF501

Data preparation (creation of fictitious requirements.json file), in `ProjectAssignment_gitsdu/data/2025-ff501`:
```
python3 ../scripts/restrictions_ff501.py
```

To solve in `ProjectAssignment_github`:
```
$ python3 adsigno/__main__.py -g post -w owa -i -m 7 /home/marco/workspace/git/EMT/ProjectAssignment_gitsdu/data/2025-ff501 | tee /home/marco/workspace/git/EMT/ProjectAssignment_gitsdu/data/2025-ff501/log.txt
```
and to produce reporting:
```
$p ython3 adsigno/solution_report.py -m 7 -s /home/marco/workspace/git/EMT/ProjectAssignment_gitsdu/data/2025-ff501/sln/sol_001.txt /home/marco/workspace/git/EMT/ProjectAssignment_gitsdu/data/2025-ff501
$ python3 adsigno/solution_report_admin.py -m 7 -s /home/marco/workspace/git/EMT/ProjectAssignment_gitsdu/data/2025-ff501/sln/sol_001.txt /home/marco/workspace/git/EMT/ProjectAssignment_gitsdu/data/2025-ff501
```

## Makefile

### 2025 FF501


```
make ff501
```

The rest below is outdated.

To solve:
```
make run
```
The target `yrun` automatizes an yes answer to all questions.

Next, generate the output in different formats in `out` with:

```
make output
```

Finally, publish online:
```
make publish
```


## Poetry

```
pyenv versions
pyenv install 3.12
pyenv local 3.12.7
poetry env use 3.12
poetry add pandas
poetry add pyYAML
poetry add numpy
poetry add pyscipopt
poetry add gurobipy
o pyproject.toml
poetry shell
poetry install
exit
```