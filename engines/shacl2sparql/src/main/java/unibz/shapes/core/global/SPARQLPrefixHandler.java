package unibz.shapes.core.global;

import com.google.common.collect.ImmutableMap;

import java.util.stream.Collectors;

public class SPARQLPrefixHandler {

    private static ImmutableMap<String, String> prefixes = ImmutableMap.<String, String>builder()
            .put("ub", "<http://swat.cse.lehigh.edu/onto/univ-bench.owl#>")
            .put("rdf", "<http://www.w3.org/1999/02/22-rdf-syntax-ns#>")
            .put("dbo", "<http://dbpedia.org/ontology/>")
            .put("dbr", "<http://dbpedia.org/resource/>")
            .put("yago", "<http://dbpedia.org/class/yago/>")
            .put("foaf", "<http://xmlns.com/foaf/0.1/>")
            .put("", "<http://example.org/>")
            .build();

    private static String prefixString = prefixes.entrySet().stream()
            .map(e -> "PREFIX " + e.getKey() + ":" + e.getValue())
            .collect(Collectors.joining("\n"))
            + "\n";

    public static String getPrefixString() {
        return prefixString;
    }
}
