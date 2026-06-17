package PSBN.Processors;

import com.gitlab.jpp.Processor;
import com.gitlab.jpp.parameters.IntegerParameter;

import PSBN.util.SBFStatTable;
import PSBN.util.SBNP;

import java.util.BitSet;
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
 * - R_P_mean = somme_j neutralCountMean(f_j) / K
 * - R_P_std  = sqrt(somme_j neutralCountVar(f_j)) / K
 * - E_P      = somme_j nbDistinctNeighborPhenotypes(f_j)
 *
 * Le nombre de matrices de poids realisant (f_1,...,f_n) (colonne
 * "GenotypeCount" de l'output) est de meme produit_j columnSetSize(f_j).
 *
 * R_P_mean/R_P_std sont normalises au sens de Wagner (2008) : r(g) =
 * N_neutral(g)/K, avec K = n * SBFStatTable.neighborCount() le nombre total
 * de voisins (n poids par colonne, chacun mutable vers toute autre valeur de
 * [-w_bound,w_bound], somme sur les n colonnes). R_P_mean = moyenne_g[r(g)]
 * et R_P_std son ecart-type, sur les genotypes g realisant le phenotype
 * (f_1,...,f_n).
 *
 * Ce calcul est exact (pas un echantillonnage) et ne necessite aucun appel a
 * clingo.
 */
public class Statifier implements Processor<SBNP, String> {

    private final ConcurrentHashMap<Integer, SBFStatTable> tablesByDimension = new ConcurrentHashMap<>();
    private final IntegerParameter includeWeightsAndTransitions;

    public Statifier(IntegerParameter includeWeightsAndTransitions) {
        this.includeWeightsAndTransitions = includeWeightsAndTransitions;
    }

    @Override
    public void reset() {
        tablesByDimension.clear();
    }

    @Override
    public String process(SBNP input) {
        int n = input.getDimension();
        BitSet[] f = input.sbfCodes();

        SBFStatTable table = tablesByDimension.computeIfAbsent(n, SBFStatTable::compute);

        // GenotypeCount = produit_j columnSetSize(f_j). Ce produit peut depasser
        // largement int et meme long pour n eleve (borne ~ (13^n)^n), d'ou un
        // BigInteger pour rester exact.
        java.math.BigInteger gCount = java.math.BigInteger.ONE;
        double rPMean = 0;
        double rPVar = 0;
        int eP = 0;
        for (BitSet code : f) {
            gCount = gCount.multiply(java.math.BigInteger.valueOf(table.columnSetSize(code)));
            rPMean += table.neutralCountMean(code);
            rPVar += table.neutralCountVar(code);
            eP += table.nbDistinctNeighborPhenotypes(code);
        }

        // Normalisation a la Wagner (2008) : r(g) = N_neutral(g)/K. rPMean est
        // une somme sur les n colonnes de neutralCountMean(f_j), chacune
        // comptant table.neighborCount() voisins ; K est donc le total sur
        // les n colonnes.
        double k = n * (double) table.neighborCount();

        return input.toCsvRow(includeWeightsAndTransitions.getValue() != 0)
                + "," + gCount + "," + (Math.sqrt(rPVar) / k) + "," + (rPMean / k) + "," + eP;
    }
}
