"""
Métagraphe des SBNPs basé sur la distance dDA (Ai-Ling Nguyen Bonnet, 2023).

Workflow en deux étapes :

  1. Générer le CSV de distances avec PairwiseDA.java (parallèle, rapide) :
       java -cp bin:lib/jpp.jar PSBN.PairwiseDA sbnps.csv distances.csv [threshold]

  2. Visualiser le métagraphe :
       python metagraphe_dDA.py sbnps.csv distances.csv [--out out.png]

Le CSV de distances contient : id_1,id_2,dDA (paires avec dDA <= threshold).
Le CSV des SBNPs doit avoir une colonne 'dynamics' (générée par la pipeline)
et des colonnes 'v_*' pour le vecteur de décomposition.
"""

import argparse
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib


# ── Construction du métagraphe depuis le CSV de distances ────────────────────

def build_metagraph(sbnps_df, dist_df):
    """
    Construit le graphe NetworkX depuis le CSV de distances précalculé.
    Attribut de noeud 'decomp' : tuple du vecteur de décomposition (v_* cols).
    Attribut d'arête 'dDA' : valeur de la distance.
    """
    decomp_cols = sorted((c for c in sbnps_df.columns if c.startswith("v_")), reverse=True)

    G = nx.Graph()
    for i in range(len(sbnps_df)):
        G.add_node(i, decomp=tuple(sbnps_df[decomp_cols].iloc[i]))

    for _, row in dist_df.iterrows():
        G.add_edge(int(row["id_1"]), int(row["id_2"]), dDA=int(row["dDA"]))

    return G


# ── Visualisation ────────────────────────────────────────────────────────────

def plot_metagraph(G, title, out_path):
    decomps = [G.nodes[i]["decomp"] for i in G.nodes()]
    unique_decomps = sorted(set(decomps), key=lambda d: d[::-1])
    cmap = matplotlib.colormaps.get_cmap("tab20").resampled(max(len(unique_decomps), 1))
    color_map = {d: cmap(k) for k, d in enumerate(unique_decomps)}
    node_colors = [color_map[G.nodes[i]["decomp"]] for i in G.nodes()]

    print("Calcul du layout force-directed (sfdp)...", flush=True)
    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog="sfdp")
    except Exception:
        # fallback si pygraphviz absent : spring avec peu d'itérations
        print("  pygraphviz absent, fallback spring_layout (iterations=20)", flush=True)
        pos = nx.spring_layout(G, seed=42, iterations=20)

    fig, ax = plt.subplots(figsize=(14, 10))
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.15, width=0.5)
    for d in unique_decomps:
        group = [i for i in G.nodes() if G.nodes[i]["decomp"] == d]
        nx.draw_networkx_nodes(G, pos, nodelist=group,
                               node_color=[color_map[d]] * len(group),
                               node_size=15, ax=ax, alpha=0.8)

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
    parser.add_argument("sbnps_csv", help="CSV de la pipeline (avec colonne dynamics)")
    parser.add_argument("distances_csv", help="CSV de distances généré par PairwiseDA.java")
    parser.add_argument("--out", default="metagraphe_dDA.png",
                        help="Fichier de sortie (défaut: metagraphe_dDA.png)")
    parser.add_argument("--max_dda", type=int, default=None,
                        help="Filtre les arêtes à dDA <= MAX_DDA (utile si le CSV contient un threshold plus large)")
    args = parser.parse_args()

    print(f"Lecture des SBNPs : {args.sbnps_csv}", flush=True)
    sbnps_df = pd.read_csv(args.sbnps_csv)
    print(f"{len(sbnps_df)} SBNPs chargés.", flush=True)

    print(f"Lecture des distances : {args.distances_csv}", flush=True)
    dist_df = pd.read_csv(args.distances_csv)
    if args.max_dda is not None:
        dist_df = dist_df[dist_df["dDA"] <= args.max_dda]
    print(f"{len(dist_df)} paires chargées (dDA <= {args.max_dda or 'all'}).", flush=True)

    G = build_metagraph(sbnps_df, dist_df)
    print(f"Graphe : {G.number_of_nodes()} noeuds, {G.number_of_edges()} arêtes.", flush=True)

    title = f"Métagraphe SBNP — {len(dist_df):,} arêtes dDA"
    plot_metagraph(G, title, args.out)


if __name__ == "__main__":
    main()
