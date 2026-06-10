package PSBN.Processors;

import com.gitlab.jpp.Processor;

import PSBN.util.RobustnessTables;
import PSBN.util.SBNP;

import java.util.concurrent.ConcurrentHashMap;

/**
 * Calcule, pour chaque SBNP, des statistiques de robustesse/evolvabilite a la
 * Wagner (2008), le "phenotype" etant le tuple des fonctions de transition
 * (f_1,...,f_n).
 *
 * f_j ne depend que de la colonne j de la matrice de poids, et l'ensemble des
 * genotypes realisant (f_1,...,f_n) est le produit cartesien
 * ColumnSet(f_1) x ... x ColumnSet(f_n) (colonnes independantes). Sous
 * distribution uniforme sur ce produit, R_P_mean, R_P_std et E_P se
 * decomposent en sommes de quantites par colonne, precalculees une fois par
 * dimension n dans RobustnessTables :
 *
 * - R_P_mean = somme_j g(f_j)
 * - R_P_std  = sqrt(somme_j var(f_j))
 * - E_P      = somme_j nf(f_j)
 *
 * Ce calcul est exact (pas un echantillonnage) et ne necessite aucun appel a
 * clingo.
 */
public class Statifier implements Processor<SBNP, String> {

    private final ConcurrentHashMap<Integer, RobustnessTables> tablesByDimension = new ConcurrentHashMap<>();

    @Override
    public void reset() {
        tablesByDimension.clear();
    }

    @Override
    public String process(SBNP input) {
        int n = input.getDimension();
        int[] f = input.transitionFunctionCodes();

        RobustnessTables tables = tablesByDimension.computeIfAbsent(n, RobustnessTables::compute);

        double rPMean = 0;
        double rPVar = 0;
        int eP = 0;
        for (int code : f) {
            rPMean += tables.g(code);
            rPVar += tables.var(code);
            eP += tables.nf(code);
        }

        return input.toString() + "," + rPMean + "," + Math.sqrt(rPVar) + "," + eP;
    }
}
