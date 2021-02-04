package unibz.shapes.endpoint;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import org.eclipse.rdf4j.query.BindingSet;
import org.eclipse.rdf4j.query.TupleQueryResult;

import java.time.Duration;
import java.time.Instant;

public class QueryEvaluation {

    private final String queryName;
    private final String queryString;
    private final TupleQueryResult tqr;
    private ImmutableList<BindingSet> bindings;
    private final Instant start;
    private Duration execTime;

    private Integer distinctCardinality;

    QueryEvaluation(String queryId, String queryString, TupleQueryResult tqr, Instant start) {
        this.queryName = queryId;
        this.queryString = queryString;
        this.start = start;
        this.tqr = tqr;
    }

    public int getDistinctCardinality() {
        return distinctCardinality == null ?
                computeDistinctCardinality() :
                distinctCardinality;
    }

    private int computeDistinctCardinality() {
        distinctCardinality = ImmutableSet.copyOf(bindings).size();
        return distinctCardinality;
    }

    public Duration getExecTime() {
        return execTime;
    }

    public ImmutableList<BindingSet> getBindingSets() {
        return bindings;
    }

    public String getQueryName() {
        return queryName;
    }

    public String getQueryString() {
        return queryString;
    }

    public void iterate() {
        ImmutableList.Builder<BindingSet> builder = ImmutableList.builder();
        while (tqr.hasNext()) {
            builder.add(tqr.next());
        }
        execTime = Duration.between(start,Instant.now());
        this.bindings = builder.build();
    }
}
