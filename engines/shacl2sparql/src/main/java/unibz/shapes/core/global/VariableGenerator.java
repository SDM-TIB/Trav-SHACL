package unibz.shapes.core.global;


import java.util.concurrent.atomic.AtomicInteger;

public class VariableGenerator {

    public enum VariableType {
        VALIDATION("p_"),
        VIOLATION("n_");
        public final String prefix;

        VariableType(String prefix) {
            this.prefix = prefix;
        }
    }
        private static final AtomicInteger index = new AtomicInteger(0);

        public static String generateVariable(VariableType type) {
            return type.prefix + index.incrementAndGet();
        }

        public static String getFocusNodeVar() {
            return "x";
        }

}
