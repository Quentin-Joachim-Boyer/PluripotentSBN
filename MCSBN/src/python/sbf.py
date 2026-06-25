"""
sbf.py — Enumération des fonctions seuil signées (SBF) et de leurs statistiques.

Une SBF de dimension k est une fonction f : {0,1}^k -> {0,1} de la forme
    f(x) = 1  ssi  somme_i w_i * x_i > 0,
avec des poids entiers w_i dans [-wb(k), wb(k)]. C'est exactement la fonction de
transition d'UN noeud d'un SBN : f_j ne depend que de la colonne j de la matrice
de poids. Comme les colonnes sont independantes, la dynamique d'un SBN de
dimension n est un n-uplet de SBF de dimension n, et N'IMPORTE QUEL n-uplet de
SBF est realisable. C'est le pivot de tout le generateur Monte-Carlo :
l'espace des dynamiques distinctes EST (SBF_n)^n.

On represente une SBF par sa table de verite encodee en entier (`tt`) : le bit s
de `tt` vaut f(s). C'est la meme convention que SBFStatTable.java cote pipeline,
donc les tables sont directement comparables.

Les statistiques par SBF (taille de l'ensemble des colonnes, robustesse,
evolvabilite) repliquent SBFStatTable.java afin que le CSV produit colle a la
pipeline.
"""

import os
import pickle
from itertools import product

# Cache partage avec le binaire C, a la racine du projet MCSBN (src/python -> ../..).
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "..", ".cache")


def wbound(n):
    """Borne des poids w_bound(d), meme convention que la pipeline ASP/Java.

    w_bound(1,1). w_bound(2,1). w_bound(3,2). w_bound(4,3). w_bound(5,5).
    w_bound(D,D) pour D > 5.
    """
    if n == 1:
        return 1
    if n == 2:
        return 1
    if n == 3:
        return 2
    if n == 4:
        return 3
    return n


def threshold_tt(col, k):
    """Table de verite (entier, bit s = f(s)) de la SBF de poids `col` en dim k."""
    tt = 0
    for s in range(1 << k):
        ssum = 0
        ss = s
        i = 0
        while ss:
            if ss & 1:
                ssum += col[i]
            ss >>= 1
            i += 1
        if ssum > 0:
            tt |= (1 << s)
    return tt


class SBFTable:
    """Table indexee par SBF (tt) pour une dimension n donnee.

    Attributs:
      n              : dimension
      wb             : borne des poids
      keys           : liste des tt des SBF distinctes (ordre stable)
      repr_col       : {tt: colonne de poids representative (tuple de n entiers)}
      column_set_size: {tt: nb de colonnes de poids realisant cette SBF}
      neutral_mean   : {tt: nb moyen de voisins neutres (cf. Wagner 2008)}
      neutral_var    : {tt: variance de ce nombre}
      evolvability   : {tt: nb de SBF distinctes atteintes par mutation d'un poids}
      neighbor_count : nb total de voisins d'une colonne = n*(domainSize-1)
    """

    __slots__ = ("n", "wb", "keys", "repr_col", "column_set_size",
                 "neutral_mean", "neutral_var", "evolvability", "neighbor_count")

    def __init__(self, n):
        self.n = n
        self.wb = wbound(n)

    def key_set(self):
        return set(self.keys)


def _compute_table(n):
    wb = wbound(n)
    domain = range(-wb, wb + 1)
    domain_size = 2 * wb + 1

    neutral_counts = {}      # tt -> list des comptes de voisins neutres
    diffs = {}               # tt -> set des SBF voisines distinctes
    repr_col = {}            # tt -> premiere colonne rencontree

    col = [0] * n
    for col_tuple in product(domain, repeat=n):
        for i in range(n):
            col[i] = col_tuple[i]
        f = threshold_tt(col, n)
        if f not in repr_col:
            repr_col[f] = col_tuple
            diffs[f] = set()
            neutral_counts[f] = []
        elif col_tuple < repr_col[f]:
            # representant canonique : colonne lexicographiquement la plus petite
            repr_col[f] = col_tuple
        dset = diffs[f]

        neutral = 0
        for i in range(n):
            old = col[i]
            for cand in domain:
                if cand == old:
                    continue
                col[i] = cand
                f2 = threshold_tt(col, n)
                if f2 == f:
                    neutral += 1
                else:
                    dset.add(f2)
            col[i] = old
        neutral_counts[f].append(neutral)

    table = SBFTable(n)
    table.keys = list(repr_col.keys())
    table.repr_col = repr_col
    table.column_set_size = {}
    table.neutral_mean = {}
    table.neutral_var = {}
    table.evolvability = {}
    table.neighbor_count = n * (domain_size - 1)

    for f, counts in neutral_counts.items():
        m = sum(counts) / len(counts)
        var = sum((c - m) ** 2 for c in counts) / len(counts)
        table.column_set_size[f] = len(counts)
        table.neutral_mean[f] = m
        table.neutral_var[f] = var
        table.evolvability[f] = len(diffs[f])

    return table


_TABLE_CACHE = {}


def _table_to_dict(t):
    return {
        "n": t.n, "wb": t.wb, "keys": t.keys, "repr_col": t.repr_col,
        "column_set_size": t.column_set_size, "neutral_mean": t.neutral_mean,
        "neutral_var": t.neutral_var, "evolvability": t.evolvability,
        "neighbor_count": t.neighbor_count,
    }


def _table_from_dict(d):
    t = SBFTable(d["n"])
    t.wb = d["wb"]
    t.keys = d["keys"]
    t.repr_col = d["repr_col"]
    t.column_set_size = d["column_set_size"]
    t.neutral_mean = d["neutral_mean"]
    t.neutral_var = d["neutral_var"]
    t.evolvability = d["evolvability"]
    t.neighbor_count = d["neighbor_count"]
    return t


def get_table(n):
    """Table SBF complete (avec stats) pour la dimension n, mise en cache disque.

    On serialise un dict de donnees brutes (pas l'instance de classe) pour que le
    cache reste lisible que sbf soit importe comme module ou lance comme script.
    """
    if n in _TABLE_CACHE:
        return _TABLE_CACHE[n]
    path = os.path.join(CACHE_DIR, "sbf_table_%dd.pkl" % n)
    if os.path.exists(path):
        with open(path, "rb") as fh:
            table = _table_from_dict(pickle.load(fh))
        _TABLE_CACHE[n] = table
        return table
    table = _compute_table(n)
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(path, "wb") as fh:
        pickle.dump(_table_to_dict(table), fh)
    _TABLE_CACHE[n] = table
    return table


_NEIGHBOR_CACHE = {}


def get_neighbor_map(n):
    """Carte des voisins SBF en dimension n : {tt: frozenset(tt voisins)}.

    Deux SBF f, g sont voisines s'il existe une colonne de poids realisant f et
    une colonne realisant g qui ne different que d'UN poids (mutation unique dans
    [-wb(n), wb(n)]). La relation est symetrique (la paire de colonnes temoin
    vaut dans les deux sens). C'est exactement le voisinage qui definit les
    aretes du metagraphe (cf. sbfNeighbors() de metagraphe.html) : deux
    dynamiques sont reliees ssi elles ne different que sur une colonne f_k, le
    changement allant vers un SBF voisin.

    Mise en cache disque (partagee avec les autres tables SBF de ce module).
    """
    if n in _NEIGHBOR_CACHE:
        return _NEIGHBOR_CACHE[n]
    path = os.path.join(CACHE_DIR, "sbf_neighbors_%dd.pkl" % n)
    if os.path.exists(path):
        with open(path, "rb") as fh:
            nbr = pickle.load(fh)
        _NEIGHBOR_CACHE[n] = nbr
        return nbr

    wb = wbound(n)
    domain = range(-wb, wb + 1)
    diffs = {}
    col = [0] * n
    for col_tuple in product(domain, repeat=n):
        for i in range(n):
            col[i] = col_tuple[i]
        f = threshold_tt(col, n)
        dset = diffs.get(f)
        if dset is None:
            dset = diffs[f] = set()
        for i in range(n):
            old = col[i]
            for cand in domain:
                if cand == old:
                    continue
                col[i] = cand
                f2 = threshold_tt(col, n)
                if f2 != f:
                    dset.add(f2)
            col[i] = old

    nbr = {f: frozenset(s) for f, s in diffs.items()}
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(path, "wb") as fh:
        pickle.dump(nbr, fh)
    _NEIGHBOR_CACHE[n] = nbr
    return nbr


_KEYSET_CACHE = {}


def get_key_set(k):
    """Ensemble des tt des SBF de dimension k avec le bound naturel wb(k)."""
    if k == 0:
        return {0}
    if k in _KEYSET_CACHE:
        return _KEYSET_CACHE[k]
    s = get_table(k).key_set()
    _KEYSET_CACHE[k] = s
    return s


_BOUNDED_KEYSET_CACHE = {}


def get_key_set_bounded(k, bound):
    """Fonctions seuil de dimension k realisables avec des poids dans [-bound, bound].

    La decomposition "sous controle" realise TOUS les sous-reseaux, a toute
    profondeur, avec le bound de la dimension du sommet (cf. wb unique cote ASP).
    Le test de realisabilite d'une face de dimension k utilise donc ce bound-la,
    et non wb(k).
    """
    if k == 0:
        return {0}
    cache_key = (k, bound)
    if cache_key in _BOUNDED_KEYSET_CACHE:
        return _BOUNDED_KEYSET_CACHE[cache_key]
    s = set()
    for col in product(range(-bound, bound + 1), repeat=k):
        s.add(threshold_tt(col, k))
    _BOUNDED_KEYSET_CACHE[cache_key] = s
    return s


if __name__ == "__main__":
    import sys
    for n in [int(x) for x in (sys.argv[1:] or [1, 2, 3, 4])]:
        t = get_table(n)
        total_cols = (2 * wbound(n) + 1) ** n
        print("n=%d  wb=%d  #colonnes=%d  #SBF distinctes=%d  #dynamiques=%d^%d"
              % (n, wbound(n), total_cols, len(t.keys), len(t.keys), n))
