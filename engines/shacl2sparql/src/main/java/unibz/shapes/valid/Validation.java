package unibz.shapes.valid;

import unibz.shapes.valid.result.ResultSet;

import java.io.IOException;

public interface Validation {

    ResultSet exec() throws IOException;
}
