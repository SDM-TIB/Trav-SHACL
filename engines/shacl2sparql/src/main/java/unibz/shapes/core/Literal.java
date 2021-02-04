package unibz.shapes.core;

import java.util.Objects;

public class Literal {

    private final String pred;
    private final String arg;
    private final boolean isPos;

    public Literal(String pred, String arg, boolean isPos) {
        this.pred = pred;
        this.arg = arg;
        this.isPos = isPos;
    }

    public String getPredicate() {
        return pred;
    }

    public Literal getAtom() {
        return isPos ?
                this :
                this.getNegation();
    }

    String getArg() {
        return arg;
    }

    public boolean isPos() {
        return isPos;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Literal literal = (Literal) o;
        return isPos == literal.isPos &&
                Objects.equals(pred, literal.pred) &&
                Objects.equals(arg, literal.arg);
    }

    @Override
    public int hashCode() {
        return Objects.hash(pred, arg, isPos);
    }

    public Literal getNegation() {
        return new Literal(pred, arg, !isPos);
    }

    @Override
    public String toString() {
        return (isPos ?
                "" :
                "!") +
                pred + "(" +
                arg + ")";
    }
}
