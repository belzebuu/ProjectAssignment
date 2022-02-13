#DATADIR=data/
#DATADIR=../ProjectAssignment_git_imada/data/
DATADIR=/home/marco/workspace/git/TT/ProjectAssignment_git_imada/data
#CASE=2021-zhiru
#CASE=2019-bachelor
#CASE=2021-psy
#CASE=2022-badm500
CASE=2022-ff501-mat

PROGRAM=python3
SOLDIR=sln
OUTPUTDIR=out



projects: # careful, read README.md before use
	python3 src/update_projects.py  ${DATADIR}/${CASE}


$(SOLDIR):
	mkdir -p sln	


assignment: | $(SOLDIR)
	python3 src/main.py ${DATADIR}/${CASE} -g post


psy: | $(SOLDIR)
	${PROGRAM} src/main.py ${DATADIR}/${CASE} -i --Wmethod owa --groups post --min_preferences 7 --cut_off_type stype --cut_off 2 | tee ${DATADIR}/${CASE}/owa.txt



badm: | $(SOLDIR)
	${PROGRAM} src/main.py ${DATADIR}/${CASE} --Wmethod owa --groups pre --min_preferences 6  | tee ${DATADIR}/${CASE}/owa.txt




$(OUTPUTDIR):
	mkdir -p sln	


output: | $(OUTPUTDIR)
	python3 src/report_sol_new.py -s ${SOLDIR}/sol_001.txt ${DATADIR}/${CASE} 
	Rscript scripts/make_gtables.R

publish: 
	#/bin/rm -rf /home/marco/public_html/out/
	#/bin/mkdir -p /home/marco/public_html/out/
	#/bin/cp -rf out /home/marco/public_html/
	cp -f out/*html /home/marco/public_html/out/




