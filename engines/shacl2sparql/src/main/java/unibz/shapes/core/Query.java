package unibz.shapes.core;


import java.util.Arrays;
import java.util.stream.Collectors;

public class Query {

    private final RulePattern rulePattern;
    private final String sparql;
    private final String id;


    public Query(String id, RulePattern rulePattern, String sparql) {
        this.rulePattern = rulePattern;
        this.sparql = sparql;
        this.id = id;
    }

    public RulePattern getRulePattern() {
        return rulePattern;
    }

    public String getSparql() {
        return sparql;
    }

    public String getId() {
        return id;
    }

    public String asSubQuery(){
        return Arrays.stream(sparql.split("\n"))
                .filter(l -> !l.contains("PREFIX"))
                .collect(Collectors.joining("\n"))
                .replace("SELECT *", "SELECT distinct(?x)");
    }
}
