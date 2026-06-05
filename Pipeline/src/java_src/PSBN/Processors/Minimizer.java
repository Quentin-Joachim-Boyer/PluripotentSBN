package PSBN.Processors;

import PSBN.util.SBNP;

import com.gitlab.jpp.Processor;

public class Minimizer implements Processor<SBNP, SBNP> {
    @Override
    public void reset() {
    }

    @Override
    public SBNP process(SBNP input) {
        return input;
    }
}