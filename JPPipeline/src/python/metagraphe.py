import DistanceParameters
from analysis_distances import *
import networkx as nx
import matplotlib.pyplot as plt
from mg_layout import layout2

# TO DO: shortest path, cout d'évolution
# Evolutivité avec metagraphe
# Viabilité: modèle simple binaire aléatoire
# pour ce qui est de viabilité avec contraintes, il faudrait identifier les sbns qui ont tel caractéristiques --> JPP
# visualisation en fixant les points. idée: placer les sommets dans l'espace (avec l'odre donné par le dendogramme)
# puis tracer les arcs en espérant que ce ne soit pas trop brouillon. l'arrangement du dendogramme devrait etre bien
'''Paramètres'''
dref = 'HSTR'  # distance de référence
dcomp = 'HDYN'  # distance à comparer
dim = 2
display = False

csvpath = f"~/Datas/Documents/Prog/TBAN/Data/Distances/distances_dim{dim}.csv"
#csvpath = f"pipelineWorkingFolder\\distances_data\\distances_dim{dim}.csv"
# sbnpath = "pipelineWorkingFolder\\distances_data\\SBN_full_list_dim2.csv"

dist_df = pd.read_csv(csvpath)
print('CSV lu, dataframe créée\n')

dref_tab = matrix_distance(dist_df, dref)
dcomp_tab = matrix_distance(dist_df, dcomp)
dcomp_max = dcomp_tab.max()
nbsbn = dist_df['id_2'].max()


def build_graph(dref_tab, dcomp_tab, epsilon=1, delta=-1):
    G = nx.Graph()
    nbsbn = dref_tab.shape[0]
    G.add_nodes_from([i for i in range(0, nbsbn)])
    # les noeuds sont les sbn
    # ils sont connectés s'ils sont epsilon proche pour dref
    # le poids des arcs est la deuxieme distance dcomp
    # epsilon: seuil sur dref (HSTR en général)
    # delta: seuil sur dcomp (HDYN en général)
    for i in range(0, nbsbn):
        for j in range(i+1, nbsbn):
            if (dref_tab[i][j] <= epsilon) & ((delta == -1) | ((delta > -1) & (dcomp_tab[i][j] <= delta))):
                # delta == -1 pas de condition sur dcomp; delta>0, on prend les voisins qui sont aussi proches selon dcomp
                if dcomp_tab[i][j] == 0:
                    poids = 3
                    couleur = 'r'
                else:
                    poids = 1/dcomp_tab[i][j]
                    couleur = 'b'
                G.add_edge(i, j, color=couleur, width=poids, weight=poids)
    return G


G = build_graph(dref_tab, dcomp_tab)  # graph complet

""" f, (ax1, ax2) = plt.subplots(1, 2)
nx.draw(G, pos=layout2, ax=ax1, with_labels=True)
G2 = build_graph(dref_tab, dcomp_tab, delta=0)
nx.draw(G2, pos=layout2, ax=ax2, with_labels=True)
plt.show() """


def compare_metagraphe_plot(G1, G2, pos=layout2):
    '''dispose les noeuds selon un layout donné
    sont colorés en rouge les arcs présents dans G1 (complet) mais pas dans G2 (restreint)
    quand G2 rajoute une condition sur la dynamique par ex'''

    # arcs commun
    colors = []
    for u, v in G1.edges():
        if not (G2.has_edge(u, v)):
            colors += 'r'
        else:
            colors += 'k'

    f, axs = plt.subplots(1, 2, figsize=(
        12, 7))
    # G1
    nx.draw(G, pos, node_color='skyblue', edge_color=colors,
            ax=axs[0], node_size=50, with_labels=True)
    # nx.draw_networkx_edges(G, pos, edge_color=colors, ax=axs[0])
    nx.draw(G2, pos=pos, ax=axs[1],
            node_color='skyblue', node_size=50, with_labels=True)
    return f, axs


seuils = [(1, 0), (2, 0), (3, 0), (1, 1), (1, 2),
          (1, 3), (1, 1), (2, 2), (3, 3)]
labels = ['Faible', 'Moyen', 'Elevé', 'Faible', 'Moyen',
          'Elevé', 'Faible-Faible', 'Moyen-Moyen', 'Elevé- Elevé']

if display:  # metagraphes en faisant varier epsilon et delta
    f, axs = plt.subplots(3, 3, figsize=(
        12, 7))
    for i in range(9):
        (epsilon, delta) = seuils[i]
        label = labels[i]
        G = build_graph(dref_tab, dcomp_tab, epsilon, delta)
        title = f'Metagraphe_dim{dim}_eps={epsilon}_delta={delta}.html'
        html_path = 'C:\\Users\\ailin\\Documents\\Stage_IBISC\\Hopfield\\'+title
        title_image = f'Metagraphe_dim{dim}_eps={epsilon}_delta={delta}.png'
        img_path = 'C:\\Users\\ailin\\Documents\\Stage_IBISC\\Hopfield\\src\\Python\\Metagraphes' + title_image
        # Affichage avec nx
        edges, weights = zip(*nx.get_edge_attributes(G, 'weight').items())
        nx.draw_networkx_nodes(G, layout2, node_color='skyblue',
                               node_size=3, ax=axs[i % 3, i // 3])
        nx.draw_networkx_edges(G, layout2, edge_color=weights,
                               width=weights, ax=axs[i % 3, i // 3],)
        axs[i//3, i %
            3].set_title(f'eps={epsilon}_delta={delta} {label}')

        # Pyvis
        # nt = Network("1000px", "1000px")  # dim de l'image HTML hauteur, largeur
        # nt.from_nx(G)
        # nt.show(title)
        # nt.save_graph(title)
        # imgkit.from_file(html_path, img_path)

    plt.show()
# plt.savefig(f'Metagraphes_dim{dim}', format="PNG")
