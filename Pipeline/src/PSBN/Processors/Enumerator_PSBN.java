package PSBN.Processors;

import com.gitlab.jpp.Processor;


public class Enumerator_PSBN implements Processor<Integer,Void> {
        
    @Override
    public void reset() {
    }

    @Override
    public Void process(Integer input) {
        int d = input;
        for (int i = 0; i < d; ++i) {
            System.out.println("Hello World !!");
        }
        return null;
    } 
}
