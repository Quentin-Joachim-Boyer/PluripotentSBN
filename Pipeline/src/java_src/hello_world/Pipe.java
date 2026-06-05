/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package hello_world;

import hello_world.Processors.Hello_world;

import com.gitlab.jpp.Job;
import com.gitlab.jpp.Pipeline;
import com.gitlab.jpp.TaskHolder;

/**
 *
 * @author defosser
 */
public class Pipe extends Pipeline<Integer,Void> {

    private final Job hello_worldJob;
    
    public Pipe() {
        super(Runtime.getRuntime().availableProcessors());
        this.hello_worldJob = new Job.JobBuilder<>(this, new Hello_world())
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
