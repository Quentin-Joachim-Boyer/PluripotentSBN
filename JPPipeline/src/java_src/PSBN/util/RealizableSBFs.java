package PSBN.util;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/**
 * Calcule, pour une dimension donnee, l'ensemble des SBF (signed Boolean
 * functions) du noeud 1 qui sont effectivement realisables par un vecteur de
 * poids entier.
 *
 * Un SBF correspond a une fonction a seuil : transition_function_bit(1,S)
 * vaut 1 ssi sum{w(i) : bit (i-1) de S est a 1} > 0, avec w(i) dans [-n, n]
 * (cf. PTBN_undercontrol.lp). Le nombre de telles fonctions est borne par
 * (2n+1)^n, bien plus petit que 2^(2^n) : enumerer les vecteurs de poids et
 * collecter les SBF produits permet d'eviter d'appeler clingcon sur des
 * tranches qui seraient de toute facon UNSAT.
 *
 * Le resultat ne depend que de n, donc il est mis en cache.
 */
public final class RealizableSBFs {

    private static final Map<Integer, int[]> CACHE = new HashMap<>();

    private RealizableSBFs() {
    }

    public static synchronized int[] forDimension(int n) {
        return CACHE.computeIfAbsent(n, RealizableSBFs::compute);
    }

    private static int[] compute(int n) {
        Set<Integer> sbfs = new HashSet<>();
        int[] weights = new int[n];
        enumerateWeights(weights, 0, n, sbfs);
        int[] result = new int[sbfs.size()];
        int idx = 0;
        for (int sbf : sbfs) result[idx++] = sbf;
        return result;
    }

    private static void enumerateWeights(int[] weights, int i, int n, Set<Integer> sbfs) {
        if (i == n) {
            sbfs.add(sbfFor(weights, n));
            return;
        }
        for (int v = -n; v <= n; v++) {
            weights[i] = v;
            enumerateWeights(weights, i + 1, n, sbfs);
        }
    }

    private static int sbfFor(int[] weights, int n) {
        int sbf = 0;
        for (int s = 0; s < (1 << n); s++) {
            int sum = 0;
            for (int k = 0; k < n; k++) {
                if ((s & (1 << k)) != 0) sum += weights[k];
            }
            if (sum > 0) sbf |= (1 << s);
        }
        return sbf;
    }
}
