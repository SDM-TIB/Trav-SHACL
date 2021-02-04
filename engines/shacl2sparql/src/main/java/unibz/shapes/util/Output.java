package unibz.shapes.util;

import java.io.*;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.time.format.FormatStyle;

public abstract class Output {

    Writer writer;
    private Instant previous;
    private final DateTimeFormatter formatter = DateTimeFormatter
            .ofLocalizedDateTime( FormatStyle.SHORT )
//            .withLocale( Locale.UK )
            .withZone( ZoneId.systemDefault() );


    public void close() throws IOException {
        writer.close();
    }

    public void write(String s) {
        try {
            writer.write(s + "\n");
//            writer.flush();

        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    public void start(String s) {
        try {
            previous= Instant.now();
            writer.write("\n"+formatter.format(previous)+ ":\n");
            writer.write(s + "\n");
//            writer.flush();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

    }

    public long elapsed() {
        Instant now = Instant.now();
        long elapsed = Duration.between(previous, now).toMillis();
        try {
            writer.write("elapsed: " + elapsed+" ms\n");
//            writer.flush();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return elapsed;
    }

}
