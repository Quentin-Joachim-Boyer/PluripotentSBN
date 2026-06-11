package PSBN.util;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.*;
import java.util.function.Consumer;
import java.util.regex.*;

/**
 * Helpers partages pour lancer clingcon et consommer sa sortie en flux.
 *
 * La sortie est lue ligne par ligne et chaque solution est passee a un
 * {@link Consumer} des qu'elle est parsee : on n'accumule jamais l'integralite
 * de la sortie ni la liste complete des solutions, ce qui borne la memoire
 * quelle que soit la taille de la tranche.
 */
public final class ClingconUtil {

    private static final Pattern BIT_PATTERN    = Pattern.compile("transition_function_bit\\((\\d+),(\\d+)\\)");
    private static final Pattern WEIGHT_PATTERN = Pattern.compile("w\\((\\d+),(\\d+)\\)=(-?\\d+)");

    private ClingconUtil() {
    }

    /**
     * Lance clingcon et pousse chaque SBNP trouvee vers {@code sink} au fil de la
     * lecture de la sortie.
     *
     * @param nSolutions nombre maximum de solutions (0 = toutes).
     * @param n          dimension.
     * @param dv         vecteur de decomposition attache a chaque SBNP.
     * @param sink       consommateur appele une fois par solution.
     */
    public static void stream(List<String> lpFiles, Map<String, Integer> constants, int nSolutions,
                              int n, DecompVector dv, Consumer<SBNP> sink) {
        List<String> cmd = new ArrayList<>();
        cmd.add("clingcon");
        cmd.add(String.valueOf(nSolutions));
        cmd.add("--project");
        cmd.add("--parallel");
        cmd.add("1");
        // cmd.add("--seed=" + new java.util.Random().nextInt(Integer.MAX_VALUE));
        for (Map.Entry<String, Integer> entry : constants.entrySet()) {
            cmd.add("-c");
            cmd.add(entry.getKey() + "=" + entry.getValue());
        }
        cmd.addAll(lpFiles);

        Process process = null;
        try {
            ProcessBuilder pb = new ProcessBuilder(cmd);
            process = pb.start();

            // Draine stderr dans un thread separe pour eviter le deadlock de pipe
            // (clingcon bloquerait si son tampon stderr se remplissait).
            final Process proc = process;
            final StringBuilder stderr = new StringBuilder();
            Thread errDrainer = new Thread(() -> {
                try (BufferedReader err = new BufferedReader(new InputStreamReader(proc.getErrorStream()))) {
                    String l;
                    while ((l = err.readLine()) != null) stderr.append(l).append("\n");
                } catch (Exception ignored) {
                }
            });
            errDrainer.setDaemon(true);
            errDrainer.start();

            // Lecture en flux de stdout : machine a etats sur les blocs "Answer:".
            try (BufferedReader out = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = out.readLine()) != null) {
                    if (!line.trim().startsWith("Answer:")) continue;
                    String atomsLine  = out.readLine(); // Answer+1 : atomes
                    out.readLine();                     // Answer+2 : ignoree
                    String assignLine = out.readLine(); // Answer+3 : assignation des poids
                    SBNP sbnp = buildSBNP(
                            atomsLine  == null ? "" : atomsLine.trim(),
                            assignLine == null ? "" : assignLine.trim(),
                            n, dv);
                    if (sbnp != null) sink.accept(sbnp);
                }
            }

            int exitCode = process.waitFor();
            errDrainer.join();
            if (exitCode != 10 && exitCode != 20 && exitCode != 30) {
                throw new RuntimeException(
                    "clingcon failed (exit code " + exitCode + ")\n" +
                    "Command: " + String.join(" ", cmd) + "\n" +
                    "Stderr: " + stderr.toString().trim()
                );
            }
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new RuntimeException("Failed to run clingcon: " + e.getMessage(), e);
        } finally {
            if (process != null && process.isAlive()) {
                process.destroyForcibly();
            }
        }
    }

    /**
     * Construit la SBNP a partir des lignes "Answer:" de clingcon, ou
     * {@code null} si la reponse est vide (aucune variable de poids declaree :
     * cas degenere ou {@code d(D)} n'est pas defini, ex. vecteur de
     * decomposition sans fait {@code btree(...)} associe).
     */
    private static SBNP buildSBNP(String atomsLine, String assignLine, int n, DecompVector dv) {
        if (assignLine.isEmpty()) {
            return null;
        }

        Map<Integer, Set<Integer>> bits = new HashMap<>();
        Matcher bm = BIT_PATTERN.matcher(atomsLine);
        while (bm.find()) {
            int node  = Integer.parseInt(bm.group(1));
            int state = Integer.parseInt(bm.group(2));
            bits.computeIfAbsent(node, k -> new HashSet<>()).add(state);
        }

        int[][] weights = new int[n][n];
        Matcher wm = WEIGHT_PATTERN.matcher(assignLine);
        while (wm.find()) {
            int wi  = Integer.parseInt(wm.group(1)) - 1;
            int wj  = Integer.parseInt(wm.group(2)) - 1;
            int val = Integer.parseInt(wm.group(3));
            if (wi >= 0 && wi < n && wj >= 0 && wj < n)
                weights[wi][wj] = val;
        }

        boolean[][] TT = new boolean[n][1 << n];
        for (int node = 1; node <= n; node++) {
            for (int s : bits.getOrDefault(node, Collections.emptySet())) {
                TT[node - 1][s] = true;
            }
        }

        return new SBNP(n, weights, TT, dv);
    }
}