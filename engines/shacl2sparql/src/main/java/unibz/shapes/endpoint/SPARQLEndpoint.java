package unibz.shapes.endpoint;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import org.eclipse.rdf4j.query.QueryLanguage;
import org.eclipse.rdf4j.query.TupleQuery;
import org.eclipse.rdf4j.repository.Repository;
import org.eclipse.rdf4j.repository.RepositoryConnection;
import org.eclipse.rdf4j.repository.sparql.SPARQLRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import unibz.shapes.core.Query;
import unibz.shapes.util.ImmutableCollectors;

import java.time.Instant;

public class SPARQLEndpoint {


    private static Logger log = LoggerFactory.getLogger(SPARQLEndpoint.class);
    private final String endPointURL;

    public SPARQLEndpoint(String endPointURL) {
        this.endPointURL = endPointURL;
    }

    public ImmutableList<QueryEvaluation> runQueries(ImmutableSet<Query> queries) {

        ImmutableList<QueryEvaluation> evals;
        Repository repo = new SPARQLRepository(endPointURL);
        repo.initialize();

        try (RepositoryConnection conn = repo.getConnection()) {
            evals = queries.stream()
                    .map(q -> runQuery(conn, q.getId(), q.getSparql()))
                    .collect(ImmutableCollectors.toList());
        }
        repo.shutDown();
        return evals;
    }

    public QueryEvaluation runQuery(String queryId, String queryString) {
        Repository repo = new SPARQLRepository(endPointURL);
        repo.initialize();

        try (RepositoryConnection conn = repo.getConnection()) {
            QueryEvaluation eval = runQuery(conn, queryId, queryString);
            repo.shutDown();
            return eval;
        }
    }

    private QueryEvaluation runQuery(RepositoryConnection conn, String queryId, String queryString) {
        log.debug("Evaluating query:\n" + queryString);

        TupleQuery tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString);
        Instant start = Instant.now();
        QueryEvaluation eval = new QueryEvaluation(queryId, queryString, tupleQuery.evaluate(), start);
        eval.iterate();
        return eval;
    }

    public String getURL() {
        return endPointURL;
    }
}
