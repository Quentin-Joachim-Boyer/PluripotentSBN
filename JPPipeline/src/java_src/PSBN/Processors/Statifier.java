package PSBN.Processors;

import com.gitlab.jpp.Processor;

import PSBN.util.SBNP;

public class Statifier implements Processor<SBNP, String> {

    @Override
    public void reset() {
    }

    @Override
    public String process(SBNP input) {

        
        return input.toString();
    }
}