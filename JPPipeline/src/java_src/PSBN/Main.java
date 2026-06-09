package PSBN;

import java.util.logging.Level;
import java.util.logging.Logger;

public class Main {
    public static void main(String args[]) {

        Pipe PSBN_pipe = new Pipe();
        
        try {
            PSBN_pipe.executeFor(
                new PipeInput( 
                    Integer.parseInt(args[0]),
                    args[1],
                    args[2],
                    Integer.parseInt(args[3]),
                    args[4]
                )
            );
        } catch (InterruptedException ex) {
            Logger.getLogger(Main.class.getName()).log(Level.SEVERE, null, ex);
        }
        PSBN_pipe.halt();
    }
}