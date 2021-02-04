package unibz.shapes.eval;

import com.google.common.collect.ImmutableSet;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import unibz.shapes.endpoint.SPARQLEndpoint;
import unibz.shapes.shape.Schema;
import unibz.shapes.shape.impl.SchemaImpl;
import unibz.shapes.shape.preprocess.ShapeParser;
import unibz.shapes.util.StringOutput;
import unibz.shapes.valid.Validation;
import unibz.shapes.valid.result.ResultSet;
import unibz.shapes.valid.result.gui.GUIOutput;
import unibz.shapes.valid.rule.RuleBasedValidation;

import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.util.Optional;

public class EvalGUIJson {

    private static Logger log = LoggerFactory.getLogger(Eval.class);

    public static GUIOutput eval(String schemaString, String endpointUrl) {
        return eval(schemaString, endpointUrl, Optional.empty());
    }

    public static GUIOutput eval(String schemaString, String endpointUrl, String graphName) {
        return eval(schemaString, endpointUrl, Optional.of(graphName));
    }

    private static GUIOutput eval(String schemaString, String endpointUrl, Optional<String> graphName) {
        Schema schema = new SchemaImpl(ImmutableSet.of(ShapeParser.parseJson(schemaString)));
        schema.getShapes()
                .forEach(sh -> sh.computeConstraintQueries(schema, graphName));
        StringOutput validationLog = new StringOutput(), validTargetsLog = new StringOutput(), inValidTargetsLog = new StringOutput(), statsLog = new StringOutput(), tracesLog =  new StringOutput(); //@@
        Validation validation = new RuleBasedValidation(
                new SPARQLEndpoint(endpointUrl),
                schema,
                validationLog,
                validTargetsLog,
                inValidTargetsLog,
                statsLog,
                tracesLog //@@ added for comparing purposes (Trav-SHACL)
        );
        Instant start = Instant.now();
        ResultSet rs;
        try {
            rs = validation.exec();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        Instant finish = Instant.now();
        long elapsed = Duration.between(start, finish).toMillis();
        log.info("Total execution time: " + elapsed);

        return new GUIOutput(rs, validationLog, validTargetsLog, inValidTargetsLog, statsLog, tracesLog); //@@
    }
}
