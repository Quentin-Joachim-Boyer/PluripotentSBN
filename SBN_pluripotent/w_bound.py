#!/usr/bin/env python3
"""
w_bound.py — Calcule w_bound(n), la borne de poids entiers minimale permettant
             de réaliser toutes les fonctions booléennes à seuil (SBF) de
             dimension n. Cf. Redaction/rapport_stage.tex, section "Fonctions
             booléennes à seuil (SBF)" : formalisation via un programme
             linéaire en nombres entiers (ILP).

ATTENTION — méthode NON exacte (heuristique de validation seulement) : voir
w_bound_orbits.py pour la version exacte, à préférer pour tout résultat
publiable (en particulier n=6). Le défaut ici : la brute force sur un rayon
R ne peut PAS garantir d'avoir trouvé toute T_n. Une SBF dont la borne
minimale W(f) dépasse R n'est réalisée par AUCUN poids de la grille [-R,R]^n,
donc n'est jamais générée ni testée : le max rapporté peut sous-estimer
silencieusement w_bound(n). Le garde-fou "bound >= r" ne détecte que le cas
où le maximum trouvé touche pile R ; il ne prouve rien si R est insuffisant
mais que le max tronqué reste strictement sous R. Le fait de retrouver
1,1,2,3,5 est une coïncidence confirmée a posteriori, pas une preuve produite
par ce script.

Méthode :
  1. Énumération brute des fonctions réalisables T_n (une passe sur les
     vecteurs de poids w dans [-R,R]^n, dédupliquées par la fonction f_w
     qu'elles réalisent). Aucune garantie que R soit suffisant (cf. ATTENTION
     ci-dessus) ; le "garde-fou" décrit plus bas est un indice, pas une preuve.
  2. Pour chaque f réalisable trouvée, résolution de l'ILP minimisant
     B = ||w||_inf sous contrainte f_w = f (exact, indépendant de R) :

       min B
       s.c.  sum_i w_i x_i >= 1   pour x in P = {x : f(x)=1}
             sum_i w_i x_i <= 0   pour x in N = {x : f(x)=0}
             -B <= w_i <= B

  3. w_bound(n) = max sur f in T_n de la borne minimale obtenue.

Usage :
    python3 w_bound.py [--max-n N] [--search-range R]

Reproduit w_bound(1..5) = 1,1,2,3,5 (cf. rapport).
"""

import argparse
import itertools
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds


def enumerate_realizable_sbfs(n, search_range):
    """Énumère T_n par force brute sur w in [-R,R]^n, dédupliqué par f.
    Retourne un dict {f (tuple de bits, un par x in {0,1}^n) -> un w témoin}."""
    xs = list(itertools.product((0, 1), repeat=n))
    seen = {}
    for w in itertools.product(range(-search_range, search_range + 1), repeat=n):
        f = tuple(1 if sum(wi * xi for wi, xi in zip(w, x)) > 0 else 0 for x in xs)
        if f not in seen:
            seen[f] = w
    return seen, xs


def minimal_weight_bound(f, xs, n, big_m):
    """Résout l'ILP donnant W(f) = min ||w||_inf tel que f_w = f."""
    P = [x for x, b in zip(xs, f) if b == 1]
    N = [x for x, b in zip(xs, f) if b == 0]

    # Variables : w_1..w_n, B
    nvar = n + 1
    c = np.zeros(nvar)
    c[-1] = 1  # minimise B

    rows, lbs, ubs = [], [], []
    for x in P:
        rows.append(list(x) + [0]); lbs.append(1); ubs.append(np.inf)
    for x in N:
        rows.append(list(x) + [0]); lbs.append(-np.inf); ubs.append(0)
    for i in range(n):
        row = [0] * nvar; row[i] = 1; row[-1] = -1
        rows.append(row); lbs.append(-np.inf); ubs.append(0)   # w_i - B <= 0
        row = [0] * nvar; row[i] = -1; row[-1] = -1
        rows.append(row); lbs.append(-np.inf); ubs.append(0)   # -w_i - B <= 0

    constraints = LinearConstraint(np.array(rows), np.array(lbs), np.array(ubs))
    bounds = Bounds([-big_m] * n + [0], [big_m] * n + [big_m])
    integrality = np.ones(nvar)

    res = milp(c, constraints=constraints, bounds=bounds, integrality=integrality)
    if not res.success:
        raise RuntimeError(f"ILP infaisable pour f={f} (big_m={big_m} trop petit ?)")
    return int(round(res.fun))


def w_bound(n, search_range, big_m):
    sbfs, xs = enumerate_realizable_sbfs(n, search_range)
    bounds = {f: minimal_weight_bound(f, xs, n, big_m) for f in sbfs}
    worst_f = max(bounds, key=bounds.get)
    return max(bounds.values()), len(sbfs), worst_f, sbfs[worst_f]


def main():
    parser = argparse.ArgumentParser(
        description="Calcule w_bound(n) (borne de poids entiers pour toutes les SBF de dimension n) via ILP.")
    parser.add_argument("--max-n", type=int, default=5,
                         help="dimension maximale calculée (défaut 5 ; au-delà, la brute-force en R devient lente)")
    parser.add_argument("--search-range", type=int, default=None,
                         help="rayon R de la recherche brute des poids réalisables (défaut : dépend de n)")
    parser.add_argument("--big-m", type=int, default=200,
                         help="borne supérieure utilisée dans l'ILP pour B (défaut 200, largement suffisant)")
    args = parser.parse_args()

    print(f"{'n':>2} | {'w_bound(n)':>10} | {'|T_n|':>6} | pire SBF (témoin w)")
    print("-" * 60)
    for n in range(1, args.max_n + 1):
        # Rayon de recherche par défaut : marge de sécurité au-delà de la
        # borne connue/estimée, pour ne pas manquer de fonctions réalisables.
        r = args.search_range or (n + 3)
        bound, count, worst_f, witness_w = w_bound(n, r, args.big_m)

        # Sanity check : si le pire cas atteint pile le rayon de recherche R,
        # c'est peut-être parce que T_n n'a pas été entièrement capturée.
        if bound >= r:
            print(f"  [!] n={n} : bound={bound} atteint le rayon de recherche R={r}, "
                  f"relancer avec --search-range plus grand pour vérifier la stabilité.")

        print(f"{n:>2} | {bound:>10} | {count:>6} | {witness_w}")


if __name__ == "__main__":
    main()
