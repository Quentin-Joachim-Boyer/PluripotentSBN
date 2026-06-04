package PSBN.Processors;

import com.gitlab.jpp.Processor;

import java.util.ArrayList;

import PSBN.util.Decomp_vector;
import PSBN.util.SBN;

public class Enumerator_PSBN implements Processor<Decomp_vector,ArrayList<SBN>> {
        
    @Override
    public void reset() {
    }

    @Override
    public ArrayList<SBN> process(Decomp_vector input) {
        return null;
    } 
}
