#!/usr/bin/env python3
"""
core_then_walk.py — paysage hybride pour metagraph.html :

  Phase 1 (coeur) : enumere EXHAUSTIVEMENT les dynamiques les plus DECOMPOSEES
    (vecteur a `decompSum` = nombre de feuilles maximal — le coeur pluripotent),
    jusqu'a un seuil de M dynamiques.
  Phase 2 (voisinage) : depuis ce coeur, lance des marches aleatoires sur le
    metagraphe (genere a la volee) pour explorer le voisinage connexe jusqu'a un
    total de n dynamiques.

Pourquoi ce decoupage. Le coeur tres decompose est rare et petit : on peut le
couvrir entierement (dense). Le reste du paysage se decouvre par marche, ce qui
donne les liens PAR CONSTRUCTION (cf. explore_metagraph.py). On obtient donc un
coeur pluripotent complet, immerge dans un voisinage connexe et representatif.

Phase 1, methode. Une dynamique decomposable a >=1 noeud invariant (f_c = proj_c).
Plus elle est decomposee, plus elle a de structure de controle. On enumere donc
par nombre de noeuds FORCES invariants k decroissant (n, n-1, ... >= min_force) :
forcer k projections + balayer les n-k colonnes libres sur toutes les SBF, puis
calculer le vecteur EXACT (Decomposer) et dedupliquer. Les niveaux a k eleve sont
peu nombreux et donnent les dynamiques les plus profondes en premier. On garde
les M a plus grand decompSum.

  Limite : forcer k projections globales ne produit que des arbres "equilibres"
  (controles globaux). Les classes profondes "en epine" (1 seul invariant global,
  ex. <0,1,1,1,2>) n'apparaissent qu'a min_force=1 — cher en d>=4. En d<=3,
  min_force=1 est trivial et l'enumeration est exacte/complete.

Sortie : meme format CSV que mcsbn.py -> add_metagraph_layout -> metagraph.html.

Usage :
  python core_then_walk.py -d 3 -M 3000 -n 30000 -o out.csv
  python core_then_walk.py -d 4 -M 20000 -n 80000 --min-force 2 -o out.csv
"""

import argparse
import sys
from itertools import combinations, product

from mcsbn import Generator, open_out
from sbf import get_neighbor_map


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-d", "--dim", type=int, required=True)
    ap.add_argument("-M", "--core", type=int, default=3000,
                    help="taille max du coeur exhaustif (def 3000)")
    ap.add_argument("-n", "--num", type=int, default=30000,
                    help="total de dynamiques distinctes voulu (def 30000)")
    ap.add_argument("-o", "--output", default="-")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--min-force", type=int, default=-1,
                    help="niveau min de noeuds forces invariants en phase 1 "
                         "(def: 1 si n<=3, sinon 2)")
    ap.add_argument("--fanout", type=int, default=4,
                    help="voisins nouveaux pris par noeud a chaque couche de "
                         "l'expansion de frontiere (def 4 ; petit = pourtour fin)")
    ap.add_argument("--measure", choices=("variety", "genotype"), default="variety")
    ap.add_argument("--no-weights", action="store_true")
    args = ap.parse_args()

    n = args.dim
    gen = Generator(n, args.measure, args.seed, include_weights=not args.no_weights)
    rng = gen.rng
    M_idx = gen.M

    # Graphe des SBF en indices (pour la marche) + projections (pour le coeur).
    tt_to_idx = {tt: i for i, tt in enumerate(gen.sbf_tt)}
    nmap = get_neighbor_map(n)
    nbr_idx = [[tt_to_idx[t] for t in nmap.get(gen.sbf_tt[i], ())] for i in range(M_idx)]
    deg_sbf = [len(x) for x in nbr_idx]
    proj = []
    for c in range(n):
        tt = 0
        for s in range(gen.N):
            if (s >> c) & 1:
                tt |= (1 << s)
        proj.append(tt_to_idx[tt])

    min_force = args.min_force if args.min_force >= 0 else (1 if n <= 3 else 2)
    irr = ["1"] + ["0"] * n

    # ── Phase 1 : coeur exhaustif des plus decomposes ──────────────────────────
    sys.stderr.write("[phase 1] coeur exhaustif (min_force=%d) ...\n" % min_force)
    core = {}   # signature f -> (decompSum, idx_tuple, csv_row)

    def consider(idx):
        csv_row, f = gen.row(idx)
        if f in core:
            return
        vec = csv_row.split(",", n + 1)[:n + 1]
        if vec == irr:
            return
        dsum = sum(int(x) for x in vec)
        core[f] = (dsum, tuple(idx), csv_row)

    for k in range(n, min_force - 1, -1):
        for S in combinations(range(n), k):
            free = [j for j in range(n) if j not in S]
            base = [0] * n
            for c in S:
                base[c] = proj[c]
            for combo in product(range(M_idx), repeat=len(free)):
                idx = base[:]
                for pos, j in enumerate(free):
                    idx[j] = combo[pos]
                consider(idx)

    # garder les M a plus grand decompSum
    ordered = sorted(core.values(), key=lambda t: -t[0])
    if len(ordered) > args.core:
        ordered = ordered[:args.core]
    sys.stderr.write("      decomposables trouves=%d  coeur garde=%d  "
                     "(decompSum %d..%d)\n"
                     % (len(core), len(ordered),
                        ordered[-1][0] if ordered else 0,
                        ordered[0][0] if ordered else 0))

    out = open_out(args.output)
    out.write(gen.header() + "\n")
    seen = set()                          # cle = tuple(idx) (== la dynamique)
    frontier = []                         # noeuds dont on explorera les voisins
    for dsum, idx, csv_row in ordered:
        key = tuple(idx)
        if key in seen:
            continue
        seen.add(key)
        frontier.append(key)
        out.write(csv_row + "\n")

    # ── Phase 2 : expansion de FRONTIERE autour du coeur ───────────────────────
    # On ne fait pas une longue chaine depuis un seul point (qui derive en ligne) :
    # on traite tout le front (d'abord TOUS les noeuds du coeur), en prenant
    # `fanout` voisins NOUVEAUX par noeud, couche par couche. Le pourtour du coeur
    # entier s'epaissit uniformement, puis l'exploration s'eloigne par couches.
    sys.stderr.write("[phase 2] expansion de frontiere (fanout=%d) jusqu'a n=%d ...\n"
                     % (args.fanout, args.num))

    def neighbors(idx):
        """Voisins metagraphe : changer une colonne k vers un voisin-SBF."""
        for k in range(n):
            base = idx[k]
            for j in nbr_idx[base]:
                yield idx[:k] + (j,) + idx[k + 1:]

    layer = 0
    while len(seen) < args.num and frontier:
        layer += 1
        rng.shuffle(frontier)
        nxt = []
        for base in frontier:
            if len(seen) >= args.num:
                break
            cands = list(neighbors(base))
            rng.shuffle(cands)
            taken = 0
            for cand in cands:
                if cand in seen:
                    continue
                seen.add(cand)
                nxt.append(cand)
                out.write(gen.row(list(cand))[0] + "\n")
                taken += 1
                if taken >= args.fanout or len(seen) >= args.num:
                    break
        frontier = nxt

    if out is not sys.stdout:
        out.close()
    total = len(seen)
    sys.stderr.write("      total=%d  (coeur=%d, voisinage=%d)  couches=%d\n"
                     % (total, len(ordered), total - len(ordered), layer))


if __name__ == "__main__":
    main()
