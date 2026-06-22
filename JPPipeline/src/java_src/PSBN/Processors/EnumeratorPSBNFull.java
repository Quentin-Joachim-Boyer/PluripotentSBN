package PSBN.Processors;

import com.gitlab.jpp.Processor;
import com.gitlab.jpp.parameters.IntegerParameter;
import com.gitlab.jpp.parameters.StringParameter;

import PSBN.util.ClingconUtil;
import PSBN.util.DecompVector;
import PSBN.util.EnumerationResult;
import PSBN.util.SBNP;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

/**
 * Enumeration monolithique d'un vecteur, avec garde-fou.
 *
 * On tente de resoudre le vecteur entier en bornant le nombre de solutions au
 * seuil {@code threshold} (clingcon s'arrete a ce nombre). Les solutions sont
 * streamees dans un buffer plafonne au seuil. Si on tient sous le seuil, on
 * renvoie directement toutes les SBNP. Sinon, on signale un debordement : le
 * vecteur sera subdivise par masque en aval.
 */
public class EnumeratorPSBNFull implements Processor<DecompVector, EnumerationResult> {

    private final StringParameter lpFile;
    private final StringParameter setupDir;
    private final IntegerParameter nSolutions;
    private final int threshold;

    public EnumeratorPSBNFull(StringParameter lpFile, StringParameter setupDir,
                                IntegerParameter nSolutions, int threshold) {
        this.lpFile = lpFile;
        this.setupDir = setupDir;
        this.nSolutions = nSolutions;
        this.threshold = threshold;
    }

    @Override
    public void reset() {
    }

    @Override
    public EnumerationResult process(DecompVector dv) {
        int n = dv.getDimension();

        Map<String, Integer> constants = new HashMap<>();
        constants.put("d", n);
        for (int i = 0; i <= n; i++) {
            constants.put("v" + (n - i), dv.get(i));
        }

        // Cap effectif : on ne demande jamais plus que le seuil de garde-fou.
        int userN = nSolutions.getValue();
        boolean guardBinds = (userN <= 0) || (userN > threshold);
        int cap = guardBinds ? threshold : userN;

        String setupFile = setupDir.getText() + "/setup_btree_" + n + "d.lp";
        ArrayList<SBNP> solutions = new ArrayList<>();
        ClingconUtil.stream(
                Arrays.asList(setupFile, lpFile.getText()),
                constants, cap, n, dv, solutions::add);

        // Garde-fou : si le seuil est la limite contraignante et qu'on l'atteint,
        // le vecteur est trop gros pour etre traite d'un bloc -> subdivision.
        if (guardBinds && solutions.size() >= threshold) {
            return EnumerationResult.overflow(dv);
        }
        return EnumerationResult.solved(dv, solutions);
    }
}