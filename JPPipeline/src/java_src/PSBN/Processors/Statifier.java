package PSBN.Processors;

import com.gitlab.jpp.Processor;

import PSBN.util.SBFStatTable;
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
 * dimension n dans SBFStatTable :
 *
 * - R_P_mean = somme_j neutralCountMean(f_j)
 * - R_P_std  = sqrt(somme_j neutralCountVar(f_j))
 * - E_P      = somme_j nbDistinctNeighborPhenotypes(f_j)
 *
 * Le nombre de matrices de poids realisant (f_1,...,f_n) (colonne
 * "GenotypeCount" de l'output) est de meme produit_j columnSetSize(f_j).
 *
 * Attention : R_P_mean/R_P_std sont ici des comptes (nombre attendu de
 * voisins neutres / ecart-type de ce compte), pas le ratio r(g) =
 * N_neutral(g)/K de Wagner (2008) ou K = 2*n^2 est le nombre total de
 * voisins (n^2 poids, +-1 chacun). Pour obtenir le R_P et l'ecart-type au
 * sens de Wagner, diviser respectivement R_P_mean et R_P_std par 2*n^2.
 *
 * Ce calcul est exact (pas un echantillonnage) et ne necessite aucun appel a
 * clingo.
 */
public class Statifier implements Processor<SBNP, String> {

    private final ConcurrentHashMap<Integer, SBFStatTable> tablesByDimension = new ConcurrentHashMap<>();

    @Override
    public void reset() {
        tablesByDimension.clear();
    }

    @Override
    public String process(SBNP input) {
        int n = input.getDimension();
        int[] f = input.transitionFunctionCodes();

        SBFStatTable table = tablesByDimension.computeIfAbsent(n, SBFStatTable::compute);

        int gCount = 1;
        double rPMean = 0;
        double rPVar = 0;
        int eP = 0;
        for (int code : f) {
            gCount *= table.columnSetSize(code);
            rPMean += table.neutralCountMean(code);
            rPVar += table.neutralCountVar(code);
            eP += table.nbDistinctNeighborPhenotypes(code);
        }

        return input.toString() + "," + gCount +  "," + Math.sqrt(rPVar) + "," + rPMean + "," + eP;
    }
}
