package PSBN.Processors;

import com.gitlab.jpp.Processor;
import PSBN.util.SBN;

public class Minimizer implements Processor<SBN,SBN>{
    @Override
    public void reset() {
    }

    @Override
    public SBN process(SBN input) {
        return input;
    } 
}
