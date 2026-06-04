package PSBN.Processors;

import com.gitlab.jpp.Processor;

import PSBN.util.Decomp_vector;

import java.util.ArrayList;

public class Decomposer implements Processor<Integer, ArrayList<Decomp_vector>> {

    @Override
    public void reset() {
    }

    @Override
    public ArrayList<Decomp_vector> process(Integer input) {
        int n = input;
        ArrayList<Decomp_vector> result = new ArrayList<>();
        enumerate(n, 0, 1 << n, new int[n + 1], result);
        return result;
    }

    private void enumerate(int n, int pos, int remaining, int[] current, ArrayList<Decomp_vector> result) {
        if (pos == n + 1) {
            if (remaining == 0)
                result.add(new Decomp_vector(current.clone()));
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
