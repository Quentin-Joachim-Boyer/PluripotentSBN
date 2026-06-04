package PSBN;

import java.util.logging.Level;
import java.util.logging.Logger;

public class Main {
    public static void main(String args[]) {
        Pipe PSBN_pipe = new Pipe();
        
        try {
            PSBN_pipe.executeFor(Integer.parseInt(args[0]));
        } catch (InterruptedException ex) {
            Logger.getLogger(Main.class.getName()).log(Level.SEVERE, null, ex);
        }
        PSBN_pipe.halt();
    }
}