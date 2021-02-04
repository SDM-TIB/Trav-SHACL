package unibz.shapes.shape.preprocess;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.apache.commons.io.FileUtils;
import unibz.shapes.core.global.SPARQLPrefixHandler;
import unibz.shapes.endpoint.SPARQLEndpoint;
import unibz.shapes.shape.*;
import unibz.shapes.shape.impl.*;
import unibz.shapes.util.ImmutableCollectors;
import unibz.shapes.util.StreamUt;

import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Collection;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ShapeParser {

    private static Logger log = LoggerFactory.getLogger(ShapeParser.class);
    static boolean includeSPARQLPrefixes = true;
    public enum Format {
        JSON,
        SHACL
    }

    public static boolean isURL(String urlString)
    {
        try
        {
            java.net.URL url = new java.net.URL(urlString);
            url.toURI();
            return true;
        } catch (Exception exception)
        {
            return false;
        }
    }

    /*public static boolean isURL(String url) {
        try {
            (new java.net.URL(url)).openStream().close();
            return true;
        } catch (Exception ex) { }
        return false;
    }*/

    public static Schema parseSchemaFromDir(Path dir, Format shapeFormat) {
        String fileExtension = getFileExtension(shapeFormat);
        switch (shapeFormat) {
            case JSON:
                return new SchemaImpl(
                        FileUtils.listFiles(
                                dir.toFile(),
                                new String[]{fileExtension},
                                false
                        ).stream()
                                .map(f -> parseJson(Paths.get(f.getAbsolutePath())))
                                .collect(ImmutableCollectors.toSet())
                );
//            case SHACL:
//                return parseSchemaFromString(
//                        concatenateTtlShapesDefs(
//                                FileUtils.listFiles(
//                                        dir.toFile(),
//                                        new String[]{fileExtension},
//                                        false
//                                )),
//                        shapeFormat
//                );
            default:
                throw new RuntimeException("Unexpected format: " + shapeFormat);
        }
    }

    public static String concatenateTtlShapesDefs(Collection<File> files) {
        return files.stream()
                .flatMap(ShapeParser::getPrefixDeclarations)
                .distinct()
                .collect(Collectors.joining("\n"))
                + "\n" +
                files.stream()
                        .map(ShapeParser::getShapeDeclaration)
                        .collect(Collectors.joining("\n"));
    }

    private static Stream<String> getPrefixDeclarations(File f) {
        try {
            return Files.lines(Paths.get(f.getAbsolutePath()))
                    .filter(l -> l.contains("@prefix"));
        } catch (IOException e) {
            throw new RuntimeException("cannot read file : " + f.getAbsolutePath(), e);
        }
    }

    private static String getShapeDeclaration(File f) {
        try {
            return Files.lines(Paths.get(f.getAbsolutePath()))
                    .filter(l -> !l.contains("@prefix"))
                    .collect(Collectors.joining("\n"));
        } catch (IOException e) {
            throw new RuntimeException("cannot read file : " + f.getAbsolutePath(), e);
        }
    }

    private static String getFileExtension(Format shapeFormat) {
        switch (shapeFormat) {
//            case SHACL:
//                return "ttl";
            case JSON:
                return "json";
        }
        throw new RuntimeException("Unexpected format: " + shapeFormat);
    }


    public static Schema parseSchemaFromString(String s, Format shapeFormat) {
////        JenaSystem.init();
//        // Avoids a bug when exporting the project as a single jar
//        org.apache.jena.query.ARQ.init();
//
//        if (shapeFormat == Format.SHACL)
//            return Parser.parse(s);
        throw new RuntimeException("Unexpected schema format : " + shapeFormat);
    }

    private static Shape parseJson(Path path) {
        Optional<String> targetQuery = Optional.empty();
        try {
            JsonObject obj = new JsonParser().parse(new FileReader(path.toFile())).getAsJsonObject();
            JsonElement targetDef = obj.get("targetDef");
            String name = obj.get("name").getAsString();
            ImmutableSet<ConstraintConjunction> parsedConstraints = parseConstraints(name, obj.get("constraintDef").getAsJsonObject().get("conjunctions").getAsJsonArray());

            if (targetDef != null) {
                JsonElement query = targetDef.getAsJsonObject().get("query");
                if (query != null) {
                    if (includeSPARQLPrefixes) {
                        targetQuery = Optional.of(SPARQLPrefixHandler.getPrefixString() + query.getAsString() + " ORDER BY ?x");
                    } else {
                        targetQuery = Optional.of(query.getAsString() + " ORDER BY ?x");
                    }

                }
            }

            return new ShapeImpl(
                    name,
                    targetQuery,
                    parsedConstraints,
                    includeSPARQLPrefixes
            );

        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    public static Shape parseJson(String jsonString) {
        Optional<String> targetQuery = Optional.empty();
        JsonObject obj = new JsonParser().parse(jsonString).getAsJsonObject();
        JsonElement targetDef = obj.get("targetDef");
        String name = obj.get("name").getAsString();
        ImmutableSet<ConstraintConjunction> parsedConstraints = parseConstraints(name, obj.get("constraintDef").getAsJsonObject().get("conjunctions").getAsJsonArray());

        if (targetDef != null) {
            JsonElement query = targetDef.getAsJsonObject().get("query");
            if (query != null) {
                if (includeSPARQLPrefixes) {
                    targetQuery = Optional.of(SPARQLPrefixHandler.getPrefixString() + query.getAsString());
                } else {
                    targetQuery = Optional.of(query.getAsString());
                }
            }
        }

        return new ShapeImpl(
                name,
                targetQuery,
                parsedConstraints,
                includeSPARQLPrefixes
        );
    }

    private static ImmutableSet<ConstraintConjunction> parseConstraints(String shapeName, JsonArray array) {
        AtomicInteger i = new AtomicInteger(0);
        return StreamUt.toStream(array.iterator()).sequential()
                .map(JsonElement::getAsJsonArray)
                .map(a -> parseDisjunct(a, shapeName + "_d" + i.incrementAndGet()))
                .collect(ImmutableCollectors.toSet());
    }

    private static ConstraintConjunction parseDisjunct(JsonArray array, String id) {

        AtomicInteger i = new AtomicInteger(0);
        ImmutableList<AtomicConstraint> constraints = StreamUt.toStream(array.iterator())
                .map(JsonElement::getAsJsonObject)
                .map(a -> parseConstraint(a, id + "_c" + i.incrementAndGet()))
                // Duplicate the constraints that have both min and max
                .flatMap(ShapeParser::duplicate)
                .collect(ImmutableCollectors.toList());

        return new ConstraintConjunctionImpl(
                id,
                constraints.stream()
                        .filter(c -> c instanceof MinOnlyConstraint)
                        .map(c -> (MinOnlyConstraint) c)
                        .collect(ImmutableCollectors.toList()),
                constraints.stream()
                        .filter(c -> c instanceof MaxOnlyConstraint)
                        .map(c -> (MaxOnlyConstraint) c)
                        .collect(ImmutableCollectors.toList()),
                constraints.stream()
                        .filter(c -> c instanceof LocalConstraint)
                        .map(c -> (LocalConstraint) c)
                        .collect(ImmutableCollectors.toList())
        );
    }

    private static Stream<AtomicConstraint> duplicate(AtomicConstraint c) {
        if (c instanceof MinAndMaxConstraint) {
            MinAndMaxConstraint cc = (MinAndMaxConstraint) c;
            return Stream.of(
                    new MinOnlyConstraintImpl(cc.getId() + "_1", cc.getPath(), cc.getMin(), cc.getDatatype(), cc.getValue(), cc.getShapeRef(), cc.isPos()),
                    new MaxOnlyConstraintImpl(cc.getId() + "_2", cc.getPath(), cc.getMax(), cc.getDatatype(), cc.getValue(), cc.getShapeRef(), cc.isPos())
            );
        }
        return Stream.of(c);
    }

    private static AtomicConstraint parseConstraint(JsonObject obj, String id) {

        JsonElement min = obj.get("min");
        JsonElement max = obj.get("max");
        JsonElement shapeRef = obj.get("shape");
        JsonElement datatype = obj.get("datatype");
        JsonElement value = obj.get("value");
        JsonElement path = obj.get("path");
        JsonElement negated = obj.get("negated");

        Optional<Integer> oMin = (min == null) ?
                Optional.empty() :
                Optional.of(min.getAsInt());
        Optional<Integer> oMax = (max == null) ?
                Optional.empty() :
                Optional.of(max.getAsInt());
        Optional<String> oShapeRef = (shapeRef == null) ?
                Optional.empty() :
                Optional.of(shapeRef.getAsString());
        Optional<String> oDatatype = (datatype == null) ?
                Optional.empty() :
                Optional.of(datatype.getAsString());
        Optional<String> oValue = (value == null) ?
                Optional.empty() :
                Optional.of(value.getAsString());
        Optional<String> oPath = (path == null) ?
                Optional.empty() :
                Optional.of(path.getAsString());
        boolean oNeg = (negated == null) ?
                true :
                !negated.getAsBoolean();

        if (oPath.isPresent()) {
            String pathstr = oPath.get();
            if (isURL(pathstr)) {
                pathstr = "<" + pathstr + ">";
                includeSPARQLPrefixes = false;
            }
            if (oMin.isPresent()) {
                if (oMax.isPresent()) {
                    return new MinAndMaxConstraintImpl(id, pathstr, oMin.get(), oMax.get(), oDatatype, oValue, oShapeRef, oNeg);
                }
                return new MinOnlyConstraintImpl(id, pathstr, oMin.get(), oDatatype, oValue, oShapeRef, oNeg);
            }
            if (oMax.isPresent()) {
                return new MaxOnlyConstraintImpl(id, pathstr, oMax.get(), oDatatype, oValue, oShapeRef, oNeg);
            }
            throw new RuntimeException("min or max cardinality expected with a path");
        }
        return new LocalConstraintImpl(id, oDatatype, oValue, oShapeRef, oNeg);
    }

}
