package PSBN.util;

import java.util.ArrayList;

/**
 * Resultat de l'enumeration monolithique (avec garde-fou) d'un vecteur.
 *
 * Soit l'enumeration a tenu sous le seuil et {@link #solutions} contient toutes
 * les SBNP du vecteur ({@link #overflowed} = false), soit le garde-fou a saute
 * ({@link #overflowed} = true) et il faut subdiviser ce vecteur par masque.
 * Le vecteur {@link #dv} est toujours present pour pouvoir generer les masques.
 */
public class EnumerationResult {

    public final DecompVector dv;
    public final ArrayList<SBNP> solutions;
    public final boolean overflowed;

    private EnumerationResult(DecompVector dv, ArrayList<SBNP> solutions, boolean overflowed) {
        this.dv = dv;
        this.solutions = solutions;
        this.overflowed = overflowed;
    }

    public static EnumerationResult solved(DecompVector dv, ArrayList<SBNP> solutions) {
        return new EnumerationResult(dv, solutions, false);
    }

    public static EnumerationResult overflow(DecompVector dv) {
        return new EnumerationResult(dv, null, true);
    }
}