package PSBN.util;

import java.util.ArrayList;
import java.util.BitSet;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class SBN {

    protected final int n;
    protected final int[][] weights;
    protected final boolean[][] TT;

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

    /**
     * Encode chaque fonction de transition f_i comme un SBF (bit s = TT[i][s]),
     * sous forme de {@link BitSet} de taille 2^n.
     */
    public static BitSet[] sbfCodes(boolean[][] TT, int n) {
        BitSet[] f = new BitSet[n];
        for (int i = 0; i < n; i++) {
            BitSet code = new BitSet(1 << n);
            for (int s = 0; s < (1 << n); s++) {
                if (TT[i][s]) code.set(s);
            }
            f[i] = code;
        }
        return f;
    }

    public BitSet[] sbfCodes() {
        return sbfCodes(TT, n);
    }

    /**
     * Calcule l'etat suivant d'un etat donne:
     * le bit i de l'etat suivant vaut TT[i][state].
     */
    private int nextState(int state) {
        int next = 0;
        for (int i = 0; i < n; i++) {
            if (TT[i][state]) next |= (1 << i);
        }
        return next;
    }

    /**
     * Calcule l'ensemble des bassins d'attraction du SBN, par parcours de trajectoire avec memoisation.
     *
     * Pour chaque etat de depart non encore traite, on suit sa trajectoire
     * jusqu'a soit rejoindre un bassin deja connu, soit retomber sur un etat
     * deja visite dans la trajectoire courante (ce qui revele un nouvel
     * attracteur, point fixe ou cycle limite). Tous les etats de la
     * trajectoire (transitoires + cycle) sont alors rattaches a ce bassin.
     *
     * @return une table associant a chaque attracteur (cycle d'etats, dans
     *         l'ordre de la trajectoire, de longueur 1 pour un point fixe)
     *         l'ensemble des etats de son bassin d'attraction (attracteur inclus).
     */
    public Map<List<Integer>, Set<Integer>> computeAttractionBasins() {
        int nbStates = 1 << n;
        int[] attractorOf = new int[nbStates];
        java.util.Arrays.fill(attractorOf, -1);

        List<List<Integer>> attractors = new ArrayList<>();
        Map<List<Integer>, Set<Integer>> basins = new LinkedHashMap<>();

        for (int start = 0; start < nbStates; start++) {
            if (attractorOf[start] != -1) continue;

            List<Integer> path = new ArrayList<>();
            Map<Integer, Integer> positionInPath = new HashMap<>();
            int current = start;
            while (attractorOf[current] == -1 && !positionInPath.containsKey(current)) {
                positionInPath.put(current, path.size());
                path.add(current);
                current = nextState(current);
            }

            int id;
            if (attractorOf[current] != -1) {
                id = attractorOf[current];
            } else {
                int cycleStart = positionInPath.get(current);
                List<Integer> cycle = new ArrayList<>(path.subList(cycleStart, path.size()));
                attractors.add(cycle);
                id = attractors.size() - 1;
                basins.put(cycle, new LinkedHashSet<>());
            }

            Set<Integer> basin = basins.get(attractors.get(id));
            for (int s : path) {
                attractorOf[s] = id;
                basin.add(s);
            }
        }

        return basins;
    }

    @Override
    public String toString() {
        return toCsvRow(true);
    }

    /**
     * Construit la ligne CSV : f_j (bitstrings) et w_i,j sont omis si
     * {@code includeWeightsAndTransitions} est false.
     * Inclut toujours AtrSize et dynamics (encodage des attracteurs par etat).
     */
    public String toCsvRow(boolean includeWeightsAndTransitions) {
        StringBuilder sb = new StringBuilder();
        if (includeWeightsAndTransitions) {
            for (int i = 0; i < n; i++) {
                for (int s = 0; s < (1 << n); s++) {
                    sb.append(TT[i][s] ? '1' : '0');
                }
                sb.append(",");
            }
            for (int i = 0; i < n; i++) {
                for (int j = 0; j < n; j++) {
                    sb.append(weights[i][j]);
                    sb.append(",");
                }
            }
        }
        Map<List<Integer>, Set<Integer>> basins = computeAttractionBasins();
        sb.append(meanSquaredAttractorSize(basins));
        sb.append(",");
        sb.append(basins.size()); // NumBasins : nombre d'attracteurs = nombre de bassins
        sb.append(",");
        sb.append(attractorDynamicsEncoding(basins));
        return sb.toString();
    }

    /**
     * Encode, pour chaque etat s, le cycle attracteur auquel il converge.
     * Format : chaines separees par '|', une par etat s=0..2^n-1 ;
     * chaque chaine est le cycle en forme canonique (rotation minimale,
     * en partant de l'etat minimal), etats separes par ','.
     * Ex. pour d=3 : "0|1,5|4|4|0|1,5|4|4".
     * Sert au calcul de dDA en Python : dDA(g,g') = somme_s dCYCLE(lim_g(s), lim_g'(s)).
     */
    public String attractorDynamicsEncoding(Map<List<Integer>, Set<Integer>> basins) {
        int nbStates = 1 << n;
        String[] stateToAtr = new String[nbStates];
        for (Map.Entry<List<Integer>, Set<Integer>> entry : basins.entrySet()) {
            String canonical = canonicalCycle(entry.getKey());
            for (int s : entry.getValue()) {
                stateToAtr[s] = canonical;
            }
        }
        StringBuilder sb = new StringBuilder();
        for (int s = 0; s < nbStates; s++) {
            if (s > 0) sb.append('|');
            sb.append(stateToAtr[s]);
        }
        return sb.toString();
    }

    /** Rotation minimale d'un cycle : commence a l'etat le plus petit. */
    private static String canonicalCycle(List<Integer> cycle) {
        int minIdx = 0;
        for (int i = 1; i < cycle.size(); i++) {
            if (cycle.get(i) < cycle.get(minIdx)) minIdx = i;
        }
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < cycle.size(); i++) {
            if (i > 0) sb.append(':');  // ':' et non ',' pour ne pas casser le CSV
            sb.append(cycle.get((minIdx + i) % cycle.size()));
        }
        return sb.toString();
    }

    /**
     * Somme de tous les poids des arcs du reseau.
     */
    public int sumOfWeights() {
        int sum = 0;
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                sum += weights[i][j];
            }
        }
        return sum;
    }

    private double meanSquaredAttractorSize(Map<List<Integer>, Set<Integer>> basins) {
        Set<List<Integer>> attractors = basins.keySet();
        long sumOfSquares = 0;
        for (List<Integer> attractor : attractors) {
            long size = attractor.size();
            sumOfSquares += size * size;
        }
        return (double) sumOfSquares / attractors.size();
    }
}