package PSBN;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.stream.IntStream;

/**
 * Calcule toutes les distances dDA par paires entre SBNPs, en parallele.
 *
 * dDA(g, g') = sum_s dCYCLE(lim_g(s), lim_g'(s))
 *
 * ou lim_g(s) est le cycle attracteur canonique de l'etat s (colonne
 * 'dynamics' du CSV, format : etats par etat separes par '|', etats
 * d'un cycle separes par ':').
 *
 * Usage :
 *   java -cp bin:lib/jpp.jar PSBN.PairwiseDA input.csv output.csv [threshold]
 *
 * output.csv contient : id_1,id_2,dDA
 * avec uniquement les paires telles que dDA <= threshold (defaut : toutes).
 */
public class PairwiseDA {

    // ── Parsing ──────────────────────────────────────────────────────────────

    /**
     * Parse la colonne dynamics d'une ligne CSV.
     * Format : "c0|c1|...|c_{2^n-1}" ou ci = "a" ou "a:b:c" (cycle canonique).
     * Retourne un tableau de tableaux d'entiers, un par etat s.
     */
    static int[][] parseDynamics(String dynamics) {
        String[] parts = dynamics.split("\\|");
        int[][] result = new int[parts.length][];
        for (int s = 0; s < parts.length; s++) {
            String[] nums = parts[s].split(":");
            result[s] = new int[nums.length];
            for (int k = 0; k < nums.length; k++) {
                result[s][k] = Integer.parseInt(nums[k].trim());
            }
        }
        return result;
    }

    // ── Distance dCYCLE ───────────────────────────────────────────────────────

    /**
     * Distance dCYCLE d'Ai-Ling (eq. 11) entre deux cycles attracteurs.
     *
     * Si |C1| >= |C2|, on minimise sur les rotations j de C1 :
     *   sum_{i=0}^{|C2|-1} H(C1[(i+j)%|C1|], C2[i])
     *   + sum_{i=|C2|}^{|C1|-1} H(C1[(i+j)%|C1|], 0)
     *
     * H(s, s') = Integer.bitCount(s ^ s') : distance de Hamming bit-a-bit.
     * Le padding de longueur utilise l'etat nul (0), pas un sentinelle.
     */
    static int dCYCLE(int[] c1, int[] c2) {
        if (c1.length < c2.length) { int[] t = c1; c1 = c2; c2 = t; }
        int L1 = c1.length, L2 = c2.length;
        int min = Integer.MAX_VALUE;
        for (int j = 0; j < L1; j++) {
            int h = 0;
            for (int i = 0; i < L2; i++) {
                h += Integer.bitCount(c1[(i + j) % L1] ^ c2[i]);
            }
            for (int i = L2; i < L1; i++) {
                h += Integer.bitCount(c1[(i + j) % L1]); // H(etat, 0) = popcount
            }
            if (h < min) { min = h; if (min == 0) break; }
        }
        return min;
    }

    // ── Distance dDA ──────────────────────────────────────────────────────────

    /**
     * dDA(g, g') = sum_s dCYCLE(lim_g(s), lim_g'(s)).
     */
    static int dDA(int[][] dyn1, int[][] dyn2) {
        int sum = 0;
        for (int s = 0; s < dyn1.length; s++) {
            sum += dCYCLE(dyn1[s], dyn2[s]);
        }
        return sum;
    }

    // ── Lecture CSV ───────────────────────────────────────────────────────────

    /**
     * Trouve l'index de la colonne 'dynamics' dans le header CSV.
     * Gere les colonnes quotees (ex. "w_1,1") en parsant caractere par caractere.
     */
    static int findDynamicsColumn(String header) {
        List<String> cols = splitCsvHeader(header);
        for (int i = 0; i < cols.size(); i++) {
            if (cols.get(i).equals("dynamics")) return i;
        }
        throw new IllegalArgumentException("Colonne 'dynamics' introuvable dans : " + header);
    }

    static List<String> splitCsvHeader(String line) {
        List<String> result = new ArrayList<>();
        StringBuilder cur = new StringBuilder();
        boolean inQuote = false;
        for (char c : line.toCharArray()) {
            if (c == '"') {
                inQuote = !inQuote;
            } else if (c == ',' && !inQuote) {
                result.add(cur.toString());
                cur.setLength(0);
            } else {
                cur.append(c);
            }
        }
        result.add(cur.toString());
        return result;
    }

    /**
     * Extrait la colonne dynCol d'une ligne CSV de donnees.
     * Les colonnes w_i,j sont quotees ; dynamics ne l'est pas mais ne
     * contient pas de ',' (separateur intra-cycle = ':').
     * On compte les virgules hors guillemets jusqu'a la bonne colonne.
     */
    static String extractDynamicsField(String line, int dynCol) {
        int col = 0;
        int start = 0;
        boolean inQuote = false;
        for (int i = 0; i < line.length(); i++) {
            char c = line.charAt(i);
            if (c == '"') {
                inQuote = !inQuote;
            } else if (c == ',' && !inQuote) {
                if (col == dynCol) {
                    return line.substring(start, i);
                }
                col++;
                start = i + 1;
            }
        }
        // derniere colonne
        if (col == dynCol) return line.substring(start);
        throw new IllegalArgumentException("Colonne " + dynCol + " introuvable dans : " + line);
    }

    // ── Main ──────────────────────────────────────────────────────────────────

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("Usage: PairwiseDA input.csv output.csv [threshold]");
            System.exit(1);
        }
        String inputCsv = args[0];
        String outputCsv = args[1];
        int threshold = args.length >= 3 ? Integer.parseInt(args[2]) : Integer.MAX_VALUE;

        System.out.println("Lecture de " + inputCsv + " ...");
        List<int[][]> dynamicsList = new ArrayList<>();
        int dynCol = -1;

        try (BufferedReader br = new BufferedReader(new FileReader(inputCsv))) {
            String header = br.readLine();
            dynCol = findDynamicsColumn(header);
            System.out.println("Colonne 'dynamics' : index " + dynCol);
            String line;
            while ((line = br.readLine()) != null) {
                if (line.isBlank()) continue;
                String dynStr = extractDynamicsField(line, dynCol);
                dynamicsList.add(parseDynamics(dynStr));
            }
        }

        int n = dynamicsList.size();
        int[][][] dynamics = dynamicsList.toArray(new int[0][][]);
        System.out.printf("%d SBNPs charges. Calcul des %,d paires (threshold=%s) ...%n",
                n, (long) n * (n - 1) / 2,
                threshold == Integer.MAX_VALUE ? "toutes" : String.valueOf(threshold));

        ConcurrentLinkedQueue<long[]> results = new ConcurrentLinkedQueue<>();
        long startTime = System.currentTimeMillis();

        IntStream.range(0, n).parallel().forEach(i -> {
            int[][] dyni = dynamics[i];
            for (int j = i + 1; j < n; j++) {
                int d = dDA(dyni, dynamics[j]);
                if (d <= threshold) {
                    results.add(new long[]{i, j, d});
                }
            }
        });

        long elapsed = System.currentTimeMillis() - startTime;
        System.out.printf("Calcul termine en %.1f s. %,d paires retenues.%n",
                elapsed / 1000.0, (long) results.size());

        System.out.println("Ecriture de " + outputCsv + " ...");
        try (PrintWriter pw = new PrintWriter(outputCsv)) {
            pw.println("id_1,id_2,dDA");
            for (long[] row : results) {
                pw.println(row[0] + "," + row[1] + "," + row[2]);
            }
        }
        System.out.println("Termine.");
    }
}
