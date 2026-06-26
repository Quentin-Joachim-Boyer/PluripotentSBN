#!/usr/bin/env python3
"""
core_tree_enum.py — Phase 1 COMPLETE : enumere les dynamiques les plus
decomposees (coeur pluripotent) via une construction recursive de l'ARBRE DE
CONTROLE, ce qui couvre aussi les classes profondes "en epine" (asymetriques)
que le forcage de projections globales (core_then_walk.py) manquait.

Idee. Au niveau dynamique, tout n-uplet de SBF est une dynamique valide (les
colonnes sont independantes : aucun couplage). On peut donc enumerer un arbre de
controle en forcant chaque noeud de controle a etre invariant SUR SA FACE :
  - controle au sommet -> f_c = proj_c global (cas equilibre) ;
  - controle "en epine" -> f_c invariant seulement sur une sous-face, libre
    ailleurs (sous-ensemble de SBF precalcule).
Les classes profondes ont beaucoup de controles et peu de noeuds libres, donc
leur enumeration est petite (~ M^{#libres}). On filtre chaque candidat par le
vecteur EXACT (Generator.row -> Decomposer) ; correction garantie, completude
assuree par l'enumeration de tous les arbres a >= min_leaves feuilles.
"""

from itertools import product


def _states_in_face(n, fixed_nodes, fixed_vals):
    free = [i for i in range(n) if not (fixed_nodes >> i) & 1]
    out = []
    for c in range(1 << len(free)):
        s = fixed_vals
        for t, fn in enumerate(free):
            if (c >> t) & 1:
                s |= (1 << fn)
        out.append(s)
    return out


def _make_invariant_idx(gen):
    """invariant_idx(face, c) = indices SBF dont la restriction a la face vaut
    proj_c (c invariant sur cette face). Mis en cache."""
    n = gen.n
    cache = {}

    def inv(fixed_nodes, fixed_vals, c):
        key = (fixed_nodes, fixed_vals, c)
        r = cache.get(key)
        if r is not None:
            return r
        states = _states_in_face(n, fixed_nodes, fixed_vals)
        r = [i for i in range(gen.M)
             if all(((gen.sbf_tt[i] >> s) & 1) == ((s >> c) & 1) for s in states)]
        cache[key] = r
        return r
    return inv


def _control_trees(n, fixed_nodes, fixed_vals):
    """Genere tous les arbres de controle enracines sur cette face. Un arbre =
    liste de splits (c, face_fixed_nodes, face_fixed_vals). [] = feuille."""
    free = [i for i in range(n) if not (fixed_nodes >> i) & 1]
    yield []
    for c in free:
        nf = fixed_nodes | (1 << c)
        for left in _control_trees(n, nf, fixed_vals):
            for right in _control_trees(n, nf, fixed_vals | (1 << c)):
                yield [(c, fixed_nodes, fixed_vals)] + left + right


def enumerate_core(gen, min_leaves, max_free=None):
    """Dict idx_tuple -> decompSum, pour toutes les dynamiques DECOMPOSABLES dont
    un arbre de controle a >= min_leaves feuilles (et <= max_free noeuds libres,
    si fourni). On deduplique par tuple d'indices AVANT tout calcul, et on ne
    calcule que le decompSum (decompose leger), pas la ligne CSV complete.

    Le coeur a forte profondeur a peu de noeuds libres (#candidats ~ M^{#libres}),
    donc les classes profondes "en epine" sont bon marche ; les classes
    equilibrees a 2 libres (deja couvertes par core_then_walk min_force=2) sont
    les plus cheres -> bornables via max_free."""
    n = gen.n
    inv = _make_invariant_idx(gen)
    repr_col = gen.repr_col
    finest = gen.decomposer.finest
    seen = set()        # idx deja evalues
    core = {}           # idx -> decompSum (decomposables seulement)
    for tree in _control_trees(n, 0, 0):
        if len(tree) + 1 < min_leaves:        # #feuilles = #splits + 1
            continue
        # Un noeud peut etre controle sur PLUSIEURS faces (arbres equilibres) :
        # son idx doit etre invariant sur TOUTES -> intersection ; un seul facteur
        # par noeud (sinon produit cartesien redondant et explosif).
        node_faces = {}
        for (c, fn, fv) in tree:
            node_faces.setdefault(c, []).append((fn, fv))
        if max_free is not None and n - len(node_faces) > max_free:
            continue
        lists, ok = [], True
        for c in range(n):
            faces = node_faces.get(c)
            if faces is None:
                lists.append(range(gen.M))            # noeud libre
                continue
            s = None
            for (fn, fv) in faces:
                iv = set(inv(fn, fv, c))
                s = iv if s is None else (s & iv)
            if not s:
                ok = False
                break
            lists.append(sorted(s))                   # controle : intersection
        if not ok:
            continue
        for idx in product(*lists):                   # idx = (i0, ..., i_{n-1})
            if idx in seen:
                continue
            seen.add(idx)
            cols = [repr_col[idx[j]] for j in range(n)]
            W = [[cols[j][i] for j in range(n)] for i in range(n)]
            d = sum(finest(W).values())
            if d >= 2:
                core[idx] = d
    return core
