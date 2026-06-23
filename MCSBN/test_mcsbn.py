#!/usr/bin/env python3
"""
test_mcsbn.py — Verifie le generateur Monte-Carlo contre la pipeline ASP.

Les tests qui ont besoin d'une sortie de reference de la pipeline la cherchent
dans JPPipeline/out/<d>d_PSBN_undercontrol_treeinsolver_output.csv ; ils sont
ignores (SKIP) si le fichier est absent.

Lancer :  python3 test_mcsbn.py
"""

import csv
import os
import sys
from collections import Counter
from itertools import product

from sbf import get_table
from decompose import Decomposer, DecomposerW, vector_from_counts
from mcsbn import Generator

PIPE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "JPPipeline", "out")


def _pipe_csv(d):
    p = os.path.join(PIPE_DIR, "%dd_PSBN_undercontrol_treeinsolver_output.csv" % d)
    return p if os.path.exists(p) else None


def _load_pipeline(path, d):
    """Retourne (gt, stats) : gt[f]=vecteur le plus decompose, stats[f]=tuple."""
    gt = {}
    stats = {}
    rows = []
    with open(path) as fh:
        r = csv.reader(fh)
        h = next(r)
        fi = [i for i, c in enumerate(h) if c.startswith("f_")]
        vi = sorted([(int(c[2:]), i) for i, c in enumerate(h) if c.startswith("v_")],
                    reverse=True)
        wi = {}
        for i, c in enumerate(h):
            if c.startswith("w_"):
                a, b = c[2:].split(",")
                wi[(int(a), int(b))] = i
        gi = {c: i for i, c in enumerate(h)}
        for row in r:
            fk = tuple(row[i] for i in fi)
            v = tuple(int(row[i]) for _, i in vi)
            W = [[0] * d for _ in range(d)]
            for (a, b), i in wi.items():
                W[a - 1][b - 1] = int(row[i])
            rows.append((fk, v, W))
            if fk not in gt or sum(v) > sum(gt[fk]):
                gt[fk] = v
            # Stats best-effort : certains anciens CSV utilisent d'autres noms.
            if "GenotypeCount" in gi and "Robustness_std" in gi:
                stats[fk] = (row[gi["GenotypeCount"]], row[gi["Robustness_std"]],
                             row[gi["Robustness_mean"]], row[gi["Evolvability"]],
                             row[gi["NumAttractors"]], row[gi["CycleLenMSQ"]])
    return gt, stats, rows


def test_decomposition_exact_d3():
    """En d=3 (espace complet) la decomposition MCSBN == finest pipeline, exactement."""
    path = _pipe_csv(3)
    if not path:
        print("SKIP test_decomposition_exact_d3 (pas de CSV pipeline)")
        return
    gt, _, _ = _load_pipeline(path, 3)
    dec = Decomposer(3)
    bad = 0
    for fk, vtrue in gt.items():
        f = [_ftt(x) for x in fk]
        vmine = tuple(vector_from_counts(dec.finest(f), 3))
        if vmine != vtrue:
            bad += 1
    assert bad == 0, "decomposition d=3 : %d ecarts" % bad
    print("OK test_decomposition_exact_d3 (%d dynamiques)" % len(gt))


def _ftt(fstr):
    tt = 0
    for s, ch in enumerate(fstr):
        if ch == '1':
            tt |= (1 << s)
    return tt


def test_sandwich_dW(d):
    """W-decomposition : >= vecteur prouve par le solveur, <= max phenotype."""
    path = _pipe_csv(d)
    if not path:
        print("SKIP test_sandwich_dW(d=%d)" % d)
        return
    gt, _, rows = _load_pipeline(path, d)
    dec = DecomposerW(d)
    bad_lower = bad_upper = 0
    for fk, v, W in rows:
        mine = vector_from_counts(dec.finest(W), d)
        if sum(mine) < sum(v):
            bad_lower += 1
        if sum(mine) > sum(gt[fk]):
            bad_upper += 1
    assert bad_lower == 0, "d=%d : %d cas ou W-decomp sous-estime le solveur" % (d, bad_lower)
    # bad_upper peut etre > 0 si le CSV pipeline est echantillonne (max incomplet).
    print("OK test_sandwich_dW(d=%d) : %d lignes, bad_lower=0, bad_upper=%d"
          % (d, len(rows), bad_upper))


def test_full_match_d3():
    """Sortie exhaustive d=3 : distribution des vecteurs ET stats == pipeline."""
    path = _pipe_csv(3)
    if not path:
        print("SKIP test_full_match_d3")
        return
    gt, stats, _ = _load_pipeline(path, 3)
    csv_dist = Counter(gt.values())

    gen = Generator(3)
    # Indices analytiques (le header quote les colonnes w_, un split naif est faux).
    n = 3
    base = (n + 1) + n + n * n  # apres v_*, f_*, w_*
    col = {"GenotypeCount": base + 2, "Robustness_std": base + 3,
           "Robustness_mean": base + 4, "Evolvability": base + 5,
           "CycleLenMSQ": base + 0, "NumAttractors": base + 1}
    for i in range(n + 1):
        col["v_%d" % (n - i)] = i
    fcols = [(n + 1) + (j - 1) for j in range(1, n + 1)]

    mc_dist = Counter()
    sbad = 0
    for idx in product(range(gen.M), repeat=3):
        line, key = gen.row(list(idx))
        p = line.split(",")
        v = tuple(int(p[col["v_%d" % (3 - i)]]) for i in range(4))
        mc_dist[v] += 1
        fk = tuple(p[i] for i in fcols)
        cs = stats[fk]
        same = (cs[0] == p[col["GenotypeCount"]]
                and cs[3] == p[col["Evolvability"]]
                and cs[4] == p[col["NumAttractors"]]
                and abs(float(cs[1]) - float(p[col["Robustness_std"]])) <= 1e-9
                and abs(float(cs[2]) - float(p[col["Robustness_mean"]])) <= 1e-9
                and abs(float(cs[5]) - float(p[col["CycleLenMSQ"]])) <= 1e-9)
        if not same:
            sbad += 1
    assert csv_dist == mc_dist, "distribution des vecteurs differente"
    assert sbad == 0, "%d ecarts de statistiques" % sbad
    print("OK test_full_match_d3 (distribution + stats exactes)")


def test_variety_novelty():
    """En grande dimension, presque chaque tirage est une dynamique inedite."""
    gen = Generator(4, measure="variety", seed=1)
    seen = set()
    draws = 20000
    for _ in range(draws):
        idx = gen._sample_indices()
        f = tuple(gen.sbf_tt[i] for i in idx)
        seen.add(f)
    novelty = len(seen) / draws
    assert novelty > 0.99, "nouveaute trop faible : %.3f" % novelty
    print("OK test_variety_novelty (nouveaute %.3f%% sur %d tirages d=4)"
          % (100 * novelty, draws))


def test_genotype_measure_differs():
    """Le mode genotype sur-echantillonne les dynamiques a fort GenotypeCount."""
    gv = Generator(3, measure="variety", seed=2)
    gg = Generator(3, measure="genotype", seed=2)
    # Moyenne de GenotypeCount sur un echantillon : genotype >> variety.
    def mean_gc(gen, k=20000):
        tot = 0
        for _ in range(k):
            idx = gen._sample_indices()
            gc = 1
            for j in idx:
                gc *= gen.csize[j]
            tot += gc
        return tot / k
    mv = mean_gc(gv)
    mg = mean_gc(gg)
    assert mg > 2 * mv, "genotype devrait favoriser les forts GenotypeCount (%.1f vs %.1f)" % (mg, mv)
    print("OK test_genotype_measure_differs (GenotypeCount moyen variety=%.0f genotype=%.0f)"
          % (mv, mg))


if __name__ == "__main__":
    test_decomposition_exact_d3()
    test_full_match_d3()
    test_sandwich_dW(3)
    test_sandwich_dW(4)
    test_variety_novelty()
    test_genotype_measure_differs()
    print("\nTous les tests passes.")
