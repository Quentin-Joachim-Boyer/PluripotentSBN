package PSBN;

import java.util.logging.Level;
import java.util.logging.Logger;

public class Main {
    public static void main(String args[]) {
        Pipe hello_pipe = new Pipe();
        
        try {
            hello_pipe.executeFor(20);
        } catch (InterruptedException ex) {
            Logger.getLogger(Main.class.getName()).log(Level.SEVERE, null, ex);
        }
        hello_pipe.halt();
    }
}