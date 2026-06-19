package PSBN.Processors;

import com.gitlab.jpp.Processor;
import com.gitlab.jpp.parameters.IntegerParameter;
import com.gitlab.jpp.parameters.Pair;
import com.gitlab.jpp.parameters.StringParameter;

import PSBN.util.ClingconUtil;
import PSBN.util.DecompVector;
import PSBN.util.RealizableSbfPrefixes;
import PSBN.util.SBNP;

import java.util.Arrays;
import java.util.BitSet;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Consumer;

/**
 * Enumeration subdivisee : fixe la fonction de transition du noeud 1 a un SBF
 * donne (cf. Subdivision.lp) pour n'explorer qu'une tranche de l'espace.
 *
 * Une tranche peut contenir un tres grand nombre de solutions, donc on les
 * streame une par une vers {@code sink} (typiquement la soumission d'une tache
 * de minimisation) sans jamais les accumuler.
 */
public class EnumeratorPSBN implements Processor<Pair<DecompVector, BitSet>, Void> {

    private final StringParameter lpFile;
    private final StringParameter setupDir;
    private final IntegerParameter nSolutions;
    private Consumer<SBNP> sink;

    public EnumeratorPSBN(StringParameter lpFile, StringParameter setupDir, IntegerParameter nSolutions) {
        this.lpFile = lpFile;
        this.setupDir = setupDir;
        this.nSolutions = nSolutions;
    }

    /** Injecte le consommateur de solutions (cf. {@code Pipe}, apres build des jobs). */
    public void setSink(Consumer<SBNP> sink) {
        this.sink = sink;
    }

    @Override
    public void reset() {
    }

    @Override
    public Void process(Pair<DecompVector, BitSet> input) {
        DecompVector dv = input.first;
        BitSet fixedPrefix = input.second;
        int n = dv.getDimension();

        Map<String, Integer> constants = new HashMap<>();
        constants.put("d", n);
        for (int i = 0; i <= n; i++) {
            constants.put("v" + (n - i), dv.get(i));
        }
        // Orientation de l'arbre (selectionne le btree dans setup_btree via `o`).
        constants.put("o", dv.getOrientation());
        // Fixe les n premiers bits (S=0..n-1) de la fonction de transition du
        // noeud 1, via les constantes fixed_sbf_bit_<s> declarees dans
        // Subdivision.lp : chaque tranche explore une partie disjointe de
        // l'espace de recherche.
        constants.put("fixed_bits", n);
        for (int s = 0; s < n; s++) {
            constants.put("fixed_sbf_bit_" + s, fixedPrefix.get(s) ? 1 : 0);
        }

        // Repartit le quota de solutions entre les tranches : sans ca, demander
        // nSolutions par tranche multiplierait le total par le nombre de
        // tranches (prefixes realisables). 0 = pas de cap, conserve tel quel.
        int userN = nSolutions.getValue();
        int cap = userN <= 0 ? 0 : Math.max(1, userN / RealizableSbfPrefixes.forDimension(n).size());

        String setupFile = setupDir.getText() + "/setup_btree_" + n + "d.lp";
        String subdivisionFile = setupDir.getText() + "/Subdivision.lp";
        ClingconUtil.stream(
                Arrays.asList(setupFile, subdivisionFile, lpFile.getText()),
                constants, cap, n, dv, sink);
        return null;
    }
}