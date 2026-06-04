package PSBN.util;

public class SBN {

    private final int n;
    private final int[][] weights;
    private final boolean[][] TT;

    public SBN(int n, int[][] weights, boolean[][] TT) {
        this.n = n;
        this.weights = weights;
        this.TT = TT;
    }

    public int getDimension() {
        return n;
    }

    public int getWeight(int i, int j) {
        return weights[i][j];
    }

    public boolean getTransition(int i, int state) {
        return TT[i][state];
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) {
            int f = 0;
            for (int s = 0; s < (1 << n); s++) {
                if (TT[i][s]) f += (1 << s);
            }
            sb.append(f).append(",");
        }
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                sb.append(weights[i][j]);
                if (i < n - 1 || j < n - 1) sb.append(",");
            }
        }
        return sb.toString();
    }
}