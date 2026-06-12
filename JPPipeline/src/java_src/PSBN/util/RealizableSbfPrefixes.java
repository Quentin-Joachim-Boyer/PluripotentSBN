package PSBN.util;

import java.util.ArrayList;
import java.util.BitSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Calcule, pour une dimension donnee, l'ensemble des prefixes de SBF (les n
 * premiers bits S=0..n-1 de la fonction de transition du noeud 1) qui sont
 * effectivement realisables par un vecteur de poids entier.
 *
 * transition_function_bit(1,S) vaut 1 ssi sum{w(i) : bit (i-1) de S est a 1} > 0,
 * avec w(i) dans [-n, n] (cf. PTBN_undercontrol.lp). Chaque prefixe est
 * represente par un {@link BitSet} de taille n (bit S = transition_function_bit(1,S)
 * pour S=0..n-1).
 *
 * Sert a subdiviser l'espace de recherche (cf. Subdivision.lp, fixed_bits) en
 * ne retenant que les prefixes realisables : les autres seraient de toute
 * facon UNSAT.
 *
 * Le resultat ne depend que de n, donc il est mis en cache.
 */
public final class RealizableSbfPrefixes {

    private static final Map<Integer, List<BitSet>> CACHE = new HashMap<>();

    private RealizableSbfPrefixes() {
    }

    public static synchronized List<BitSet> forDimension(int n) {
        return CACHE.computeIfAbsent(n, RealizableSbfPrefixes::compute);
    }

    private static List<BitSet> compute(int n) {
        Set<BitSet> prefixes = new HashSet<>();
        int[] weights = new int[n];
        enumerateWeights(weights, 0, n, prefixes);
        return new ArrayList<>(prefixes);
    }

    private static void enumerateWeights(int[] weights, int i, int n, Set<BitSet> prefixes) {
        if (i == n) {
            prefixes.add(prefixFor(weights, n));
            return;
        }
        for (int v = -n; v <= n; v++) {
            weights[i] = v;
            enumerateWeights(weights, i + 1, n, prefixes);
        }
    }

    private static BitSet prefixFor(int[] weights, int n) {
        BitSet prefix = new BitSet(n);
        for (int s = 0; s < n; s++) {
            int sum = 0;
            for (int k = 0; k < n; k++) {
                if ((s & (1 << k)) != 0) sum += weights[k];
            }
            if (sum > 0) prefix.set(s);
        }
        return prefix;
    }
}
