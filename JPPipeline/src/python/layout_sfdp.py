#!/usr/bin/env python3
"""
Génère les colonnes x/y pour un CSV *_output.csv en utilisant graph-tool SFDP.
Usage : python layout_sfdp.py <input.csv> [output.csv]
Si output est omis, le fichier est modifié en place.

Installation graph-tool (conda recommandé) :
    conda install -c conda-forge graph-tool
"""

import sys
import csv
import re
import itertools
import time

# ─── Logique SBF (portée depuis metagraphe.html) ─────────────────────────────

def w_bound(n):
    if n <= 2: return 1
    if n == 3: return 2
    if n == 4: return 3
    return n

def threshold(v):
    n = len(v)
    bits = []
    for s in range(1 << n):
        t = sum(v[i] for i in range(n) if s & (1 << i))
        bits.append('1' if t > 0 else '0')
    return ''.join(bits)

def sbf_neighbors(n):
    """Précalcule, pour chaque valeur de threshold possible, ses voisins SBF."""
    wb = w_bound(n)
    rng = range(-wb, wb + 1)
    neighbor_map = {}  # threshold_str → set of reachable threshold_str
    v = [0] * n
    for combo in itertools.product(rng, repeat=n):
        v = list(combo)
        f = threshold(v)
        if f not in neighbor_map:
            neighbor_map[f] = set()
        s = neighbor_map[f]
        for i in range(n):
            old = v[i]
            for c in rng:
                if c == old:
                    continue
                v[i] = c
                f2 = threshold(v)
                if f2 != f:
                    s.add(f2)
            v[i] = old
    return neighbor_map

# ─── Lecture CSV ──────────────────────────────────────────────────────────────

def load_csv(path):
    import gzip
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rt', newline='') as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = reader.fieldnames
    return rows, fieldnames

# ─── Construction du graphe (même logique que buildGraph dans metagraphe.html) ─

def build_graph_data(rows, fieldnames):
    fcols = sorted([h for h in fieldnames if re.match(r'^f_\d+$', h)],
                   key=lambda h: int(h[2:]))
    vcols = sorted([h for h in fieldnames if re.match(r'^v_\d+$', h)],
                   key=lambda h: -int(h[2:]))  # décroissant
    n = len(fcols)
    if n == 0:
        raise ValueError("Aucune colonne f_* trouvée dans le CSV")

    print(f"  {n} gènes, {len(rows)} lignes brutes", flush=True)

    # Déduplication par signature f_* (même logique que metagraphe.html)
    fkey_to_idx = {}
    unique_rows = []
    decomp_sum = []

    for row in rows:
        fkey = '|'.join(row[c] for c in fcols)
        if fkey not in fkey_to_idx:
            fkey_to_idx[fkey] = len(unique_rows)
            unique_rows.append(row)
            s = sum(int(row[c]) for c in vcols) if vcols else 0
            decomp_sum.append(s)
        elif vcols:
            idx = fkey_to_idx[fkey]
            s = sum(int(row[c]) for c in vcols)
            if s > decomp_sum[idx]:
                unique_rows[idx] = row
                decomp_sum[idx] = s

    N = len(unique_rows)
    print(f"  {N} nœuds uniques après déduplication", flush=True)

    # Vecteurs f_* pour chaque nœud
    vecs = [[row[c] for c in fcols] for row in unique_rows]

    # Précalcul des voisins SBF
    print("  Précalcul des voisins SBF…", flush=True)
    neighbors = sbf_neighbors(n)

    # Construction de l'adjacence
    print("  Construction des arêtes…", flush=True)
    edges = []
    vec = [None] * n
    for i in range(N):
        vec[:] = vecs[i]
        for k in range(n):
            nbrs = neighbors.get(vec[k])
            if not nbrs:
                continue
            old = vec[k]
            for nb in nbrs:
                vec[k] = nb
                j = fkey_to_idx.get('|'.join(vec))
                if j is not None and j > i:
                    edges.append((i, j))
            vec[k] = old

    print(f"  {len(edges)} arêtes", flush=True)
    return N, edges, unique_rows, fkey_to_idx, fcols

# ─── Layout SFDP ─────────────────────────────────────────────────────────────

def compute_layout(N, edges):
    t_import = time.time()
    import graph_tool.all as gt
    dt_import = time.time() - t_import
    print(f"  import graph-tool     : {dt_import:.1f}s", flush=True)

    t_build = time.time()
    g = gt.Graph(directed=False)
    g.add_vertex(N)
    g.add_edge_list(edges)
    dt_build = time.time() - t_build
    print(f"  construction graphe   : {dt_build:.1f}s  ({N} nœuds, {len(edges)} arêtes)", flush=True)

    t_layout = time.time()
    pos = gt.sfdp_layout(g, multilevel=True)
    dt_layout = time.time() - t_layout
    print(f"  SFDP layout           : {dt_layout:.1f}s", flush=True)
    print(f"  ─────────────────────────────────────────", flush=True)
    print(f"  total                 : {dt_import+dt_build+dt_layout:.1f}s  (overhead {dt_import:.1f}s + calcul {dt_build+dt_layout:.1f}s)", flush=True)

    xs = pos.get_2d_array([0])[0]
    ys = pos.get_2d_array([1])[0]
    return xs, ys

# ─── Écriture CSV ─────────────────────────────────────────────────────────────

def write_csv(path, rows, fieldnames, fkey_to_idx, fcols, xs, ys):
    import gzip
    out_fields = list(fieldnames)
    if 'x' not in out_fields:
        out_fields.append('x')
    if 'y' not in out_fields:
        out_fields.append('y')

    pos_by_idx = {idx: (xs[idx], ys[idx]) for idx in range(len(xs))}

    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'wt', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=out_fields)
        writer.writeheader()
        for row in rows:
            fkey = '|'.join(row[c] for c in fcols)
            idx = fkey_to_idx.get(fkey)
            out = dict(row)
            if idx is not None:
                x, y = pos_by_idx[idx]
                out['x'] = f'{x:.6f}'
                out['y'] = f'{y:.6f}'
            else:
                out['x'] = ''
                out['y'] = ''
            writer.writerow(out)

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else input_path

    print(f"Lecture de {input_path}…", flush=True)
    rows, fieldnames = load_csv(input_path)

    print("Construction du graphe…", flush=True)
    N, edges, unique_rows, fkey_to_idx, fcols = build_graph_data(rows, fieldnames)

    print("Layout SFDP…", flush=True)
    xs, ys = compute_layout(N, edges)

    print(f"Écriture de {output_path}…", flush=True)
    write_csv(output_path, rows, fieldnames, fkey_to_idx, fcols, xs, ys)

    print("Terminé.", flush=True)

if __name__ == '__main__':
    main()