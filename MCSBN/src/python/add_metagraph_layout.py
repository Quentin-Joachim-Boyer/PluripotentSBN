#!/usr/bin/env python3
"""
add_metagraph_layout.py — ajoute les colonnes metagraph_x, metagraph_y a un CSV
genere (par mcsbn ou la pipeline), en placant chaque dynamique dans le
metagraphe via DRGraph.

Le metagraphe (cf. metagraphe.html) :
  - un noeud par dynamique distincte, identifiee par sa signature f_1..f_n
    (chaque f_j est la table de verite, un bitstring de longueur 2^n) ;
  - une arete entre deux dynamiques qui ne different que sur UNE colonne f_k,
    le changement allant vers un SBF voisin (mutation d'un seul poids ;
    voisinage fourni par sbf.get_neighbor_map, symetrique).

On exporte ce graphe au format DRGraph ("N E" puis lignes "i j poids"), on
appelle le binaire Vis (cf. tools/DRGraph), on relit les coordonnees 2D et on
les recopie sur chaque ligne du CSV (les lignes partageant une meme signature
recoivent la meme position).

Deux passes sur le fichier d'entree pour ne pas tout charger en memoire :
  1) ne lit que les colonnes f_* -> signatures, deduplication, aretes, layout ;
  2) reecrit le CSV en streaming en ajoutant metagraph_x, metagraph_y.

Usage :
  python add_metagraph_layout.py in.csv[.gz] [-o out.csv[.gz]] [options DRGraph]
"""

import argparse
import csv
import gzip
import math
import os
import re
import subprocess
import sys
import tempfile

import sbf

# csv peut rencontrer des champs longs (bitstrings 2^n, n grand).
csv.field_size_limit(1 << 24)

F_COL_RE = re.compile(r"^\"?f_(\d+)\"?$")


def open_text(path, mode):
    """Ouvre un .csv ou .csv.gz en texte selon l'extension."""
    if path == "-":
        return sys.stdin if "r" in mode else sys.stdout
    if path.endswith(".gz"):
        return gzip.open(path, mode + "t", newline="")
    return open(path, mode, newline="")


def find_f_columns(header):
    """Indices des colonnes f_k dans l'ordre k=1..n. Vide si absentes."""
    idx = {}
    for col, name in enumerate(header):
        m = F_COL_RE.match(name)
        if m:
            idx[int(m.group(1))] = col
    if not idx:
        return []
    ks = sorted(idx)
    if ks != list(range(1, len(ks) + 1)):
        raise SystemExit("Colonnes f_* non contigues (%s)." % ks)
    return [idx[k] for k in ks]


def bitstring_to_tt(bs):
    """Bitstring (char s = f(s)) -> table de verite entiere (bit s)."""
    # le char d'indice s porte le bit s ; on inverse pour lire en base 2.
    return int(bs[::-1], 2) if bs else 0


def build_metagraph(in_path):
    """Pass 1 : signatures, deduplication et aretes du metagraphe.

    Retourne (n, sig_to_node, n_nodes, edges) ou edges est un set de (i, j), i<j.
    sig_to_node mappe une signature (tuple de tt) vers l'indice de noeud.
    """
    with open_text(in_path, "r") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            raise SystemExit("CSV vide.")
        fcols = find_f_columns(header)
        if not fcols:
            raise SystemExit(
                "CSV sans colonnes f_* : metagraphe impossible "
                "(genere sans --no-weights ?).")
        n = len(fcols)
        expect_len = 1 << n

        sig_to_node = {}
        for row in reader:
            if not row:
                continue
            try:
                sig = tuple(bitstring_to_tt(row[c]) for c in fcols)
            except IndexError:
                raise SystemExit("Ligne trop courte pour les colonnes f_*.")
            # validation legere de longueur sur la premiere colonne
            if len(row[fcols[0]]) != expect_len:
                raise SystemExit(
                    "Longueur de f_1 = %d, attendu 2^%d = %d."
                    % (len(row[fcols[0]]), n, expect_len))
            if sig not in sig_to_node:
                sig_to_node[sig] = len(sig_to_node)

    n_nodes = len(sig_to_node)
    nbr = sbf.get_neighbor_map(n)

    edges = set()
    for sig, i in sig_to_node.items():
        for k in range(n):
            base = sig[k]
            for nb in nbr.get(base, ()):
                cand = sig[:k] + (nb,) + sig[k + 1:]
                j = sig_to_node.get(cand)
                if j is not None and j > i:
                    edges.add((i, j))
    return n, sig_to_node, n_nodes, edges


def fallback_layout(n_nodes):
    """Positions de secours (cercle) quand DRGraph n'est pas applicable."""
    if n_nodes <= 1:
        return [(0.0, 0.0)] * n_nodes
    return [(math.cos(2 * math.pi * i / n_nodes),
             math.sin(2 * math.pi * i / n_nodes)) for i in range(n_nodes)]


def run_drgraph(n_nodes, edges, vis_bin, params, env, verbose):
    """Ecrit le graphe, lance Vis, relit les coordonnees -> liste (x, y)."""
    with tempfile.TemporaryDirectory(prefix="mcsbn_meta_") as td:
        gpath = os.path.join(td, "graph.txt")
        opath = os.path.join(td, "layout.txt")
        with open(gpath, "w") as gf:
            gf.write("%d %d\n" % (n_nodes, len(edges)))
            for i, j in edges:
                gf.write("%d %d 1\n" % (i, j))

        cmd = [vis_bin, "-input", gpath, "-output", opath,
               "-neg", str(params["neg"]), "-samples", str(params["samples"]),
               "-gamma", str(params["gamma"]), "-mode", str(params["mode"]),
               "-A", str(params["A"]), "-B", str(params["B"])]
        if verbose:
            print("[drgraph] " + " ".join(cmd), file=sys.stderr)
        res = subprocess.run(cmd, env=env,
                             stdout=(None if verbose else subprocess.DEVNULL),
                             stderr=(None if verbose else subprocess.DEVNULL))
        if res.returncode != 0 or not os.path.exists(opath):
            raise SystemExit("DRGraph (Vis) a echoue (code %d)." % res.returncode)

        coords = [None] * n_nodes
        with open(opath) as of:
            head = of.readline().split()
            cnt = int(head[0])
            for idx in range(cnt):
                parts = of.readline().split()
                coords[idx] = (float(parts[0]), float(parts[1]))
    # noeuds isoles eventuellement absents : 0,0 par defaut
    return [c if c is not None else (0.0, 0.0) for c in coords]


def locate_vis(explicit):
    """Trouve le binaire Vis ; le construit via build.sh si absent."""
    if explicit:
        if not os.path.exists(explicit):
            raise SystemExit("Binaire Vis introuvable : %s" % explicit)
        return explicit
    env_bin = os.environ.get("MCSBN_VIS")
    if env_bin and os.path.exists(env_bin):
        return env_bin
    here = os.path.dirname(os.path.abspath(__file__))
    drg = os.path.normpath(os.path.join(here, "..", "..", "tools", "DRGraph"))
    vis = os.path.join(drg, "Vis")
    if os.path.exists(vis):
        return vis
    build = os.path.join(drg, "build.sh")
    if os.path.exists(build):
        print("[drgraph] Vis absent, compilation via build.sh ...", file=sys.stderr)
        if subprocess.run(["bash", build]).returncode == 0 and os.path.exists(vis):
            return vis
    raise SystemExit(
        "Binaire DRGraph 'Vis' introuvable. Compilez-le :\n"
        "  bash %s\n"
        "ou indiquez-le via --vis / $MCSBN_VIS." % build)


def make_env():
    """Env subprocess : ajoute le lib conda au LD_LIBRARY_PATH si detecte."""
    env = os.environ.copy()
    here = os.path.dirname(os.path.abspath(__file__))
    conda = os.path.normpath(os.path.join(here, "..", "..", "..", ".conda"))
    lib = os.path.join(conda, "lib")
    if os.path.isdir(lib):
        env["LD_LIBRARY_PATH"] = lib + os.pathsep + env.get("LD_LIBRARY_PATH", "")
    return env


def rewrite_csv(in_path, out_path, fcols, sig_to_node, coords, fmt):
    """Pass 2 : recopie le CSV en ajoutant metagraph_x, metagraph_y."""
    with open_text(in_path, "r") as fin, open_text(out_path, "w") as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout)
        header = next(reader)
        writer.writerow(header + ["metagraph_x", "metagraph_y"])
        for row in reader:
            if not row:
                continue
            sig = tuple(bitstring_to_tt(row[c]) for c in fcols)
            x, y = coords[sig_to_node[sig]]
            writer.writerow(row + [fmt % x, fmt % y])


def derive_output(in_path):
    if in_path.endswith(".csv.gz"):
        return in_path[:-7] + "_metagraph.csv.gz"
    if in_path.endswith(".gz"):
        return in_path[:-3] + "_metagraph.gz"
    base, ext = os.path.splitext(in_path)
    return base + "_metagraph" + (ext or ".csv")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="CSV ou CSV.gz genere (avec colonnes f_*)")
    ap.add_argument("-o", "--output", help="sortie (def: <input>_metagraph...)")
    ap.add_argument("--vis", help="chemin du binaire DRGraph 'Vis'")
    ap.add_argument("--neg", type=int, default=5, help="negative samples (def 5)")
    ap.add_argument("--samples", type=int, default=400,
                    help="iterations DRGraph (def 400)")
    ap.add_argument("--gamma", type=float, default=0.1, help="poids repulsion (def .1)")
    ap.add_argument("--mode", type=int, default=1, help="mode DRGraph (def 1)")
    ap.add_argument("--A", type=float, default=2.0, help="parametre a (def 2)")
    ap.add_argument("--B", type=float, default=1.0,
                    help="parametre b, forme de la distribution (def 1)")
    ap.add_argument("--precision", type=int, default=6,
                    help="chiffres significatifs des coords (def 6)")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="affiche la sortie de DRGraph")
    args = ap.parse_args()

    out_path = args.output or derive_output(args.input)
    fmt = "%%.%dg" % args.precision

    print("[1/3] construction du metagraphe ...", file=sys.stderr)
    n, sig_to_node, n_nodes, edges = build_metagraph(args.input)
    fcols = None  # recalcule l'ordre des colonnes f pour la pass 2
    with open_text(args.input, "r") as fh:
        fcols = find_f_columns(next(csv.reader(fh)))
    print("      n=%d  noeuds(dynamiques distinctes)=%d  aretes=%d"
          % (n, n_nodes, len(edges)), file=sys.stderr)

    print("[2/3] layout ...", file=sys.stderr)
    if n_nodes <= 2 or len(edges) == 0:
        print("      graphe trivial/sans arete -> layout de secours (cercle).",
              file=sys.stderr)
        coords = fallback_layout(n_nodes)
    else:
        vis_bin = locate_vis(args.vis)
        params = {"neg": args.neg, "samples": args.samples, "gamma": args.gamma,
                  "mode": args.mode, "A": args.A, "B": args.B}
        coords = run_drgraph(n_nodes, edges, vis_bin, params,
                             make_env(), args.verbose)

    print("[3/3] reecriture du CSV -> %s" % out_path, file=sys.stderr)
    rewrite_csv(args.input, out_path, fcols, sig_to_node, coords, fmt)
    print("OK", file=sys.stderr)


if __name__ == "__main__":
    main()
