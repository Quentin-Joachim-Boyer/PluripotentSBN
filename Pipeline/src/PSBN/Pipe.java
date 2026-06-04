package PSBN;

import com.gitlab.jpp.Job;
import com.gitlab.jpp.Pipeline;
import com.gitlab.jpp.TaskHolder;
import PSBN.Processors.Decomposer;

/**
 *
 * @author BOYER
 */


public class Pipe extends Pipeline<Integer,Void> {

    private final Job hello_worldJob;
    
    public Pipe() {
        super(Runtime.getRuntime().availableProcessors());
        this.hello_worldJob = new Job.JobBuilder<>(this, new Decomposer())
                .setTaskSubmitter(new TaskHolder(this.startSignal))
                .build();
    }

    @Override
    protected void reset() {
    }

    @Override
    protected void initialTasks() {
        this.hello_worldJob.buildNewTask(input);
        
                    System.out.println("BOUH !!!");
    }
    @Override
    protected void after() {
       // process all result

        System.out.println("Done");
    }
    
}