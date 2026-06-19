package PSBN.util;

public class DecompVector {

    private final int[] values;
    // Index d'orientation de l'arbre de decomposition. Un vecteur sous-determine
    // l'arbre (orientations gauche/droite distinctes) ; l'orientation selectionne
    // l'arbre via la constante `o` du setup_btree. Defaut 0 (retro-compatible).
    private final int orientation;

    public DecompVector(int[] values) {
        this(values, 0);
    }

    public DecompVector(int[] values, int orientation) {
        this.values = values.clone();
        this.orientation = orientation;
    }

    public int getDimension() {
        return values.length - 1;
    }

    public int get(int i) {
        return values[i];
    }

    public int getOrientation() {
        return orientation;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder("_");
        for (int i = 0; i < values.length; i++) {
            if (i > 0) sb.append("_");
            sb.append(values[i]);
        }
        sb.append("_");
        if (orientation != 0) sb.append("o").append(orientation).append("_");
        return sb.toString();
    }
}