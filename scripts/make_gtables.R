library(googleVis)

priorities <- read.csv("out/popularity.csv",header=TRUE,na.strings="NA",dec=".", sep=";")
#priorities <- priorities[,c(1:5,6:(6+11))]
#names(priorities) <- c("Topic ID","Title","Type","Inst","Preferences in total","1st pr.","2nd pr.","3rd pr.","4th pr.",paste(c(5:12),"th pr.",sep=""))
#names <- c("1st pr.","2nd pr.","3rd pr.","4th pr.")

#library(dplyr)
#priorities <- priorities %>% mutate(Titel=substr(Titel,start=0,stop=30)) %>% filter(Inst %in% c("IMADA")) %>% select(-Type)
#priorities <- priorities[order(priorities["Inst"],-priorities[names[1]],-priorities[names[2]],-priorities[names[3]],-priorities[names[4]]),]




Table <- gvisTable(priorities)
print(Table,file="out/popularity.html")

#plot(Table)


projects <- read.csv("out/projects.csv",header=TRUE,na.strings="NA",dec=".", sep=";")
Table <- gvisTable(projects)
print(Table,file="out/projects.html")

plot(Table)



students <- read.csv("out/students.csv",header=TRUE,na.strings="NA",dec=".", sep=";")
Table <- gvisTable(students)
print(Table,file="out/students.html")

plot(Table)


advisors <- read.csv("out/advisors.csv",header=TRUE,na.strings="NA",dec=".", sep=";")
Table <- gvisTable(advisors)
print(Table,file="out/advisors.html")

plot(Table)