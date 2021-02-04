package unibz.shapes.util;

import java.io.StringWriter;

public class StringOutput extends Output {

    public StringOutput() {
        this.writer = new StringWriter();
    }

    public String asString() {
        return writer.toString();
    }
}
