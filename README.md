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




Work Flow
=========

To find an assignment:
```
python3 src/main.py data/2021-example/ -g post
```
To produce different types of reporting:
```
python3 src/report_sol_new.py -d data/2021-example/ -s sln/sol_001.txt
```
