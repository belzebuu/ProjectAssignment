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
```


Work flow in association with valkyrien.imada.sdu.dk/BADM500 Portal
===================================================================

Solve the assignment problem with `src/main.py` and the needed parameters. For
an example, see `Makefile` variable `RUN_FLAGS`. 
Check the options available:
```
python3 src/main.py -h
```
In particular the `-e` option is to distinguish between a `projects.csv` file that already contains the teams or not.
By default the solution is written in `sln`.

To execute:
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

