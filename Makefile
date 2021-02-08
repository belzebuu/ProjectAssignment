#DATADIR=data/
DATADIR=../ProjectAssignment_git_imada/data/
CASE=2021-zhiru
#CASE=2019-bachelor
PROGRAM=python3


assignment:
	python3 src/main.py ${DATADIR}/${CASE} -g post

output:
	python3 src/report_sol_new.py -d ${DATADIR}/${CASE} -s sln/sol_001.txt







publish: 
	/bin/rm -rf /home/marco/WWWpublic/Teaching/FF501/Ekstern/${CASE}/out
	#/bin/mkdir /home/marco/WWWpublic/Teaching/FF501/Ekstern/${YEAR}
	/bin/cp -rf out /home/marco/WWWpublic/Teaching/FF501/Ekstern/${CASE}/



# owa"; do # "powers"  "identity"
psy:
	${PROGRAM} src/main.py -d data/2018-psy -m minimax_instab_weighted -W owa | tee res/2018-psy-owa-minimax_instab_weighted.txt; done
