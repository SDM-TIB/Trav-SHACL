package unibz.shapes.util;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class FileOutput extends Output{

    public FileOutput(File outputFile) throws IOException {
        this.writer = new BufferedWriter(new FileWriter(outputFile));
    }
}
