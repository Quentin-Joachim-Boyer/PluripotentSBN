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

Phase 1, methode (cf. core_tree_enum.py). On enumere les ARBRES DE CONTROLE : a
chaque face on force un noeud de controle a etre invariant SUR CETTE FACE (pas
seulement globalement). Au niveau dynamique tout n-uplet de SBF est valide (les
colonnes sont independantes), donc cette construction est libre de tout couplage.
Avantage decisif sur l'ancien forcage de projections GLOBALES : on couvre AUSSI
les classes profondes "en epine"/asymetriques (controles non-globaux) — ~47% du
coeur profond en d=4 que l'ancien manquait. Les dynamiques tres decomposees ont
peu de noeuds libres, donc l'enumeration du coeur profond est bon marche
(max_free=0 suffit a etre complet en haut ; verifie : identique a max_free=1 pour
dsum>=9 en d=4).

Sortie : meme format CSV que mcsbn.py -> add_metagraph_layout -> metagraph.html.

Usage :
  python core_then_walk.py -d 3 -M 3000 -n 30000 -o out.csv
  python core_then_walk.py -d 4 -M 20000 -n 80000 --min-leaves 8 -o out.csv
"""

import argparse
import os
import subprocess
import sys

from mcsbn import Generator, open_out
from sbf import get_neighbor_map
from core_tree_enum import enumerate_core


def _locate_core_bin(opt):
    """Chemin du binaire C pour la phase 1, ou None pour l'enumerateur Python."""
    if opt == "none":
        return None
    if opt != "auto":
        if not os.path.exists(opt):
            sys.exit("--core-bin introuvable : " + opt)
        return opt
    here = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.normpath(os.path.join(here, "..", "..", "bin", "mcsbn"))
    return cand if os.path.exists(cand) else None


def _phase1_via_c(core_bin, n, min_leaves, max_free, M, no_weights, tt_to_idx):
    """Lance `mcsbn --core-trees`, lit le coeur, et renvoie une liste triee
    (decompSum, idx_tuple, csv_row). On force les poids cote C (pour reconstruire
    les indices via f_*), et on retaille la ligne selon no_weights."""
    mf = -1 if max_free is None else max_free
    cmd = [core_bin, "-d", str(n), "--core-trees", "--min-leaves", str(min_leaves),
           "--max-free", str(mf), "-M", str(M), "-o", "-"]
    env = os.environ.copy()
    env["MCSBN_DIR"] = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        sys.exit("[phase 1] binaire C en echec :\n" + proc.stderr)
    sys.stderr.write(proc.stderr)        # resume [core-trees]
    nw = n * n
    ordered = []
    for line in proc.stdout.splitlines()[1:]:       # saute l'entete
        if not line:
            continue
        f = line.split(",")
        # ordre des colonnes : v_n..v_0 (n+1), f_1..f_n (n), w_* (n*n), stats (6)
        idx = tuple(tt_to_idx[int(f[n + 1 + j][::-1], 2)] for j in range(n))
        dsum = sum(int(f[i]) for i in range(n + 1))
        row = (",".join(f[:n + 1] + f[n + 1 + n + nw:])  # v_* + stats (sans f_/w_)
               if no_weights else line)
        ordered.append((dsum, idx, row))
    return ordered


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
    ap.add_argument("--min-leaves", type=int, default=-1,
                    help="phase 1 : nb min de feuilles de l'arbre de controle "
                         "(plus haut = coeur plus petit/profond ; def: 2 si n<=3, sinon 8)")
    ap.add_argument("--max-free", type=int, default=-1,
                    help="phase 1 : nb max de noeuds libres par arbre (borne le "
                         "cout ; def: illimite si n<=3, sinon 0 = complet pour le "
                         "coeur profond). Augmenter pour inclure des classes moins "
                         "decomposees (plus lent).")
    ap.add_argument("--core-bin", default="auto",
                    help="phase 1 via le binaire C (mode --core-trees, ~45x plus "
                         "rapide) : 'auto' = bin/mcsbn s'il existe, sinon Python ; "
                         "'none' force l'enumerateur Python ; ou un chemin explicite")
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

    # Graphe des SBF en indices (pour la marche de la phase 2).
    tt_to_idx = {tt: i for i, tt in enumerate(gen.sbf_tt)}
    nmap = get_neighbor_map(n)
    nbr_idx = [[tt_to_idx[t] for t in nmap.get(gen.sbf_tt[i], ())] for i in range(M_idx)]
    deg_sbf = [len(x) for x in nbr_idx]

    min_leaves = args.min_leaves if args.min_leaves >= 0 else (2 if n <= 3 else 8)
    max_free = None if args.max_free < 0 and n <= 3 else (
        args.max_free if args.max_free >= 0 else 0)

    # ── Phase 1 : coeur COMPLET des plus decomposes (arbres de controle) ───────
    # Enumeration des arbres de controle (un controle force invariant par face),
    # qui couvre AUSSI les classes profondes "en epine"/asymetriques que le
    # forcage de projections GLOBALES manquait (~47% du coeur profond en d=4).
    # Le binaire C (mode --core-trees) fait la meme chose ~45x plus vite.
    sys.stderr.write("[phase 1] coeur exhaustif (arbres ; min_leaves=%d, max_free=%s) ...\n"
                     % (min_leaves, max_free))

    core_bin = _locate_core_bin(args.core_bin)
    if core_bin:
        ordered = _phase1_via_c(core_bin, n, min_leaves, max_free, args.core,
                                args.no_weights, tt_to_idx)
    else:
        core = enumerate_core(gen, min_leaves, max_free=max_free)   # idx -> decompSum
        top = sorted(core.items(), key=lambda kv: -kv[1])[:args.core]
        ordered = [(dsum, idx, gen.row(list(idx))[0]) for idx, dsum in top]
        sys.stderr.write("      (python) decomposables=%d  coeur garde=%d  (decompSum %d..%d)\n"
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
