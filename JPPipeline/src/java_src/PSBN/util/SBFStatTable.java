package PSBN.util;

import java.util.ArrayList;
import java.util.BitSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Table precalculee, indexee par signed Boolean function (SBF) f (un
 * {@link BitSet} de taille 2^n), de statistiques sur
 * ColumnSet(f) = { v in [-w_bound,w_bound]^n : threshold(v) = f },
 * ou threshold(v) encode, pour chaque etat s, le bit
 * "(somme des v[i] pour i actif dans s) > 0".
 *
 * Sert notamment a la decomposition par colonne des statistiques de
 * robustesse/evolvabilite a la Wagner (2008) : une fonction de transition f_j
 * d'un SBN ne depend que de la colonne j de sa matrice de poids
 * (f_j = threshold(colonne_j)), et l'ensemble des genotypes realisant un
 * phenotype (f_1,...,f_n) est le produit cartesien
 * ColumnSet(f_1) x ... x ColumnSet(f_n). Sous distribution uniforme sur ce
 * produit (colonnes independantes) :
 *
 * - R_P_mean(f_1,...,f_n) = somme_j neutralCountMean(f_j)
 * - R_P_std(f_1,...,f_n)  = sqrt(somme_j neutralCountVar(f_j))
 * - E_P(f_1,...,f_n)      = somme_j nbDistinctNeighborPhenotypes(f_j)
 *
 * et le nombre de matrices de poids realisant (f_1,...,f_n) est
 * produit_j columnSetSize(f_j).
 *
 * Pour chaque SBF f atteignable :
 * - columnSetSize(f) = |ColumnSet(f)|, le nombre de vecteurs de poids menant a f ;
 * - neutralCountMean(f) = moyenne, sur v in ColumnSet(f), du nombre de
 *                         voisins (i,+-1) de v dont threshold reste egal a f
 *                         (un compte, pas le ratio r de Wagner (2008), qui
 *                         s'obtient en divisant par 2*n) ;
 * - neutralCountVar(f)  = variance de cette meme quantite ;
 * - nbDistinctNeighborPhenotypes(f) = nombre de SBF distincts atteints par
 *                         les voisins non neutres, sur l'ensemble de
 *                         ColumnSet(f).
 */
public final class SBFStatTable {

    private final Map<BitSet, Integer> columnSetSize = new HashMap<>();
    private final Map<BitSet, Double> neutralCountMean = new HashMap<>();
    private final Map<BitSet, Double> neutralCountVar = new HashMap<>();
    private final Map<BitSet, Integer> nbDistinctNeighborPhenotypes = new HashMap<>();

    private SBFStatTable() {
    }

    public int columnSetSize(BitSet f) {
        return columnSetSize.getOrDefault(f, 0);
    }

    public double neutralCountMean(BitSet f) {
        return neutralCountMean.getOrDefault(f, 0.0);
    }

    public double neutralCountVar(BitSet f) {
        return neutralCountVar.getOrDefault(f, 0.0);
    }

    public int nbDistinctNeighborPhenotypes(BitSet f) {
        return nbDistinctNeighborPhenotypes.getOrDefault(f, 0);
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

    public static SBFStatTable compute(int n) {
        SBFStatTable tables = new SBFStatTable();
        int wb = wBound(n);
        int domainSize = 2 * wb + 1;

        int nbCols = 1;
        for (int i = 0; i < n; i++) nbCols *= domainSize;

        Map<BitSet, List<Integer>> neutralCountsByF = new HashMap<>();
        Map<BitSet, Set<BitSet>> diffsByF = new HashMap<>();

        int[] v = new int[n];
        for (int idx = 0; idx < nbCols; idx++) {
            int rest = idx;
            for (int i = 0; i < n; i++) {
                v[i] = (rest % domainSize) - wb;
                rest /= domainSize;
            }

            BitSet f = threshold(v, n);
            Set<BitSet> diffs = diffsByF.computeIfAbsent(f, k -> new HashSet<>());

            int neutral = 0;
            for (int i = 0; i < n; i++) {
                for (int delta : new int[]{-1, 1}) {
                    int old = v[i];
                    v[i] += delta;
                    BitSet f2 = threshold(v, n);
                    v[i] = old;
                    if (f2.equals(f)) {
                        neutral++;
                    } else {
                        diffs.add(f2);
                    }
                }
            }
            neutralCountsByF.computeIfAbsent(f, k -> new ArrayList<>()).add(neutral);
        }

        for (Map.Entry<BitSet, List<Integer>> entry : neutralCountsByF.entrySet()) {
            BitSet f = entry.getKey();
            List<Integer> counts = entry.getValue();

            double mean = 0;
            for (int c : counts) mean += c;
            mean /= counts.size();

            double sumSq = 0;
            for (int c : counts) {
                double d = c - mean;
                sumSq += d * d;
            }

            tables.columnSetSize.put(f, counts.size());
            tables.neutralCountMean.put(f, mean);
            tables.neutralCountVar.put(f, sumSq / counts.size());
            tables.nbDistinctNeighborPhenotypes.put(f, diffsByF.get(f).size());
        }

        return tables;
    }

    /**
     * threshold(v)[s] = 1 ssi la somme des v[i] pour i actif dans s est > 0.
     */
    private static BitSet threshold(int[] v, int n) {
        int nbStates = 1 << n;
        BitSet code = new BitSet(nbStates);
        for (int s = 0; s < nbStates; s++) {
            int sum = 0;
            for (int i = 0; i < n; i++) {
                if ((s & (1 << i)) != 0) sum += v[i];
            }
            if (sum > 0) code.set(s);
        }
        return code;
    }
}
