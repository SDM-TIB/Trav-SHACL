#' Compute metric dief@t 
#'
#' This function computes the dief@t metric at a point in time t.
#' @param inputtrace dataframe with the answer trace. Attributes of the dataframe: test, approach, answer, time.
#' @param inputtest string that specifies the specific test to analyze from the answer trace.
#' @param t point in time to compute dieft. By default, the function computes the minimum of the execution time among the approaches in the answer trace.
#' @keywords dieft, diefficiency
#' @author Maribel Acosta
#' @import flux
#' @export dieft
#' @seealso diefk, diefk2, plotAnswerTrace
#' @examples 
#' # Compute dief@t when t is the time where the slowest approach produced the last answer.
#' dieft(traces, "Q9.sparql")
#' # Compute dief@t after 7.5 time units (seconds) of execution. 
#' dieft(traces, "Q9.sparql", 7.5) 
dieft <- function(inputtrace, inputtest, t=-1) {
  
  # Initialize output structure.
  test <- NULL
  approach <- NULL
  time <- NULL
  df <- data.frame(test=character(), approach=character(), dieft=double(), stringsAsFactors=TRUE)
  
  # Obtain test and approaches to compare.
  results <- subset(inputtrace, test==inputtest)
  approaches <- unique(results$approach)
  
  # Obtain t per approach. 
  if (t==-1) {
    n <- c()
    for (a in approaches) {
      x <- subset(results, approach==a)
      n <- c(n, x[nrow(x),]$time)
    }
    t<- max(n)
  }
  
  # Compute dieft per approach.
  for (a in approaches) {
    subtrace <- subset(results, approach==a & time<=t)  
    subtrace <- subtrace[, c("time", "answer") ]
    k <- nrow(subtrace)
    if (nrow(subtrace)==1) {
      if (subtrace$answer==0) {
        k <- 0
      }
    }
    com <- data.frame(t, k)
    names(com) <- c("time", "answer")
    subtrace <- rbind(subtrace, com)
    dieft <- 0
    if (nrow(subtrace) > 1) {
      dieft <- flux::auc(subtrace$time, subtrace$answer)
    }
    df <- rbind(df, data.frame("test"=inputtest, "approach"=a, "dieft"=dieft))
  }
  
  return(df)
  
}

#' Compute metric dief@k
#'
#' This function computes the dief@k metric at a given k (number of answers).
#' @param inputtrace dataframe with the answer trace. Attributes of the dataframe: test, approach, answer, time.
#' @param inputtest string that specifies the specific test to analyze from the answer trace.
#' @param k number of answers to compute diefk. By default, the function computes the minimum of the total number of answers produced by the approaches.
#' @keywords diefk, diefficiency
#' @author Maribel Acosta
#' @import flux
#' @export diefk
#' @seealso dieft, diefk2, plotAnswerTrace
#' @examples
#' # Compute dief@k when k is the number of answers produced 
#' # by the approach theat generated the least answers. 
#' diefk(traces, "Q9.sparql") 
#' # Compute dief@k while producing the first k=1000 answers. 
#' diefk(traces, "Q9.sparql", 1000)
diefk <- function(inputtrace, inputtest, k=-1) {
  
  # Initialize output structure.
  test <- NULL
  approach <- NULL
  answer <- NULL
  df <- data.frame(test=character(), approach=character(), diefk=double(), stringsAsFactors=TRUE)
  
  # Obtain test and approaches to compare.
  results <- subset(inputtrace, test==inputtest)
  approaches <- unique(results$approach)
  
  # Obtain k per approach. 
  if (k==-1) {
    n <- c()
    for (a in approaches) {
      x <- subset(results, approach==a)
      n <- c(n, nrow(x))
    }
    k<- min(n)
  }
  
  # Compute diefk per approach.
  for (a in approaches) {
    subtrace <- subset(results, approach==a & answer<=k)  
    diefk <- 0
    if (nrow(subtrace) > 1) {
      diefk <- auc(subtrace$time, subtrace$answer)
    }
    df <- rbind(df, data.frame("test"=inputtest, "approach"=a, "diefk"=diefk))
  }
  
  return(df)
  
}

#' Compute dief@k at a portion of the answer
#'
#' This function computes the dief@k metric at a given kp (portion of answers).
#' @param inputtrace dataframe with the answer trace. Attributes of the dataframe: test, approach, answer, time.
#' @param inputtest string that specifies the specific test to analyze from the answer trace.
#' @param kp portion of answers to compute diefk (between 0.0 and 1.0). By default and when kp=1.0, this function behaves the same as diefk. It computes the kp portion of of minimum of of number of answers  produced by the approaches.
#' @keywords diefk, diefficiency
#' @author Maribel Acosta
#' @export diefk2
#' @seealso dieft, diefk, plotAnswerTrace
#' @examples 
#' # Compute dief@k when the approaches produced 25% of the answers w.r.t. 
#' # the approach that produced the least answers.
#' diefk2(traces, "Q9.sparql", 0.25)
diefk2 <- function(inputtrace, inputtest, kp=-1) {
  
  # Initialize output structure.
  test <- NULL
  approach <- NULL
  df <- data.frame(test=character(), approach=character(), diefk=double(), stringsAsFactors=TRUE)
  
  # Obtain test and approaches to compare.
  results <- subset(inputtrace, test==inputtest)
  approaches <- unique(results$approach)
  
  # Obtain k per approach. 
  n <- c()
  for (a in approaches) {
    x <- subset(results, approach==a)
    n <- c(n, nrow(x))
  }
  k <- min(n) 
  if (kp>-1) {
    k <- k*kp
  }
  
  # Compute diefk.
  df <- diefk(inputtrace, inputtest, k)
  
  return(df)
  
}

#' Plot the answer trace of approaches
#'
#' This function plots the answer trace of the approaches when executing a given test.
#' @param inputtrace dataframe with the answer trace. Attributes of the dataframe: test, approach, answer, time.
#' @param inputtest string that specifies the specific test to analyze from the answer trace.
#' @param colors (optional) list of colors to use for the different approaches.
#' @keywords diefk, diefficiency
#' @author Maribel Acosta
#' @import ggplot2
#' @export plotAnswerTrace
#' @seealso diefk, dieft
#' @examples  
#' plotAnswerTrace(traces, "Q9.sparql")
#' plotAnswerTrace(traces, "Q9.sparql", c("#ECC30B","#D56062","#84BCDA"))
plotAnswerTrace <- function(inputtrace, inputtest, title=inputtest, colors=c("#ECC30B","#D56062","#84BCDA")) {
  
  # Obtain test and approaches to compare.
  test <- NULL
  answer <- NULL
  approach <- NULL
  time <- NULL
  results <- subset(inputtrace, test==inputtest)
  
  # Generate Plot
  resplot <- ggplot(data=results,aes(x=time, y=answer))
  resplot <- resplot + geom_point(aes(colour=approach), size=3)
  resplot <- resplot + ggtitle(title)
  resplot <- resplot + xlab('Time') +  ylab('# Answers Produced')
  resplot <- resplot + theme(
    legend.justification=c(0,1), legend.position=c(0,1),
    legend.text = element_text(size = 16),
    legend.title=element_blank(),
    legend.background = element_rect(fill = 'transparent',  colour = "transparent"),
    axis.text = element_text(colour = "black", size=14),
    axis.title = element_text(colour = "black", size=12),
    panel.background = element_rect(fill = 'white', colour = 'gray'),
    panel.grid.minor = element_blank(),
    panel.grid.major.y = element_blank())
  
  print(resplot + scale_colour_manual(values = colors))
  
}

