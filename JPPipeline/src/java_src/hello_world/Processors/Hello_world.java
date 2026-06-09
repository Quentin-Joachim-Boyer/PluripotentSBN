/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package hello_world.Processors;

import com.gitlab.jpp.Processor;

/**
 *
 * @author defosser
 */
public class Hello_world implements Processor<Integer,Void> {

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
