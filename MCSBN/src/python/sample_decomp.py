#!/usr/bin/env python3
"""
sample_decomp.py — echantillonne des dynamiques d'un VECTEUR DE DECOMPOSITION
fixe (prototype), au lieu de balayer aveuglement (SBF_n)^n.

Motivation. Le Monte-Carlo uniforme gaspille l'essentiel de ses tirages sur des
dynamiques irreductibles <1,0,...,0> (90.9% en d=3, 98.9% en d=4) : les classes
decomposables — celles qui portent la structure de pluripotence — sont rares et
petites. On les vise donc directement.

Principe (correct par construction, reutilise tout MCSBN).
  Une dynamique est decomposable SSI au moins un noeud c est globalement
  invariant, c.-a-d. f_c = projection_c (f_c(s) = x_c partout). On force donc
  `force` noeuds a etre des projections (proposition structuree qui atterrit dans
  la region decomposable), on echantillonne les autres colonnes normalement
  (espace des poids -> SBN toujours valide), puis on FILTRE sur le vecteur de
  decomposition exact calcule par MCSBN. Aucun risque de produire une dynamique
  invalide ou hors-cible : le filtre est l'oracle.

  Heuristique du nombre de noeuds forces : un arbre binaire a `L` feuilles a
  `L-1` noeuds internes (= noeuds de controle), donc force = (somme des v_k) - 1
  par defaut, plafonne a n-1.

Sortie : meme format CSV que mcsbn.py (passe ensuite dans add_metagraph_layout).

Usage :
  python sample_decomp.py -d 4 --vector 0,2,0,0,0 -n 50000 -o out.csv
"""

import argparse
import sys

from mcsbn import Generator, open_out, vector_from_counts  # noqa: F401
from sbf import threshold_tt


def proj_index(gen, c):
    """Index, dans la table SBF, de la projection_c (f(s) = bit c de s)."""
    tt = 0
    for s in range(gen.N):
        if (s >> c) & 1:
            tt |= (1 << s)
    # table.keys = liste des tt ; on construit l'index inverse une fois.
    return gen._tt_to_idx[tt]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-d", "--dim", type=int, required=True)
    ap.add_argument("--vector", required=True,
                    help="vecteur cible v_n,...,v_0 (ex. 0,2,0,0,0)")
    ap.add_argument("-n", "--num", type=int, default=10000,
                    help="nb de dynamiques DISTINCTES voulues (def 10000)")
    ap.add_argument("-o", "--output", default="-")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--measure", choices=("variety", "genotype"), default="variety")
    ap.add_argument("--force", type=int, default=-1,
                    help="nb de noeuds forces invariants (def: total_feuilles-1)")
    ap.add_argument("--max-draws", type=int, default=0,
                    help="plafond de tirages (0 = illimite)")
    ap.add_argument("--no-weights", action="store_true")
    args = ap.parse_args()

    n = args.dim
    target = args.vector.strip()
    target_list = [int(x) for x in target.split(",")]
    if len(target_list) != n + 1:
        sys.exit("le vecteur doit avoir n+1=%d composantes" % (n + 1))
    total_leaves = sum(target_list)
    force = args.force if args.force >= 0 else max(1, total_leaves - 1)
    force = min(force, n)  # on ne peut pas forcer plus de n noeuds

    gen = Generator(n, args.measure, args.seed, include_weights=not args.no_weights)
    gen._tt_to_idx = {tt: i for i, tt in enumerate(gen.sbf_tt)}
    proj = [proj_index(gen, c) for c in range(n)]
    rng = gen.rng

    target_prefix = ",".join(str(x) for x in target_list)

    out = open_out(args.output)
    out.write(gen.header() + "\n")

    seen = set()
    draws = 0
    kept = 0
    M = gen.M
    while kept < args.num:
        if args.max_draws and draws >= args.max_draws:
            break
        draws += 1
        idx = [rng.randrange(M) for _ in range(n)]
        # force `force` noeuds distincts a etre des projections (invariants)
        nodes = rng.sample(range(n), force)
        for c in nodes:
            idx[c] = proj[c]
        csv_row, f = gen.row(idx)
        # le vecteur est le prefixe (n+1 premiers champs) de la ligne
        vec = csv_row.split(",", n + 1)[:n + 1]
        if ",".join(vec) != target_prefix:
            continue
        if f in seen:
            continue
        seen.add(f)
        kept += 1
        out.write(csv_row + "\n")

    if out is not sys.stdout:
        out.close()

    rate = 100.0 * kept / draws if draws else 0.0
    distinct_hit = 100.0 * len(seen) / draws if draws else 0.0
    sys.stderr.write(
        "cible <%s>  force=%d  tirages=%d  gardes(distincts)=%d  "
        "acceptation=%.2f%%  (distinctes/tirage=%.2f%%)\n"
        % (target, force, draws, kept, rate, distinct_hit))


if __name__ == "__main__":
    main()
