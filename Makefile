#DATADIR=data/
#DATADIR=../ProjectAssignment_git_imada/data/
#DATADIR=/home/marco/workspace/git/TT/ProjectAssignment_git_imada/data

HOST=$(shell hostname)

ifeq (${HOST},ADM-131257-Mac)
	DATADIR=/Users/march/workspace/git/flask/Assignment/Assign/data/
else
	DATADIR=/home/marco/workspace/git/flask/Assignment/Assign/data/
endif
DATADIR=/home/marco/workspace/git/TT/ProjectAssignment_git_imada/data

#DATADIR=/home/marco/Teaching/Bachelor/aaskh20/student_alloc/media
#CASE=2021-zhiru
#CASE=2019-bachelor
#CASE=2021-psy
#CASE=2022-badm500
#CASE=2022-ff501-mat
#CASE=2022-ff501
#CASE=2022-psy
CASE=2023-badm500/Assignment
CASE=2022-ff501
CASE=28022023_133345
CASE=2023-ff501


SOLDIR=sln
OUTPUTDIR=out

PROGRAM=python3 src/adsigno/__main__.py
#PROGRAM=python3 -m adsigno 

RUN_FLAGS=-i --Wmethod owa --groups post --min_preferences 7 --cut_off_type stype --cut_off 2 # 2022-psy
RUN_FLAGS=--Wmethod owa --groups pre --min_preferences 6 # 2022-BADM500
RUN_FLAGS=-e --Wmethod owa --groups pre --min_preferences 5 # 2023-BADM500
RUN_FLAGS=-i --groups post --min_preferences 7 # 2022-

OUTPUT_FLAGS=--allow_unassigned --min_preferences 5
OUTPUT_FLAGS=--allow_unassigned --prioritize_all --min_preferences 5
OUTPUT_FLAGS=-e --min_preferences 7
OUTPUT_FLAGS=-g post -w owa -i -m 7

projects: # careful, read README.md before use
	python3 src/update_projects.py  ${DATADIR}/${CASE}


$(SOLDIR):
	mkdir -p sln	

$(OUTPUTDIR):
	mkdir -p sln	



assignment: | $(SOLDIR)
	${PROGRAM} ${DATADIR}/${CASE} -g post


psy: | $(SOLDIR)
	${PROGRAM} ${DATADIR}/${CASE}  | tee ${DATADIR}/${CASE}/log.txt



badm: | $(SOLDIR)
	${PROGRAM} ${DATADIR}/${CASE} | tee ${DATADIR}/${CASE}/log.txt


ff501: $(SOLDIR)
	${PROGRAM} -g post -w owa -i -m 7 ${DATADIR}/${CASE} | tee ${DATADIR}/${CASE}/log.txt


run:
	python3 ${ENTRY} ${RUN_FLAGS} ${DATADIR}/${CASE}  | tee ${DATADIR}/${CASE}/log.txt


yrun:
	yes | python3 ${ENTRY} ${RUN_FLAGS} ${DATADIR}/${CASE}  | tee ${DATADIR}/${CASE}/log.txt
	

output: | $(OUTPUTDIR)
	yes | python3 src/adsigno/report_sol_new.py ${OUTPUT_FLAGS} -s ${SOLDIR}/sol_001.txt ${DATADIR}/${CASE} 
	yes | python3 src/adsigno/report_sol.py ${OUTPUT_FLAGS} -s ${SOLDIR}/sol_001.txt ${DATADIR}/${CASE}
	Rscript scripts/make_gtables.R


publish: 
	#/bin/rm -rf /home/marco/public_html/out/
	#/bin/mkdir -p /home/marco/public_html/out/
	#/bin/cp -rf out /home/marco/public_html/
	#cp -f out/* /home/marco/public_html/ff501-2022/
	#cp -f out/* ~/public_html/BADM500/2023/a/
	cp -f out/* ~/public_html/Teaching/FF501/Ekstern/2023/out
 
install: #editable install
	pip3.8 install -e .


list:
	pip3.8 list


requirements:
	pipreqs .


docker:
	docker run -it --rm -v ${PWD}:/mnt --entrypoint=bash ubuntu:focal
	apt update && apt install python3 python3-pip python3-distro-info python-debian libfuzzy-dev -y
	pip install -U setuptools pip
	python3 -m pip install ssdeep