#' Compares dief@t with other benchmark metrics as in <doi:10.1007/978-3-319-68204-4_1>
#'
#' This function repeats the results reported in "Experiment 1" in Acosta, M., Vidal, M. E., & Sure-Vetter, Y. (2017) <doi:10.1007/978-3-319-68204-4_1>.
#' Experiment 1 compares the performance of querying approaches when using metrics defined in the literature (total execution time, time for the first tuple, throughput, and completeness) and the metric dieft@t.
#' @param traces dataframe with the result of the traces. The structure of this dataframe is as follows: "test,approach,tuple,time".
#' @param metrics dataframe with the result of the other metrics. The structure of this dataframe is as follows: "test,approach,tfft,totaltime,comp".
#' @keywords dieft, diefficiency
#' @author Maribel Acosta
#' @import utils
#' @export experiment1
#' @seealso experiment2, dieft
#' @examples 
#' # To fully reproduce the experiments download the full files and load them using read.csv:
#' # traces is available at <https://figshare.com/files/9625852>
#' # metrics is available at <https://figshare.com/files/9660316>
#' results1 <- experiment1(traces, metrics)
experiment1 <- function(traces, metrics) {
  
  # Compute further metrics: throughput, inverse of execution time, inverse of time for the first tuple.
  metrics$throughput <- with(metrics, metrics$comp/metrics$totaltime)
  metrics$invtfft <- with(metrics, 1/metrics$tfft)
  metrics$invtotaltime <- with(metrics, 1/metrics$totaltime)
  
  # Obtain queries.
  queries <- unique(traces$test)
  
  # Compute dieft.
  dieftDF <- data.frame(test=character(), approach=character(), dieft=double(), stringsAsFactors=TRUE)
  for (q in queries) {
    print(c("Computing dieft for all approaches for test ", q))
    dieftDF <- rbind(dieftDF, dieft(traces, q))
  }
  
  # Merge conventional metrics and dieft into a single dataframe.
  allmetrics <- merge(metrics, dieftDF)
  
  
  return(allmetrics)
}

#' Generate radar plots that compare dief@t with other benchmark metrics in a specific test as in <doi:10.1007/978-3-319-68204-4_1>
#'
#' This function plots the results reported for a single given test in "Experiment 1" in Acosta, M., Vidal, M. E., & Sure-Vetter, Y. (2017) <doi:10.1007/978-3-319-68204-4_1>.
#' Experiment 1 compares the performance of querying approaches when using metrics defined in the literature (total execution time, time for the first tuple, throughput, and completeness) and the metric dieft@t.
#' @keywords dieft, diefficiency
#' @author Maribel Acosta
#' @param  allmetrics dataframe with the results of all the metrics in Experiment 1. 
#' @param  q id of the selected test to plot. 
#' @param  colors (optional) list of colors to use for the different approaches.
#' @import graphics
#' @export plotExperiment1Test
#' @seealso experiment1, plotExperiment1
#' @examples 
#' results1 <- experiment1(traces, metrics)
#' plotExperiment1Test(results1, "Q9.sparql")
#' plotExperiment1Test(results1, "Q9.sparql", c("#ECC30B","#D56062","#84BCDA"))
plotExperiment1Test <- function(allmetrics, q, title=q, colors=c("#ECC30B","#D56062","#84BCDA")) {
  
  # Plot metrics using spider plot. 
  test <- NULL
  keeps <- c("invtfft", "invtotaltime", "comp", "throughput", "dieft") 
  
  data <- subset(allmetrics, test==q) 
  approaches <- c(data["approach"])[[1]]
  data <- data[keeps]
  
  maxs <- data.frame(invtfft=max(data$invtfft), invtotaltime=max(data$invtotaltime), comp=max(data$comp), throughput=max(data$throughput), dieft=max(data$dieft))
  mins <- data.frame(invtfft=0, invtotaltime=0, comp=0, throughput=0, dieft=0)
  
  data <- rbind(maxs, mins ,data)
  
  colors_border=colors
  colors_in=alpha(colors_border, 0.15)
  
  radarchart( data, 
              pcol=colors_border , pfcol=colors_in, plwd=4 , plty=1,
              cglcol="grey", cglty=1, axislabcol="grey", cglwd=1.0,
              vlcex=1.5,
              title=title,
              vlabels=c("(TFFF)^-1", "(ET)^-1", "Comp", "T", "dief@t"))
  
  legend(x=-1.5, y=1.3, legend=approaches, bty = "n", pch=20 , col=colors_border , text.col = "black", cex=1.3, pt.cex=2.5)  
  
}

#' Generate radar plots that compare dief@t with other benchmark metrics in all tests as in <doi:10.1007/978-3-319-68204-4_1>
#'
#' This function plots the results reported in Experiment 1 in Acosta, M., Vidal, M. E., & Sure-Vetter, Y. (2017) <doi:10.1007/978-3-319-68204-4_1>.
#' Experiment 1 compares the performance of querying approaches when using metrics defined in the literature (total execution time, time for the first tuple, throughput, and completeness) and the metric dieft@t.
#' @param  allmetrics dataframe with the result of all the metrics in Experiment 1. 
#' @param  colors (optional) list of colors to use for the different approaches.
#' @keywords diefk, diefficiency
#' @author Maribel Acosta
#' @import fmsb
#' @import ggplot2
#' @export plotExperiment1
#' @seealso experiment1, diefk2
#' results1 <- experiment1(traces, metrics)
#' plotExperiment1(results1)
#' plotExperiment1(results1, c("#ECC30B","#D56062","#84BCDA"))
plotExperiment1 <- function(allmetrics, colors=c("#ECC30B","#D56062","#84BCDA")) {
  
  # Obtain queries.
  queries <- unique(allmetrics$test)
  
  # Plot the metrics for each test in Experiment 1.  
  for (q in queries) {
    plotExperiment1Test(allmetrics, q, colors)  
  }
}  

#' Compares dief@k at different answer portions as in <doi:10.1007/978-3-319-68204-4_1>
#'
#' This function repeats the results reported in Experiment 2 in Acosta, M., Vidal, M. E., & Sure-Vetter, Y. (2017) <doi:10.1007/978-3-319-68204-4_1>.
#' "Experiment 2" measures the continuous efficiency of approaches when producing the first 25%, 50%, 75%, and 100% of the answers. 
#' @param traces dataframe with the result of the traces. The structure of this dataframe is as follows: "test,approach,tuple,time".
#' @keywords diefk, diefficiency
#' @author Maribel Acosta
#' @import plyr
#' @import utils
#' @export experiment2
#' @seealso experiment1, diefk2
#' @examples 
#' # To fully reproduce the experiments download the full file and load it using read.csv:
#' # traces is available at <https://figshare.com/files/9625852>
#' results2 <- experiment2(traces)
experiment2 <- function(traces) {
  
  # Obtain queries.
  queries <- unique(traces$test)
  
  # Compute diefk for different k%: 25, 50, 75, 100.
  diefkDF <- data.frame(test=character(), approach=character(), "diefk25"=double(), "diefk50"=double(), "diefk75"=double(), "diefk100"=double())
  keeps <- c("diefk25", "diefk50", "diefk75", "diefk100")
  for (q in queries) {
     
      print(c("Computing diefk for all approaches for test ", q))
      
      k25DF <- diefk2(traces, q, 0.25)
      k25DF <- plyr::rename(k25DF, c("diefk"="diefk25"))
      
      k50DF <- diefk2(traces, q, 0.50)
      k50DF <- plyr::rename(k50DF, c("diefk"="diefk50"))
      
      k75DF <- diefk2(traces, q, 0.75)
      k75DF <- plyr::rename(k75DF, c("diefk"="diefk75"))
      
      k100DF <- diefk2(traces, q, 1.00)
      k100DF <- plyr::rename(k100DF, c("diefk"="diefk100"))
      
      
      x <- cbind(k25DF, k50DF, k75DF, k100DF)
      diefkDF <- rbind(diefkDF, x)
      
  }
  
  return(diefkDF)
  
}

#' Generate radar plots that compare dief@k at different answer completeness in a specific test as in  <doi:10.1007/978-3-319-68204-4_1>
#'
#' This function plots the results reported for a single given test in "Experiment 2" in Acosta, M., Vidal, M. E., & Sure-Vetter, Y. (2017) <doi:10.1007/978-3-319-68204-4_1>.
#' "Experiment 2" measures the continuous efficiency of approaches when producing the first 25%, 50%, 75%, and 100% of the answers. 
#' @keywords diefk, diefficiency
#' @author Maribel Acosta
#' @param  diefkDF dataframe resulting from Experiment 2.
#' @param  q id of the selected test to plot. 
#' @param  colors (optional) list of colors to use for the different approaches.
#' @import fmsb
#' @import ggplot2
#' @import graphics
#' @export plotExperiment2Test
#' @seealso experiment2, plotExperiment2
#' @examples 
#' results2 <- experiment2(traces)
#' plotExperiment2Test(results2, "Q9.sparql")
#' plotExperiment2Test(results2, "Q9.sparql", c("#ECC30B","#D56062","#84BCDA"))
plotExperiment2Test <- function(diefkDF, q, colors=c("#ECC30B","#D56062","#84BCDA")) {
  
  # Plot metrics using spider plot.
  test <- NULL
  approaches <- unique(diefkDF["approach"])[[1]]
  keeps <- c("diefk25", "diefk50", "diefk75", "diefk100")
  
  x <- subset(diefkDF, test==q)
  x <- x[keeps]
  
  maxs <- data.frame(diefk25=max(x$diefk25), diefk50=max(x$diefk50), diefk75=max(x$diefk75), diefk100=max(x$diefk100))
  mins <- data.frame(diefk25=0, diefk50=0,  diefk75=0, diefk100=0)
  
  data <- rbind(maxs, mins, x)
  
  colors_border=colors
  colors_in=alpha(colors_border, 0.15)
  radarchart( data, 
              pcol=colors_border , pfcol=colors_in, plwd=4 , plty=1,
              cglcol="grey", cglty=1, axislabcol="grey", cglwd=1.0,
              vlcex=1.5,
              title=q,
              vlabels=c("k=25%", "k=50%", "k=75%", "k=100%"))
  legend(x=-1.5, y=1.3, legend=approaches, bty = "n", pch=20 , col=colors_border , text.col = "black", cex=1.3, pt.cex=2.5)

}

#' Generate radar plots that compare dief@k at different answer completeness in all tests as in  <doi:10.1007/978-3-319-68204-4_1>
#'
#' This function plots the results reported in Experiment 2 in Acosta, M., Vidal, M. E., & Sure-Vetter, Y. (2017) <doi:10.1007/978-3-319-68204-4_1>.
#' "Experiment 2" measures the continuous efficiency of approaches when producing the first 25%, 50%, 75%, and 100% of the answers. 
#' @keywords diefk, diefficiency
#' @author Maribel Acosta
#' @param  diefkDF dataframe with the results of Experiment 2. 
#' @param  colors (optional) list of colors to use for the different approaches.
#' @export plotExperiment2
#' @seealso experiment2, diefk2
#' @examples 
#' results2 <- experiment2(traces)
#' plotExperiment2(results2)
#' plotExperiment2(results2, c("#ECC30B","#D56062","#84BCDA"))
plotExperiment2 <- function(diefkDF, colors=c("#ECC30B","#D56062","#84BCDA")) {
  
  # Obtain queries.
  queries <- unique(diefkDF$test)
  
  # Plot the metrics for each test in Experiment 2.  
  for (q in queries) {
    plotExperiment2Test(diefkDF, q, colors)  
  }
}  

