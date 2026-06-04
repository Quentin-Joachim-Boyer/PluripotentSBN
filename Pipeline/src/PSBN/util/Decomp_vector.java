package PSBN.util;

public class Decomp_vector {

    private final int[] values;

    public Decomp_vector(int[] values) {
        this.values = values.clone();
    }

    public int getDimension() {
        return values.length - 1;
    }

    public int get(int i) {
        return values[i];
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder("_");
        for (int i = 0; i < values.length; i++) {
            if (i > 0) sb.append("_");
            sb.append(values[i]);
        }
        sb.append("_");
        return sb.toString();
    }
}