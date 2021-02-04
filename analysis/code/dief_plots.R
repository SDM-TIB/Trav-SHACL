library(ggplot2)
library(fmsb)
library(flux)

source("dief.R")
source("reproduceExperiments.R")

run_all <- function() {
    datasets = c("SKGs",
                "MKGs",
                "LKGs")
    
    sizes = c("schema1", "schema2", "schema3")
    
    for(i in 1:length(datasets)) {
        ds <- datasets[i]
        for(i in 1:length(sizes)) {
            traces <- read.csv(url(paste("file:///results/dief_data/",sizes[i],"/traces/all_",ds,".csv",sep='')))
            
            jpeg(paste("/results/plots/traces/traces_",sizes[i],"_",ds,".jpg",sep=''))
            plotAnswerTrace(traces, ds, paste(switch(sizes[i], schema1={"Shape Schema 1"}, schema2={"Shape Schema 2"}, schema3={"Shape Schema 3"}),ds))
            dev.off()
        
            metrics <- read.csv(url(paste("file:///results/dief_data/",sizes[i],"/metrics/",ds,".csv",sep='')))
            
            dieft(traces, ds)
            exp1 <- experiment1(traces, metrics)
            jpeg(paste("/results/plots/dieft/dieft_",sizes[i],"_",ds,".jpg",sep=''))
            plotExperiment1Test(exp1, ds, paste(switch(sizes[i], schema1={"Shape Schema 1"}, schema2={"Shape Schema 2"}, schema3={"Shape Schema 3"}),ds))
            dev.off()
        }
    }
}

run_all()

