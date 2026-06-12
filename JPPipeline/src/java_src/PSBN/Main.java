package PSBN;

import java.util.logging.Level;
import java.util.logging.Logger;

public class Main {
    public static void main(String args[]) {

        Pipe PSBN_pipe = new Pipe();
        
        // args[5] (optionnel) : 1/0 pour inclure/omettre les colonnes f_j et
        // w_i,j du CSV (non utilisees par la visualisation scatter). Defaut : 1.
        boolean includeWeightsAndTransitions = args.length <= 5 || Integer.parseInt(args[5]) != 0;

        try {
            PSBN_pipe.executeFor(
                new PipeInput(
                    Integer.parseInt(args[0]),
                    args[1],
                    args[2],
                    Integer.parseInt(args[3]),
                    args[4],
                    includeWeightsAndTransitions
                )
            );
        } catch (InterruptedException ex) {
            Logger.getLogger(Main.class.getName()).log(Level.SEVERE, null, ex);
        }
        PSBN_pipe.halt();
    }
}