#!/usr/bin/env python3
"""
w_bound_orbits.py — Variante de w_bound_bfs.py avec réduction par symétrie,
                     pour pousser le calcul jusqu'à n=6 sans brute force sur
                     les poids ni exploration complète de T_n.

Amélioration par rapport à w_bound_bfs.py : deux fonctions f, g liées par une
permutation des n coordonnées ont la même borne minimale ||w||_inf (permuter
les poids ne change pas leur norme infinie). Comme la relation de voisinage du
BFS (un seul bit de f retourné) est compatible avec cette action du groupe
S_n, on montre qu'explorer les 2^n voisins d'UN SEUL représentant par orbite
suffit à découvrir toutes les orbites voisines (si x' = sigma(x) et r' =
sigma(r), retourner le bit x' de r' est équivalent-orbite à retourner le bit
x de r ; comme x' parcourt tous les indices quand x le fait, l'ensemble des
orbites atteintes est identique).

On obtient ainsi T_n / S_n (les classes d'équivalence) au lieu de T_n, avec un
facteur de réduction pouvant aller jusqu'à n! (720 pour n=6), pour un coût de
canonicalisation vectorisé (numpy) négligeable.

Usage :
    python3 w_bound_orbits.py [--max-n N]

Reproduit w_bound(1..5) = 1,1,2,3,5 comme les autres variantes ; permet
d'atteindre n=6 en un temps raisonnable.
"""

import argparse
import itertools
from collections import deque

import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds


def build_permutation_matrix(n, xs):
    """Pour chaque permutation sigma de S_n, la table de réindexation des 2^n
    points : perm_matrix[k, j] = indice, dans xs, du point xs[j] dont les
    coordonnées ont été permutées par sigma_k. Shape (n!, 2^n)."""
    xs_index = {x: i for i, x in enumerate(xs)}
    perms = list(itertools.permutations(range(n)))
    matrix = np.empty((len(perms), len(xs)), dtype=np.int64)
    for k, sigma in enumerate(perms):
        for j, x in enumerate(xs):
            x_sigma = tuple(x[sigma[i]] for i in range(n))
            matrix[k, j] = xs_index[x_sigma]
    return matrix


def canonical(f_arr, perm_matrix, weights):
    """Représentant canonique de l'orbite de f sous S_n : parmi les n!
    permutées de f, celle de plus petit encodage entier (ordre total
    arbitraire mais cohérent, pas besoin d'être lexicographique)."""
    permuted = f_arr[perm_matrix]                  # (n!, 2^n)
    packed = permuted @ weights                     # (n!,) entiers
    best = int(np.argmin(packed))
    return tuple(int(b) for b in permuted[best]), int(packed[best])


def is_realizable(f, xs, n):
    """Faisabilité LP réelle : existe-t-il w in R^n tel que f_w = f ?"""
    P = [x for x, b in zip(xs, f) if b == 1]
    N = [x for x, b in zip(xs, f) if b == 0]
    A_ub, b_ub = [], []
    for x in P:
        A_ub.append([-xi for xi in x]); b_ub.append(-1)
    for x in N:
        A_ub.append(list(x)); b_ub.append(0)
    res = linprog(c=np.zeros(n), A_ub=A_ub, b_ub=b_ub,
                   bounds=[(-100, 100)] * n, method="highs")
    return res.success


def enumerate_orbits(n):
    """BFS sur les orbites de T_n sous S_n : un seul représentant canonique
    par orbite, ses 2^n voisins (un bit retourné) suffisent à découvrir
    toutes les orbites adjacentes (cf. docstring du module)."""
    xs = list(itertools.product((0, 1), repeat=n))
    N = len(xs)
    weights = 2 ** np.arange(N, dtype=np.int64)
    perm_matrix = build_permutation_matrix(n, xs)

    f0 = np.zeros(N, dtype=np.int64)                # f=0, réalisée par w=0
    f0_canon, f0_id = canonical(f0, perm_matrix, weights)

    seen_ids = {f0_id}
    dead_ids = set()                                 # orbites confirmées infaisables
    reps = {f0_id: f0_canon}
    queue = deque([f0_canon])

    while queue:
        f = queue.popleft()
        f_arr = np.array(f, dtype=np.int64)
        for i in range(N):
            g_arr = f_arr.copy(); g_arr[i] = 1 - g_arr[i]
            g_canon, g_id = canonical(g_arr, perm_matrix, weights)
            if g_id in seen_ids or g_id in dead_ids:
                continue
            if is_realizable(g_canon, xs, n):
                seen_ids.add(g_id)
                reps[g_id] = g_canon
                queue.append(g_canon)
            else:
                dead_ids.add(g_id)
    return reps, xs


def minimal_weight_bound(f, xs, n, big_m):
    """ILP entier : W(f) = min ||w||_inf tel que f_w = f (identique aux
    autres variantes ; invariant par permutation des coordonnées, donc valide
    pour n'importe quel représentant de l'orbite)."""
    P = [x for x, b in zip(xs, f) if b == 1]
    N = [x for x, b in zip(xs, f) if b == 0]

    nvar = n + 1
    c = np.zeros(nvar); c[-1] = 1

    rows, lbs, ubs = [], [], []
    for x in P:
        rows.append(list(x) + [0]); lbs.append(1); ubs.append(np.inf)
    for x in N:
        rows.append(list(x) + [0]); lbs.append(-np.inf); ubs.append(0)
    for i in range(n):
        row = [0] * nvar; row[i] = 1; row[-1] = -1
        rows.append(row); lbs.append(-np.inf); ubs.append(0)
        row = [0] * nvar; row[i] = -1; row[-1] = -1
        rows.append(row); lbs.append(-np.inf); ubs.append(0)

    constraints = LinearConstraint(np.array(rows), np.array(lbs), np.array(ubs))
    bounds = Bounds([-big_m] * n + [0], [big_m] * n + [big_m])
    res = milp(c, constraints=constraints, bounds=bounds, integrality=np.ones(nvar))
    if not res.success:
        raise RuntimeError(f"ILP infaisable pour f={f} (big_m={big_m} trop petit ?)")
    return int(round(res.fun))


def w_bound(n, big_m):
    reps, xs = enumerate_orbits(n)
    bounds = {fid: minimal_weight_bound(f, xs, n, big_m) for fid, f in reps.items()}
    worst_id = max(bounds, key=bounds.get)
    return max(bounds.values()), len(reps), reps[worst_id]


def main():
    parser = argparse.ArgumentParser(
        description="Calcule w_bound(n) via BFS d'orbites sous S_n (sans brute force sur les poids).")
    parser.add_argument("--max-n", type=int, default=5)
    parser.add_argument("--big-m", type=int, default=200)
    args = parser.parse_args()

    print(f"{'n':>2} | {'w_bound(n)':>10} | {'#orbites':>9} | pire SBF (repr. canonique w)")
    print("-" * 70)
    for n in range(1, args.max_n + 1):
        bound, n_orbits, worst_f = w_bound(n, args.big_m)
        print(f"{n:>2} | {bound:>10} | {n_orbits:>9} | {worst_f}")


if __name__ == "__main__":
    main()
