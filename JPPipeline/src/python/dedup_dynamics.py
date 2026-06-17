"""
Déduplication des dynamiques d'un CSV de la pipeline (variante undercontrol).

Une dynamique est entièrement déterminée par le tuple des fonctions de transition
(f_1,...,f_n). undercontrol est *complet* (il trouve toutes les dynamiques
distinctes) mais *redondant* : une même dynamique apparaît une fois par arbre de
décomposition qu'elle vérifie, donc avec plusieurs vecteurs de décomposition.

On déduplique par (f_1,...,f_n) en gardant la décomposition LA PLUS FINE. Raffiner
une décomposition (découper une face en deux) augmente strictement le nombre total
de sous-faces, donc « la plus fine » = celle qui maximise la somme des composantes
du vecteur v_*. (Vérifié sans ex aequo en d=3.)

Les colonnes non liées à la décomposition (AtrSize, dynamics, GenotypeCount,
R_P_*, E_P) ne dépendent que de la dynamique : on conserve telle quelle la ligne
correspondant au vecteur canonique.

Usage :
  python dedup_dynamics.py in.csv [out.csv]
  (out.csv par défaut : in_dedup.csv)
"""

import csv
import sys
from collections import defaultdict


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    in_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else in_path.rsplit(".", 1)[0] + "_dedup.csv"

    with open(in_path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = [r for r in reader if r]

    idx = {h: i for i, h in enumerate(header)}
    f_cols = sorted((h for h in header if h.startswith("f_")), key=lambda c: int(c[2:]))
    v_cols = [h for h in header if h.startswith("v_")]
    if not f_cols:
        sys.exit("Pas de colonnes f_* : impossible d'identifier les dynamiques.")
    if not v_cols:
        sys.exit("Pas de colonnes v_* : rien à dédupliquer.")

    f_i = [idx[c] for c in f_cols]
    v_i = [idx[c] for c in v_cols]

    by_dyn = defaultdict(list)
    for r in rows:
        by_dyn[tuple(r[i] for i in f_i)].append(r)

    kept = []
    ties = 0
    for group in by_dyn.values():
        best, best_sum, best_vec, tie = None, -1, None, False
        for r in group:
            vec = tuple(int(r[i]) for i in v_i)
            s = sum(vec)
            if s > best_sum:
                best, best_sum, best_vec, tie = r, s, vec, False
            elif s == best_sum and vec != best_vec:
                tie = True
        if tie:
            ties += 1
        kept.append(best)

    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(kept)

    print(f"Entrée  : {len(rows)} lignes")
    print(f"Sortie  : {len(kept)} dynamiques distinctes -> {out_path}")
    if ties:
        print(f"ATTENTION : {ties} dynamiques avec ex aequo à la somme max "
              f"(choix non unique, premier rencontré gardé).")


if __name__ == "__main__":
    main()
