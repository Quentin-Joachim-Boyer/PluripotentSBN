package PSBN;

import java.util.ArrayList;
import java.util.HashMap;

import com.gitlab.jpp.Job;
import com.gitlab.jpp.OutputHandler;
import com.gitlab.jpp.Pipeline;
import com.gitlab.jpp.TaskHolder;

import PSBN.Processors.Decomposer;
import PSBN.Processors.Enumerator_PSBN;
import PSBN.Processors.Minimizer;
import PSBN.util.Decomp_vector;
import PSBN.util.SBN;

/**
 * @author BOYER
 */


public class Pipe extends Pipeline<Integer,Void> {

    
    private final Job<Integer, ArrayList<Decomp_vector>> DecompositionJob;
    private final Job<Decomp_vector, ArrayList<SBN>> EnumerationJob;
    private final Job<SBN, SBN> MinimizationJob;

    @SuppressWarnings("unchecked")    
    public Pipe() {
        super(Runtime.getRuntime().availableProcessors());
        
        this.DecompositionJob = new Job.JobBuilder<Integer, ArrayList<Decomp_vector>>(this, new Decomposer())
                .setTaskSubmitter(new TaskHolder(this.startSignal))
                .setOutputHandler(new OutputHandler<ArrayList<Decomp_vector>>() {
                    @Override
                    public void handle(ArrayList<Decomp_vector> processorOutput) {
                        for (Decomp_vector dv : processorOutput) {
                            EnumerationJob.buildNewTask(dv);
                        }   
                    }
                })
                .build();
        this.EnumerationJob = new Job.JobBuilder<Decomp_vector, ArrayList<SBN>>(this, new Enumerator_PSBN())
                .setOutputHandler(new OutputHandler<ArrayList<SBN>>() {
                    @Override
                    public void handle(ArrayList<SBN> processorOutput) {
                        for (SBN sbn : processorOutput) {
                            MinimizationJob.buildNewTask(sbn);
                        }   
                    }
                })
                .build();
        this.MinimizationJob = new Job.JobBuilder<SBN,SBN>(this, new Minimizer())
                .build();
    }

    @Override
    protected void reset() {
    }

    @Override
    protected void initialTasks() {
        this.DecompositionJob.buildNewTask(input);
        
                    System.out.println("BOUH !!!");
    }
    @Override
    protected void after() {
       // process all result

        System.out.println("Done");
    }
    
}