package PSBN.util;

public class SBNP extends SBN {

    private final DecompVector decomp;
    /** Arbre de decomposition etiquete par les noeuds de controle (cf. ClingconUtil.buildTree), "" si absent. */
    private final String tree;

    public SBNP(int n, int[][] weights, boolean[][] TT, DecompVector decomp) {
        this(n, weights, TT, decomp, "");
    }

    public SBNP(int n, int[][] weights, boolean[][] TT, DecompVector decomp, String tree) {
        super(n, weights, TT);
        this.decomp = decomp;
        this.tree = tree == null ? "" : tree;
    }

    public DecompVector getDecomp() {
        return decomp;
    }

    public String getTree() {
        return tree;
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
        sb.append(tree).append(","); // arbre etiquete, juste apres le vecteur
        sb.append(super.toCsvRow(includeWeightsAndTransitions));
        return sb.toString();
    }
}
