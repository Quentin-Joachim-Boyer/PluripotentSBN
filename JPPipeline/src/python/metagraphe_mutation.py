"""
Métagraphe mutationnel des SBNPs.

Deux SBNPs sont voisins si l'un est accessible depuis l'autre par une seule
mutation élémentaire (changer un poids w_i,j vers une autre valeur dans
[-wBound(n), wBound(n)]) ET que le mutant est présent dans le dataset.

La table de voisinage SBF est précalculée en Python (O(wBound^n × n)) depuis
la définition threshold(v)[s] = 1 ssi Σ_{i actif dans s} v[i] > 0.
Aucun champ supplémentaire dans le CSV.

Usage :
  python metagraphe_mutation.py sbnps.csv [--out out.png] [--no-plot]
"""

import argparse
import itertools
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl


# ── Table de voisinage SBF ────────────────────────────────────────────────────

def w_bound(n):
    """Borne des poids (même convention que SBFStatTable.java)."""
    if n <= 2: return 1
    if n == 3: return 2
    if n == 4: return 3
    return n


def threshold(v):
    """SBF d'un vecteur de poids v : tuple de bits, index = état s."""
    n = len(v)
    bits = []
    for s in range(1 << n):
        total = sum(v[i] for i in range(n) if s & (1 << i))
        bits.append(1 if total > 0 else 0)
    return tuple(bits)


def sbf_neighbors(n):
    """
    Pour chaque SBF (tuple de bits) atteignable par threshold,
    retourne l'ensemble des SBF distincts atteignables par une mutation
    d'un seul poids (vers toute autre valeur dans [-wb, wb]).
    """
    wb = w_bound(n)
    domain = range(-wb, wb + 1)
    neighbors = {}  # sbf_tuple → set of neighbor sbf_tuples

    for v in itertools.product(domain, repeat=n):
        v = list(v)
        f = threshold(v)
        if f not in neighbors:
            neighbors[f] = set()
        for i in range(n):
            old = v[i]
            for c in domain:
                if c == old:
                    continue
                v[i] = c
                f2 = threshold(v)
                if f2 != f:
                    neighbors[f].add(f2)
            v[i] = old

    return neighbors


def sbf_str_to_tuple(s):
    return tuple(int(c) for c in s)


def sbf_tuple_to_str(t):
    return "".join(str(b) for b in t)


# ── Construction du graphe de mutation ───────────────────────────────────────

def build_mutation_graph(df):
    f_cols = [c for c in df.columns if c.startswith("f_")]
    n = len(f_cols)
    sbf_len = 1 << n

    def sbf_str(val):
        """Entier pandas → bitstring décimal zero-paddé ('0010', pas binaire)."""
        return str(int(val)).zfill(sbf_len)

    print(f"Précalcul de la table de voisinage SBF pour n={n}...", flush=True)
    neighbors = sbf_neighbors(n)
    print(f"  {len(neighbors)} SBF distincts, table calculée.", flush=True)

    # Lookup : tuple de SBF strings → index de ligne
    lookup = {}
    sbf_vecs = []
    for i, row in df.iterrows():
        vec = tuple(sbf_str(row[c]) for c in f_cols)
        sbf_vecs.append(vec)
        lookup[vec] = i

    # Ordre décroissant = (v_n, v_{n-1}, ..., v_0) = ordre naturel du CSV
    decomp_cols = sorted((c for c in df.columns if c.startswith("v_")), reverse=True)
    G = nx.Graph()
    for i in range(len(df)):
        G.add_node(i, decomp=tuple(df[decomp_cols].iloc[i]))

    for i in range(len(df)):
        vec = sbf_vecs[i]
        for k in range(n):
            f_k = sbf_str_to_tuple(vec[k])
            for nbr_tuple in neighbors.get(f_k, ()):
                nbr_str = sbf_tuple_to_str(nbr_tuple)
                query = vec[:k] + (nbr_str,) + vec[k+1:]
                j = lookup.get(query)
                if j is not None and j > i:
                    G.add_edge(i, j, col=k)

    print(f"Graphe : {G.number_of_nodes()} nœuds, {G.number_of_edges()} arêtes.")
    return G


# ── Visualisation ─────────────────────────────────────────────────────────────

def plot_graph(G, title, out_path):
    decomps = [G.nodes[i]["decomp"] for i in G.nodes()]
    # Somme croissante = peu décomposé (petit total) en premier, puis lex
    unique_decomps = sorted(set(decomps), key=lambda d: (sum(d), d))
    cmap = mpl.colormaps["tab20"].resampled(max(len(unique_decomps), 1))
    color_map = {d: cmap(k) for k, d in enumerate(unique_decomps)}
    node_colors = [color_map[G.nodes[i]["decomp"]] for i in G.nodes()]

    print("Calcul du layout...", flush=True)
    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog="sfdp")
    except Exception:
        print("  pygraphviz absent, fallback spring_layout.", flush=True)
        pos = nx.spring_layout(G, seed=42, k=1.5)

    fig, ax = plt.subplots(figsize=(14, 10))
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.4, width=0.8, edge_color="steelblue")
    # Dessiner du plus commun (fond) au plus rare (dessus) pour que les
    # groupes minoritaires restent visibles par-dessus la masse dominante.
    for d in unique_decomps:
        group = [i for i in G.nodes() if G.nodes[i]["decomp"] == d]
        nx.draw_networkx_nodes(G, pos, nodelist=group,
                               node_color=[color_map[d]] * len(group),
                               node_size=40, ax=ax, alpha=0.9)

    handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=color_map[d],
                   markersize=8, label=str(d))
        for d in unique_decomps
    ]
    ax.legend(handles=handles, title="Vecteur de décomposition",
              loc="upper left", fontsize=6, ncol=2)
    ax.set_title(title)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f"Figure sauvegardée : {out_path}", flush=True)
    plt.close(fig)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sbnps_csv", help="CSV de la pipeline (avec colonnes f_*)")
    parser.add_argument("--out", default="metagraphe_mutation.png")
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()

    print(f"Lecture de {args.sbnps_csv} ...", flush=True)
    df = pd.read_csv(args.sbnps_csv)
    print(f"{len(df)} SBNPs chargés.", flush=True)

    G = build_mutation_graph(df)

    isolated = sum(1 for nd in G.nodes() if G.degree(nd) == 0)
    components = nx.number_connected_components(G)
    print(f"Nœuds isolés : {isolated}  |  Composantes connexes : {components}")

    if not args.no_plot:
        title = (f"Métagraphe mutationnel SBNP — "
                 f"{G.number_of_nodes()} nœuds, {G.number_of_edges()} arêtes")
        plot_graph(G, title, args.out)


if __name__ == "__main__":
    main()
