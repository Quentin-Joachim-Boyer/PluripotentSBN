package PSBN.util;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Tables precalculees pour la decomposition par colonne des statistiques de
 * robustesse/evolvabilite a la Wagner (2008).
 *
 * Une fonction de transition f_j ne depend que de la colonne j de la matrice
 * de poids : f_j = threshold(colonne_j), ou threshold(v) encode en binaire,
 * pour chaque etat s, le bit "(somme des v[i] pour i actif dans s) > 0".
 *
 * L'ensemble des genotypes realisant un phenotype (f_1,...,f_n) est le
 * produit cartesien ColumnSet(f_1) x ... x ColumnSet(f_n), ou
 * ColumnSet(f) = { v in [-w_bound,w_bound]^n : threshold(v) = f }.
 * Sous distribution uniforme sur ce produit (colonnes independantes), les
 * statistiques de Wagner se decomposent :
 *
 * - R_P_mean(f_1,...,f_n) = somme_j g(f_j)
 * - R_P_std(f_1,...,f_n)  = sqrt(somme_j var(f_j))
 * - E_P(f_1,...,f_n)      = somme_j nf(f_j)
 *
 * ou pour chaque code de fonction f atteignable :
 * - g(f)   = moyenne, sur v in ColumnSet(f), du nombre de voisins (i,+-1)
 *            de v dont threshold reste egal a f ;
 * - var(f) = variance de cette meme quantite ;
 * - nf(f)  = nombre de codes de fonctions distincts atteints par les voisins
 *            non neutres, sur l'ensemble de ColumnSet(f).
 */
public final class RobustnessTables {

    private final Map<Integer, Double> g = new HashMap<>();
    private final Map<Integer, Double> var = new HashMap<>();
    private final Map<Integer, Integer> nf = new HashMap<>();

    private RobustnessTables() {
    }

    public double g(int f) {
        return g.getOrDefault(f, 0.0);
    }

    public double var(int f) {
        return var.getOrDefault(f, 0.0);
    }

    public int nf(int f) {
        return nf.getOrDefault(f, 0);
    }

    /**
     * Borne des poids w_bound(d) (meme convention que count_frequency.lp /
     * PTBN_undercontrol.lp) :
     * w_bound(1,1). w_bound(1,2). w_bound(2,3). w_bound(3,4). w_bound(5,5).
     * w_bound(D,D) :- D > 5.
     */
    public static int wBound(int n) {
        switch (n) {
            case 1:
                return 1;
            case 2:
                return 1;
            case 3:
                return 2;
            case 4:
                return 3;
            default:
                return n;
        }
    }

    public static RobustnessTables compute(int n) {
        RobustnessTables tables = new RobustnessTables();
        int wb = wBound(n);
        int domainSize = 2 * wb + 1;

        int nbCols = 1;
        for (int i = 0; i < n; i++) nbCols *= domainSize;

        Map<Integer, List<Integer>> neutralCountsByF = new HashMap<>();
        Map<Integer, Set<Integer>> diffsByF = new HashMap<>();

        int[] v = new int[n];
        for (int idx = 0; idx < nbCols; idx++) {
            int rest = idx;
            for (int i = 0; i < n; i++) {
                v[i] = (rest % domainSize) - wb;
                rest /= domainSize;
            }

            int f = threshold(v, n);
            Set<Integer> diffs = diffsByF.computeIfAbsent(f, k -> new HashSet<>());

            int neutral = 0;
            for (int i = 0; i < n; i++) {
                for (int delta : new int[]{-1, 1}) {
                    int old = v[i];
                    v[i] += delta;
                    int f2 = threshold(v, n);
                    v[i] = old;
                    if (f2 == f) {
                        neutral++;
                    } else {
                        diffs.add(f2);
                    }
                }
            }
            neutralCountsByF.computeIfAbsent(f, k -> new ArrayList<>()).add(neutral);
        }

        for (Map.Entry<Integer, List<Integer>> entry : neutralCountsByF.entrySet()) {
            int f = entry.getKey();
            List<Integer> counts = entry.getValue();

            double mean = 0;
            for (int c : counts) mean += c;
            mean /= counts.size();

            double sumSq = 0;
            for (int c : counts) {
                double d = c - mean;
                sumSq += d * d;
            }

            tables.g.put(f, mean);
            tables.var.put(f, sumSq / counts.size());
            tables.nf.put(f, diffsByF.get(f).size());
        }

        return tables;
    }

    /**
     * threshold(v)[s] = 1 ssi la somme des v[i] pour i actif dans s est > 0.
     */
    private static int threshold(int[] v, int n) {
        int nbStates = 1 << n;
        int code = 0;
        for (int s = 0; s < nbStates; s++) {
            int sum = 0;
            for (int i = 0; i < n; i++) {
                if ((s & (1 << i)) != 0) sum += v[i];
            }
            if (sum > 0) code |= (1 << s);
        }
        return code;
    }
}
