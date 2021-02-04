package unibz.shapes.core;

import com.google.common.collect.ImmutableSet;
import org.eclipse.rdf4j.query.BindingSet;
import unibz.shapes.util.ImmutableCollectors;

import java.util.stream.Collectors;
import java.util.stream.Stream;

public class RulePattern {
    private final Literal head;
    private final ImmutableSet<Literal> literals;
    private final ImmutableSet<String> variables;

    // If a value for each variable is produced (by a solution mapping), then the rule pattern can be instantiated.
    // Note that it may be the case that these variables do not appear in the the body of the rule (because there is no constraint to propagate on these values, they only need to exist)

    public RulePattern(Literal head, ImmutableSet<Literal> body) {
        this.head = head;
        this.literals = body;
        this.variables = Stream.concat(
                Stream.of(head.getArg()),
                body.stream()
                        .map(a -> a.getArg())
        ).collect(ImmutableCollectors.toSet());
    }

    public Literal getHead() {
        return head;
    }

    public ImmutableSet<Literal> getLiterals() {
        return literals;
    }

    @Override
    public String toString() {
        return head + ": - " +
                getBodyString();
    }

    private String getBodyString() {
        if (literals.isEmpty()) {
            return "";
        }
        return literals.stream()
                .map(Literal::toString)
                .collect(Collectors.joining(", "));
    }

    public Literal instantiateAtom(Literal a, BindingSet bs) {
        return new Literal(
                a.getPredicate(),
                bs.getValue(a.getArg()).stringValue(),
                a.isPos()
        );

    }

    public ImmutableSet<Literal> instantiateBody(BindingSet bs) {
                return literals.stream()
                        .map(a -> instantiateAtom(a, bs))
                        .collect(ImmutableCollectors.toSet());
    }

    public ImmutableSet<String> getVariables() {
        return variables;
    }
}
