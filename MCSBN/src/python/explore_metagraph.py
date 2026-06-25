#!/usr/bin/env python3
"""
explore_metagraph.py — echantillonne une REGION CONNEXE du metagraphe par une
marche de Metropolis-Hastings, amorcee sur la pluripotence.

Pourquoi pas un tirage i.i.d. ? Le degre moyen d'un echantillon i.i.d. du
metagraphe est proportionnel a la fraction tiree (degre ~ deg_complet * N/Ntot) :
en d=4 il faudrait ~200M de noeuds pour seulement percoler. Variete (i.i.d.) et
liens (densite) sont donc structurellement opposes sous tirage independant.

Structure exploitee. Le metagraphe est le PRODUIT CARTESIEN n-fois du petit
graphe des SBF G (32 noeuds en d=3, 370 en d=4) : deux dynamiques sont voisines
ssi elles different sur UNE colonne f_k, vers un voisin dans G. Donc :
  * les voisins de n'importe quelle dynamique se generent a la volee (G est en
    cache, cf. sbf.get_neighbor_map) — pas besoin de materialiser 10^10 noeuds ;
  * le vrai metagraphe est connexe : on en extrait une region connexe en
    l'explorant, ce qui donne les liens PAR CONSTRUCTION.

Marche de Metropolis-Hastings vers l'uniforme sur les dynamiques distinctes.
  Proposition : changer une colonne k (tiree proportionnellement a deg_G) vers un
  voisin-SBF uniforme -> q(u->v) = 1/deg(u). Acceptation min(1, deg(u)/deg(v)) :
  la stationnaire est uniforme (fidele a la variete), tout en restant connexe.
  deg(u) = somme_k deg_G(colonne_k de u).

Amorce sur la pluripotence : la graine est une dynamique DECOMPOSABLE (un noeud
force a la projection -> invariant -> decomposable). La marche s'eloigne ensuite
dans le bulk irreductible (~99%), donc le coeur pluripotent apparait, connexe et
a sa vraie proportion, au centre du voisinage. metagraph.html colore par vecteur
de decomposition : meme minoritaire, la pluripotence ressort.

Sortie : meme format CSV que mcsbn.py -> directement utilisable par
add_metagraph_layout puis metagraph.html.

Usage :
  python explore_metagraph.py -d 4 -n 50000 -o out.csv
  python explore_metagraph.py -d 4 -n 80000 --seed-vector 0,0,4,0,0 -o out.csv
"""

import argparse
import sys

from mcsbn import Generator, open_out
from sbf import get_neighbor_map


def build_seed(gen, proj, seed_vector, rng):
    """Une dynamique decomposable (idx-tuple) ; si seed_vector, de cette classe."""
    n = gen.n
    M = gen.M
    target = ",".join(seed_vector) if seed_vector else None
    while True:
        idx = [rng.randrange(M) for _ in range(n)]
        c = rng.randrange(n)
        idx[c] = proj[c]                      # noeud invariant -> decomposable
        csv_row, _ = gen.row(idx)
        vec = csv_row.split(",", n + 1)[:n + 1]
        if target is not None:
            if ",".join(vec) == target:
                return idx
        elif vec != (["1"] + ["0"] * n):       # tout sauf irreductible <1,0,...>
            return idx


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-d", "--dim", type=int, required=True)
    ap.add_argument("-n", "--num", type=int, default=50000,
                    help="nb de dynamiques DISTINCTES a collecter (def 50000)")
    ap.add_argument("-o", "--output", default="-")
    ap.add_argument("--seed", type=int, default=0, help="graine RNG")
    ap.add_argument("--seed-vector", default=None,
                    help="classe de la dynamique d'amorce (ex. 0,0,4,0,0)")
    ap.add_argument("--seeds", type=int, default=1,
                    help="nb de points d'amorce (marches concatenees)")
    ap.add_argument("--max-steps", type=int, default=0,
                    help="plafond de pas par marche (0 = 50*num)")
    ap.add_argument("--measure", choices=("variety", "genotype"), default="variety")
    ap.add_argument("--no-weights", action="store_true")
    args = ap.parse_args()

    n = args.dim
    gen = Generator(n, args.measure, args.seed, include_weights=not args.no_weights)
    rng = gen.rng
    M = gen.M

    # Graphe des SBF en indices : nbr_idx[i] = indices voisins, deg_sbf[i] = degre.
    tt_to_idx = {tt: i for i, tt in enumerate(gen.sbf_tt)}
    nmap = get_neighbor_map(n)
    nbr_idx = [[tt_to_idx[t] for t in nmap.get(gen.sbf_tt[i], ())] for i in range(M)]
    deg_sbf = [len(x) for x in nbr_idx]

    # Projections (pour amorcer sur du decomposable).
    proj = []
    for c in range(n):
        tt = 0
        for s in range(gen.N):
            if (s >> c) & 1:
                tt |= (1 << s)
        proj.append(tt_to_idx[tt])

    seed_vec = args.seed_vector.split(",") if args.seed_vector else None
    max_steps = args.max_steps or (50 * args.num)

    out = open_out(args.output)
    out.write(gen.header() + "\n")

    seen = set()
    n_decomp = 0
    steps_total = 0

    def node_deg(idx):
        return sum(deg_sbf[i] for i in idx)

    for _ in range(args.seeds):
        if len(seen) >= args.num:
            break
        idx = build_seed(gen, proj, seed_vec, rng)
        cur_deg = node_deg(idx)
        steps = 0
        while len(seen) < args.num and steps < max_steps:
            steps += 1
            steps_total += 1
            # collecte le noeud courant s'il est nouveau
            key = tuple(idx)
            if key not in seen:
                seen.add(key)
                csv_row, _ = gen.row(idx)
                vec = csv_row.split(",", n + 1)[:n + 1]
                if vec != (["1"] + ["0"] * n):
                    n_decomp += 1
                out.write(csv_row + "\n")
            # proposition MH : colonne k ~ deg_G, voisin uniforme
            r = rng.random() * cur_deg
            k = 0
            acc = deg_sbf[idx[0]]
            while acc < r and k < n - 1:
                k += 1
                acc += deg_sbf[idx[k]]
            old = idx[k]
            new = nbr_idx[old][rng.randrange(deg_sbf[old])]
            prop_deg = cur_deg - deg_sbf[old] + deg_sbf[new]
            # accept min(1, deg(cur)/deg(prop))
            if prop_deg <= cur_deg or rng.random() < cur_deg / prop_deg:
                idx[k] = new
                cur_deg = prop_deg

    if out is not sys.stdout:
        out.close()

    collected = len(seen)
    sys.stderr.write(
        "collectes=%d  decomposables=%d (%.2f%%)  pas=%d  (%.1f pas/noeud)\n"
        % (collected, n_decomp, 100.0 * n_decomp / max(1, collected),
           steps_total, steps_total / max(1, collected)))


if __name__ == "__main__":
    main()
