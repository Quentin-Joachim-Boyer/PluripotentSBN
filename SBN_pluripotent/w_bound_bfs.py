#!/usr/bin/env python3
"""
w_bound_bfs.py — Variante de w_bound.py évitant la brute force sur l'espace
                  des poids pour énumérer T_n (les SBF réalisables).

Idée : dans l'arrangement des 2^n hyperplans {w : sum_i w_i x_i = 0} (un par
point x), deux régions voisines (séparées par une seule hyperplan) donnent des
fonctions f qui ne diffèrent qu'en un seul point x. Comme cet arrangement est
connexe, on peut donc atteindre toute T_n par un simple parcours en largeur
dans l'espace des fonctions, en partant de f=0 (réalisée par w=0) et en
testant à chaque étape "retourner le bit x fait-il encore une fonction
réalisable ?" via une simple faisabilité LP (réelle, pas de recherche de
rayon de poids entier).

L'ILP entier (identique à w_bound.py) n'intervient qu'ensuite, pour calculer
la borne de poids minimale ||w||_inf de chaque fonction réalisable trouvée.

Usage :
    python3 w_bound_bfs.py [--max-n N]

Reproduit w_bound(1..5) = 1,1,2,3,5 (cf. rapport_stage.tex).
"""

import argparse
import itertools
from collections import deque

import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds


def is_realizable(f, xs, n):
    """Faisabilité LP réelle : existe-t-il w in R^n tel que f_w = f ?"""
    P = [x for x, b in zip(xs, f) if b == 1]
    N = [x for x, b in zip(xs, f) if b == 0]

    # sum x_i w_i >= 1  <=>  -x . w <= -1
    A_ub, b_ub = [], []
    for x in P:
        A_ub.append([-xi for xi in x]); b_ub.append(-1)
    for x in N:
        A_ub.append(list(x)); b_ub.append(0)

    res = linprog(c=np.zeros(n), A_ub=A_ub, b_ub=b_ub,
                   bounds=[(-100, 100)] * n, method="highs")
    return res.success


def enumerate_realizable_sbfs(n):
    """BFS dans l'espace des fonctions, partant de f=0, via retournements
    d'un seul bit testés par faisabilité LP. Retourne l'ensemble T_n."""
    xs = list(itertools.product((0, 1), repeat=n))
    f0 = tuple(0 for _ in xs)  # réalisée par w=0
    seen = {f0}
    queue = deque([f0])
    while queue:
        f = queue.popleft()
        for i in range(len(xs)):
            g = f[:i] + (1 - f[i],) + f[i + 1:]
            if g in seen:
                continue
            if is_realizable(g, xs, n):
                seen.add(g)
                queue.append(g)
    return seen, xs


def minimal_weight_bound(f, xs, n, big_m):
    """ILP entier : W(f) = min ||w||_inf tel que f_w = f (cf. w_bound.py)."""
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
    sbfs, xs = enumerate_realizable_sbfs(n)
    bounds = {f: minimal_weight_bound(f, xs, n, big_m) for f in sbfs}
    worst_f = max(bounds, key=bounds.get)
    return max(bounds.values()), len(sbfs), worst_f


def main():
    parser = argparse.ArgumentParser(
        description="Calcule w_bound(n) via BFS + faisabilité LP (sans brute force sur les poids).")
    parser.add_argument("--max-n", type=int, default=5)
    parser.add_argument("--big-m", type=int, default=200)
    args = parser.parse_args()

    print(f"{'n':>2} | {'w_bound(n)':>10} | {'|T_n|':>6}")
    print("-" * 30)
    for n in range(1, args.max_n + 1):
        bound, count, worst_f = w_bound(n, args.big_m)
        print(f"{n:>2} | {bound:>10} | {count:>6}")


if __name__ == "__main__":
    main()
