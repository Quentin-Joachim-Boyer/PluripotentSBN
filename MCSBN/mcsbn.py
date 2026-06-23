#!/usr/bin/env python3
"""
mcsbn.py — Generateur Monte-Carlo de SBN, format CSV compatible pipeline.

But : explorer le plus largement possible la VARIETE des dynamiques de SBN de
dimension d, avec des ressources raisonnables, en inferant toutes les proprietes
en post-traitement (aucun appel a un solveur).

  Loi de generation (le choix central)
  ------------------------------------
  Une dynamique de SBN = un n-uplet de fonctions seuil signees (SBF), une par
  noeud (les colonnes de la matrice de poids sont INDEPENDANTES, et tout n-uplet
  de SBF est realisable). L'espace des dynamiques distinctes est donc EXACTEMENT
  (SBF_n)^n.

  Pour representer fidelement la variete, on tire chaque colonne UNIFORMEMENT
  parmi les SBF DISTINCTES (mode "variety", defaut) : la loi resultante est alors
  uniforme sur l'ensemble des dynamiques distinctes. Comme cet espace est immense
  (ex. 370^4 ~ 2e10 en d=4), presque chaque tirage est une dynamique inedite :
  l'exploration est quasi-optimale (≈ 1 dynamique nouvelle par tirage).

  Un mode "genotype" tire chaque colonne proportionnellement a son nombre de
  matrices de poids (taille de ColumnSet) : la loi approche alors l'uniforme sur
  les matrices de poids (mesure "naturelle" des genotypes), au prix d'une
  exploration de la variete bien moins efficace.

  Proprietes inferees (colonnes du CSV)
  -------------------------------------
  - v_n..v_0      : vecteur de decomposition "sous controle" du reseau echantillonne
                    (cf. decompose.DecomposerW : inegalites exactes sur W). C'est
                    une propriete du GENOTYPE tire ; la pipeline rapporte, elle, le
                    maximum sur toutes les realisations d'une dynamique. Pour la
                    plupart des dynamiques (indecomposables) les deux coincident.
  - f_1..f_n      : tables de transition (bitstrings de longueur 2^n).
  - w_i,j         : une realisation exacte des poids (f_j = seuil(colonne j)).
  - CycleLenMSQ   : moyenne des (longueurs de cycle)^2 sur les attracteurs.
  - NumAttractors : nombre d'attracteurs.
  - GenotypeCount : nombre exact de matrices realisant la dynamique (produit des
                    tailles de ColumnSet ; entier potentiellement tres grand).
  - Robustness_std/mean, Evolvability : a la Wagner (2008), calcul exact par
                    colonne (cf. SBFStatTable cote pipeline).
"""

import argparse
import gzip
import random
import sys

from sbf import get_table, wbound
from decompose import DecomposerW, vector_from_counts


def cycle_lengths(succ, N):
    """Longueurs des cycles attracteurs du graphe fonctionnel s -> succ[s]."""
    state_attr = [-1] * N
    lengths = []
    for start in range(N):
        if state_attr[start] != -1:
            continue
        path = []
        pos = {}
        cur = start
        while state_attr[cur] == -1 and cur not in pos:
            pos[cur] = len(path)
            path.append(cur)
            cur = succ[cur]
        if state_attr[cur] == -1:
            clen = len(path) - pos[cur]
            lengths.append(clen)
            aid = len(lengths) - 1
            for s in path:
                state_attr[s] = aid
        else:
            a = state_attr[cur]
            for s in path:
                state_attr[s] = a
    return lengths


class Generator:
    def __init__(self, n, measure="variety", seed=0, include_weights=True):
        self.n = n
        self.N = 1 << n
        self.measure = measure
        self.include_weights = include_weights
        self.rng = random.Random(seed)

        table = get_table(n)
        self.table = table
        self.sbf_tt = table.keys
        self.M = len(self.sbf_tt)
        self.repr_col = [table.repr_col[tt] for tt in self.sbf_tt]
        self.csize = [table.column_set_size[tt] for tt in self.sbf_tt]
        self.nmean = [table.neutral_mean[tt] for tt in self.sbf_tt]
        self.nvar = [table.neutral_var[tt] for tt in self.sbf_tt]
        self.evol = [table.evolvability[tt] for tt in self.sbf_tt]

        # Constante de normalisation K (Wagner 2008) : nombre total de voisins de
        # la matrice de poids = n*n poids, chacun mutable vers (domainSize-1) valeurs.
        domain_size = 2 * wbound(n) + 1
        self.K = n * n * (domain_size - 1)

        self.decomposer = DecomposerW(n)

        if measure == "genotype":
            # Poids cumulatifs pour le tirage proportionnel a |ColumnSet|.
            self._cum = []
            acc = 0
            for c in self.csize:
                acc += c
                self._cum.append(acc)
            self._tot = acc

    def _sample_indices(self):
        n = self.n
        if self.measure == "variety":
            r = self.rng.randrange
            M = self.M
            return [r(M) for _ in range(n)]
        # genotype : tirage proportionnel a la taille de ColumnSet.
        from bisect import bisect_right
        cum = self._cum
        tot = self._tot
        rnd = self.rng.random
        return [bisect_right(cum, rnd() * tot) for _ in range(n)]

    def header(self):
        n = self.n
        cols = ["v_%d" % (n - i) for i in range(n + 1)]
        if self.include_weights:
            cols += ["f_%d" % j for j in range(1, n + 1)]
            for i in range(1, n + 1):
                for j in range(1, n + 1):
                    cols.append('"w_%d,%d"' % (i, j))
        cols += ["CycleLenMSQ", "NumAttractors", "GenotypeCount",
                 "Robustness_std", "Robustness_mean", "Evolvability"]
        return ",".join(cols)

    def row(self, idx):
        """Construit la ligne CSV pour le n-uplet de SBF d'indices `idx`."""
        n = self.n
        N = self.N
        f = [self.sbf_tt[idx[j]] for j in range(n)]   # f[j] table de verite noeud j
        cols = [self.repr_col[idx[j]] for j in range(n)]  # colonne j = poids vers j

        # Matrice W[i][j] = poids i -> j = cols[j][i].
        W = [[cols[j][i] for j in range(n)] for i in range(n)]

        # Etats successeurs : bit j de succ[s] = f_j(s).
        succ = [0] * N
        for s in range(N):
            nx = 0
            for j in range(n):
                if (f[j] >> s) & 1:
                    nx |= (1 << j)
            succ[s] = nx

        lengths = cycle_lengths(succ, N)
        num_attr = len(lengths)
        cyclemsq = sum(L * L for L in lengths) / num_attr

        gcount = 1
        rmean = 0.0
        rvar = 0.0
        evol = 0
        for j in range(n):
            ij = idx[j]
            gcount *= self.csize[ij]
            rmean += self.nmean[ij]
            rvar += self.nvar[ij]
            evol += self.evol[ij]
        r_std = (rvar ** 0.5) / self.K
        r_mean = rmean / self.K

        counts = self.decomposer.finest(W)
        vec = vector_from_counts(counts, n)

        parts = [str(x) for x in vec]
        if self.include_weights:
            for j in range(n):
                parts.append("".join('1' if (f[j] >> s) & 1 else '0' for s in range(N)))
            for i in range(n):
                for j in range(n):
                    parts.append(str(W[i][j]))
        parts.append(repr(cyclemsq))
        parts.append(str(num_attr))
        parts.append(str(gcount))
        parts.append(repr(r_std))
        parts.append(repr(r_mean))
        parts.append(str(evol))
        return ",".join(parts), tuple(f)


def open_out(path):
    if path == "-" or path is None:
        return sys.stdout
    if path.endswith(".gz"):
        return gzip.open(path, "wt", newline="")
    return open(path, "w", newline="")


def run(args):
    gen = Generator(args.d, measure=args.measure, seed=args.seed,
                    include_weights=not args.no_weights)
    out = open_out(args.o)
    try:
        out.write(gen.header() + "\n")
        seen = set()
        n_written = 0

        if args.exhaustive:
            from itertools import product
            space = gen.M ** args.d
            if space > args.max_exhaustive:
                sys.stderr.write(
                    "Espace exhaustif trop grand (%d > %d). Utilise le mode "
                    "echantillonne (retire --exhaustive).\n" % (space, args.max_exhaustive))
                return 1
            for idx in product(range(gen.M), repeat=args.d):
                line, key = gen.row(list(idx))
                out.write(line + "\n")
                n_written += 1
            sys.stderr.write("Exhaustif : %d dynamiques distinctes (= %d^%d).\n"
                             % (n_written, gen.M, args.d))
            return 0

        target = args.n
        max_draws = args.max_draws if args.max_draws > 0 else target * 50
        draws = 0
        stale = 0
        while n_written < target and draws < max_draws:
            idx = gen._sample_indices()
            draws += 1
            line, key = gen.row(idx)
            if key in seen:
                stale += 1
                # Arret anticipe si l'espace est manifestement epuise.
                if stale > 200000 and stale > 20 * (n_written + 1):
                    sys.stderr.write(
                        "Espace probablement epuise (%d distinctes, %d tirages).\n"
                        % (n_written, draws))
                    break
                continue
            stale = 0
            seen.add(key)
            out.write(line + "\n")
            n_written += 1
        sys.stderr.write("%d dynamiques distinctes en %d tirages (%.1f%% de nouveaute).\n"
                         % (n_written, draws, 100.0 * n_written / max(draws, 1)))
        return 0
    finally:
        if out is not sys.stdout:
            out.close()


def main():
    p = argparse.ArgumentParser(description="Generateur Monte-Carlo de SBN (CSV pipeline).")
    p.add_argument("-d", type=int, required=True, help="dimension du reseau")
    p.add_argument("-n", type=int, default=100000,
                   help="nombre de dynamiques distinctes a produire (mode echantillonne)")
    p.add_argument("-o", type=str, default="-",
                   help="fichier de sortie (.gz supporte), ou '-' pour stdout")
    p.add_argument("--measure", choices=["variety", "genotype"], default="variety",
                   help="loi de tirage des colonnes (defaut: variety)")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--max-draws", type=int, default=0,
                   help="plafond de tirages (defaut: 50*n)")
    p.add_argument("--exhaustive", action="store_true",
                   help="enumere TOUTES les dynamiques (petites dimensions seulement)")
    p.add_argument("--max-exhaustive", type=int, default=5_000_000,
                   help="garde-fou sur la taille de l'enumeration exhaustive")
    p.add_argument("--no-weights", action="store_true",
                   help="omet f_* et w_* (CSV plus compact)")
    args = p.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
