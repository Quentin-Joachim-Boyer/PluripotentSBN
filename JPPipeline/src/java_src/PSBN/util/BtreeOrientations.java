package PSBN.util;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;

/**
 * Enumeration des formes d'arbres de decomposition (btree) d'un vecteur donne.
 *
 * Un vecteur de decomposition SOUS-DETERMINE l'arbre : un vecteur asymetrique
 * (ex. {@code <0,1,2>}) admet plusieurs orientations distinctes selon la
 * repartition des feuilles entre sous-arbres gauche/droit. Chaque orientation
 * capture des dynamiques differentes (le contexte "noeud de controle actif" a
 * droite differe de "inactif" a gauche), donc l'unite d'enumeration correcte
 * est l'arbre, pas le vecteur.
 *
 * Ce calcul est l'exact pendant Java de {@code btree_terms} dans
 * gen_setup_btree.py : il doit produire le MEME nombre d'orientations, pour que
 * l'index {@code o} cote pipeline corresponde aux faits btree generes cote ASP.
 */
public final class BtreeOrientations {

    private BtreeOrientations() {}

    /**
     * Nombre d'orientations d'arbre distinctes pour ce vecteur.
     * @param vec vec[i] = nombre de sous-dynamiques de dimension (n - i)
     * @param n   dimension du reseau
     */
    public static int orientationCount(int[] vec, int n) {
        TreeMap<Integer, Integer> counts = new TreeMap<>();
        for (int i = 0; i < vec.length; i++) {
            int d = n - i;
            if (vec[i] > 0) counts.put(d, vec[i]);
        }
        return build(n, counts).size();
    }

    private static long volume(Map<Integer, Integer> counts) {
        long v = 0;
        for (Map.Entry<Integer, Integer> e : counts.entrySet()) {
            v += (long) e.getValue() * (1L << e.getKey());
        }
        return v;
    }

    /** Toutes les formes d'arbres (chaines btree/4) realisant `counts` a la dimension `dim`. */
    private static Set<String> build(int dim, TreeMap<Integer, Integer> counts) {
        Set<String> out = new TreeSet<>();
        // Cas feuille : une seule sous-dynamique, exactement de dimension `dim`.
        if (counts.size() == 1 && counts.containsKey(dim) && counts.get(dim) == 1) {
            out.add("btree(nil,nil," + dim + ",nil)");
            return out;
        }
        // Sinon : noeud de controle scindant en deux sous-arbres de dim-1,
        // chacun de volume 2^(dim-1).
        long half = 1L << (dim - 1);
        for (TreeMap<Integer, Integer> left : subMultisetsWithVol(counts, half)) {
            TreeMap<Integer, Integer> right = new TreeMap<>();
            for (Map.Entry<Integer, Integer> e : counts.entrySet()) {
                int rem = e.getValue() - left.getOrDefault(e.getKey(), 0);
                if (rem > 0) right.put(e.getKey(), rem);
            }
            for (String l : build(dim - 1, left)) {
                for (String r : build(dim - 1, right)) {
                    out.add("btree(" + l + "," + r + "," + dim + ",nil)");
                }
            }
        }
        return out;
    }

    /** Tous les sous-multiensembles de `counts` de volume exactement `target`. */
    private static List<TreeMap<Integer, Integer>> subMultisetsWithVol(
            TreeMap<Integer, Integer> counts, long target) {
        List<Integer> dims = new ArrayList<>(counts.keySet());
        List<TreeMap<Integer, Integer>> result = new ArrayList<>();
        pick(dims, 0, counts, new TreeMap<>(), target, result);
        return result;
    }

    private static void pick(List<Integer> dims, int idx, TreeMap<Integer, Integer> counts,
                             TreeMap<Integer, Integer> chosen, long target,
                             List<TreeMap<Integer, Integer>> result) {
        if (idx == dims.size()) {
            if (volume(chosen) == target) result.add(new TreeMap<>(chosen));
            return;
        }
        int d = dims.get(idx);
        for (int k = 0; k <= counts.get(d); k++) {
            if (k > 0) chosen.put(d, k); else chosen.remove(d);
            if (volume(chosen) <= target) {
                pick(dims, idx + 1, counts, chosen, target, result);
            }
        }
        chosen.remove(d);
    }
}
