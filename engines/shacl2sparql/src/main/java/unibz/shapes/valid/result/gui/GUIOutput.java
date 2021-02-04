package unibz.shapes.valid.result.gui;

import unibz.shapes.util.StringOutput;
import unibz.shapes.valid.result.ResultSet;

public class GUIOutput {
    private final ResultSet rs;
    private final StringOutput validationLog;
    private final StringOutput validTargetsLog;
    private final StringOutput inValidTargetsLog;
    private final StringOutput statsLog;
    private final StringOutput tracesLog; //@@ added for comparing purposes (Trav-SHACL)

    public GUIOutput(ResultSet rs, StringOutput validationLog, StringOutput validTargetsLog, StringOutput inValidTargetsLog, StringOutput statsLog, StringOutput tracesLog) { //@@
        this.rs = rs;
        this.validationLog = validationLog;
        this.validTargetsLog = validTargetsLog;
        this.inValidTargetsLog = inValidTargetsLog;
        this.statsLog = statsLog;
        this.tracesLog = tracesLog; //@@ added for comparing purposes (Trav-SHACL)
    }

    public String getLog(){
        return validationLog.asString();
    }

    public String getTargetViolations(){
        return rs.toString();
    }

    public boolean isValid(){
        return rs.getInValidTargetResults().isEmpty();
    }

    public String getStats(){
        return statsLog.asString();
    }

    public int numberOfValidTargets(){
        return rs.getValidTargetResults().size();
    }

    public int numberOfInValidTargets(){
        return rs.getInValidTargetResults().size();
    }

}
