#DATADIR=data/
#DATADIR=../ProjectAssignment_git_imada/data/
DATADIR=/home/marco/workspace/git/TT/ProjectAssignment_git_imada/data
#CASE=2021-zhiru
#CASE=2019-bachelor
#CASE=2021-psy
CASE=2022-badm500
PROGRAM=python3


assignment:
	python3 src/main.py ${DATADIR}/${CASE} -g post

output:
	python3 src/report_sol_new.py -s sln/sol_001.txt ${DATADIR}/${CASE} 







publish: 
	/bin/rm -rf /home/marco/WWWpublic/Teaching/FF501/Ekstern/${CASE}/out
	#/bin/mkdir /home/marco/WWWpublic/Teaching/FF501/Ekstern/${YEAR}
	/bin/cp -rf out /home/marco/WWWpublic/Teaching/FF501/Ekstern/${CASE}/





# owa"; do # "powers"  "identity"
psy:
	${PROGRAM} src/main.py ${DATADIR}/${CASE} -i --Wmethod owa --groups post --min_preferences 7 --cut_off_type stype --cut_off 2 | tee ${DATADIR}/${CASE}/owa.txt


badm:
	${PROGRAM} src/main.py ${DATADIR}/${CASE} --Wmethod owa --groups pre --min_preferences 6  | tee ${DATADIR}/${CASE}/owa.txt
