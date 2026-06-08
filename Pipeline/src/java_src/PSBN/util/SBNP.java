package PSBN.util;

public class SBNP extends SBN {

    private final Decomp_vector decomp;

    public SBNP(int n, int[][] weights, boolean[][] TT, Decomp_vector decomp) {
        super(n, weights, TT);
        this.decomp = decomp;
    }

    public Decomp_vector getDecomp() {
        return decomp;
    }


    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i <= decomp.getDimension(); i++) {
            sb.append(decomp.get(i)).append(",");
        }
        sb.append(super.toString());
        return sb.toString();
    }
}
