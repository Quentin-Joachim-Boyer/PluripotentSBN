package PSBN.Processors;

import com.gitlab.jpp.Processor;

import PSBN.util.DecompVector;
import PSBN.util.BtreeOrientations;
import java.util.ArrayList;

public class Decomposer implements Processor<Integer, ArrayList<DecompVector>> {

    @Override
    public void reset() {
    }

    @Override
    public ArrayList<DecompVector> process(Integer input) {
        int n = input;
        ArrayList<DecompVector> result = new ArrayList<>();
        enumerate(n, 0, 1 << n, new int[n + 1], result);
        return result;
    }

    private void enumerate(int n, int pos, int remaining, int[] current, ArrayList<DecompVector> result) {
        if (pos == n + 1) {
            if (remaining == 0) {
                // Un vecteur sous-determine l'arbre : on emet une tache par
                // orientation (l'unite d'enumeration correcte est l'arbre).
                int orientations = BtreeOrientations.orientationCount(current, n);
                for (int o = 0; o < orientations; o++)
                    result.add(new DecompVector(current.clone(), o));
            }
            return;
        }
        int maxVal = 1 << pos;
        int weight = 1 << (n - pos);
        for (int v = 0; v <= maxVal && v * weight <= remaining; v++) {
            current[pos] = v;
            enumerate(n, pos + 1, remaining - v * weight, current, result);
        }
    }
}
