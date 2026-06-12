package PSBN.util;

public class SBNP extends SBN {

    private final DecompVector decomp;

    public SBNP(int n, int[][] weights, boolean[][] TT, DecompVector decomp) {
        super(n, weights, TT);
        this.decomp = decomp;
    }

    public DecompVector getDecomp() {
        return decomp;
    }


    @Override
    public String toString() {
        return toCsvRow(true);
    }

    @Override
    public String toCsvRow(boolean includeWeightsAndTransitions) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i <= decomp.getDimension(); i++) {
            sb.append(decomp.get(i)).append(",");
        }
        sb.append(super.toCsvRow(includeWeightsAndTransitions));
        return sb.toString();
    }
}
