"""
Analyses des fiches de Redaction/plan_figures.md, sur les CSV de la passe.

Chaque fiche recalcule ses nombres (attendu / obtenu, les valeurs attendues
étant celles de plan_figures.md), choisit les lignes à capturer et les écrit
dans un petit CSV préfixé par la dimension (3d_<fiche>_<programme>.csv), que
les pages HTML ouvrent directement. Sauf critère propre à la fiche, la ligne
retenue est celle qui a le moins de poids non nuls, puis la plus petite somme
des |w|, puis la première dans l'ordre trié (décision T7). Une dynamique déjà
retenue par une fiche précédente, dans l'ordre du plan, est écartée des
suivantes, pour que deux figures ne montrent pas la même.

Conventions (annexe A.2) : l'état s a pour bit i-1 la valeur du nœud i, le
caractère s de f_j donne le nœud j à l'état suivant, et f_j(s) = 1 si la somme
des w_i,j des nœuds i actifs dans s est > 0. Une étiquette d'état s'écrit
x3x2x1, comme dans sbn_viz.
"""

import csv
import gzip
import itertools
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
V0200 = (0, 2, 0, 0)
V0120 = (0, 1, 2, 0)
ARBRE_FIXE_0200 = "3[*,*]"  # arbre de setup_btree_3d.lp pour ⟨0,2,0,0⟩ (programmes undercontrol)


# ---------------------------------------------------------------------------
# Lecture des CSV et outils sur les dynamiques

def lire(path):
    path = Path(path)
    if path.suffix == ".gz":
        with gzip.open(path, "rt", newline="") as f:
            return f.read()
    return path.read_text(newline="")


class Table:
    """Un CSV de la passe ; la ligne k du corps est la solution n° k + 1."""

    def __init__(self, path):
        self.nom = Path(path).name
        self.lignes = lire(path).splitlines()
        tete = next(csv.reader([self.lignes[0]]))
        rows = list(csv.reader(self.lignes[1:]))
        self.d = d = sum(c.startswith("f_") for c in tete)
        iv = [tete.index(f"v_{k}") for k in range(d, -1, -1)]
        jf = [tete.index(f"f_{j}") for j in range(1, d + 1)]
        iw = [tete.index(f"w_{i},{j}") for i in range(1, d + 1) for j in range(1, d + 1)]
        it = tete.index("tree") if "tree" in tete else None
        self.v = [tuple(int(r[i]) for i in iv) for r in rows]
        self.f = [tuple(r[i] for i in jf) for r in rows]
        self.w = [tuple(int(r[i]) for i in iw) for r in rows]
        self.tree = [r[it] if it is not None else "" for r in rows]
        self._tete, self._rows = tete, rows

    def __len__(self):
        return len(self.v)

    def col(self, nom):
        i = self._tete.index(nom)
        return [float(r[i]) for r in self._rows]

    def t7(self, k):
        """Clé du choix par défaut (T7)."""
        return (sum(x != 0 for x in self.w[k]), sum(abs(x) for x in self.w[k]), k)

    def dyn(self, vec=None):
        """Dynamiques distinctes, éventuellement d'un seul vecteur."""
        return {self.f[k] for k in range(len(self)) if vec is None or self.v[k] == vec}


def seuil(w, d):
    """Fonctions de transition réalisées par la matrice de poids w (aplatie)."""
    return tuple("".join("1" if sum(w[(i - 1) * d + j - 1] for i in range(1, d + 1)
                                    if (s >> (i - 1)) & 1) > 0 else "0"
                         for s in range(2 ** d)) for j in range(1, d + 1))


def transitions(f):
    d = len(f)
    return [sum(int(f[j][s]) << j for j in range(d)) for s in range(2 ** d)]


def etiquette(s, d):
    return format(s, f"0{d}b")


def faces_propres(d):
    """Sous-cubes de dimension 1 à d - 1, comme ensembles d'états."""
    faces = []
    for fixe in itertools.product([None, 0, 1], repeat=d):
        if all(x is None for x in fixe) or all(x is not None for x in fixe):
            continue
        faces.append(frozenset(s for s in range(2 ** d)
                               if all(x is None or ((s >> i) & 1) == x for i, x in enumerate(fixe))))
    return faces


def faces_invariantes(f):
    T = transitions(f)
    return [F for F in faces_propres(len(f)) if all(T[s] in F for s in F)]


def coordonnees_autonomes(f):
    """Sous-ensembles propres A des nœuds dont l'évolution ne dépend que de A
    (comme la partie contrôle (x1, x2) de la dynamique de P0)."""
    d, T = len(f), transitions(f)
    autonomes = []
    for r in range(1, d):
        for A in itertools.combinations(range(d), r):
            masque = sum(1 << i for i in A)
            image = {}
            if all(image.setdefault(s & masque, T[s] & masque) == T[s] & masque for s in range(2 ** d)):
                autonomes.append(tuple(i + 1 for i in A))
    return autonomes


def lire_arbre(a):
    """'2[1[*,*],*]' -> (2, (1, '*', '*'), '*')."""
    pos = 0

    def rec():
        nonlocal pos
        if a[pos] == "*":
            pos += 1
            return "*"
        j = a.index("[", pos)
        n, pos = int(a[pos:j]), j + 1
        g = rec()
        pos += 1  # virgule
        h = rec()
        pos += 1  # crochet fermant
        return (n, g, h)
    return rec()


def faces_distinctes(f, arbre):
    """Condition de Laurent (dif_faces), à chaque coupe de l'arbre : les deux
    moitiés portent des sous-dynamiques différentes, si bien que le nœud de
    contrôle change réellement l'évolution des autres nœuds."""
    d, T = len(f), transitions(f)

    def rec(noeud, fixes):
        if noeud == "*":
            return True
        n, g, h = noeud
        libres = [i for i in range(d) if i + 1 != n and i + 1 not in fixes]
        masque = sum(1 << i for i in libres)
        base = sum(v << (i - 1) for i, v in fixes.items())
        etats = [base | sum(((a >> k) & 1) << i for k, i in enumerate(libres)) for a in range(2 ** len(libres))]
        return (any(T[s] & masque != T[s | 1 << (n - 1)] & masque for s in etats)
                and rec(g, {**fixes, n: 0}) and rec(h, {**fixes, n: 1}))
    return rec(lire_arbre(arbre), {})


def vec_txt(v):
    return "⟨" + ",".join(map(str, v)) + "⟩"


def poids_txt(w, d):
    return ", ".join(f"{i}→{j} : {w[(i - 1) * d + j - 1]:+d}" for i in range(1, d + 1)
                     for j in range(1, d + 1) if w[(i - 1) * d + j - 1])


# ---------------------------------------------------------------------------
# Résultats

DEJA = set()  # dynamiques déjà retenues par une fiche (remis à zéro par toutes())


def libres(t, ks):
    """Les lignes de ks dont la dynamique n'a pas encore été retenue."""
    return [k for k in ks if t.f[k] not in DEJA]

class Fiche:
    def __init__(self, ident, titre):
        self.r = {"fiche": ident, "titre": titre, "comptes": [], "fichiers": [], "notes": []}

    def compte(self, quoi, obtenu, attendu=None, tol=None):
        if attendu is None:
            ok = None
        elif tol is not None:
            ok = abs(obtenu - attendu) <= tol + 1e-12
        else:
            ok = obtenu == attendu
        self.r["comptes"].append({"quoi": quoi, "attendu": attendu, "obtenu": obtenu, "ok": ok})

    def note(self, texte):
        self.r["notes"].append(texte)

    def extraire(self, t, ks, nom, dossier, legende=""):
        """Écrit les lignes ks de t dans dossier/nom (ordre du fichier)."""
        ks = sorted(set(ks))
        DEJA.update(t.f[k] for k in ks)
        (dossier / nom).write_text("\n".join([t.lignes[0]] + [t.lignes[k + 1] for k in ks]) + "\n")
        self.r["fichiers"].append({
            "fichier": nom, "source": t.nom, "legende": legende,
            "lignes": [{"n": k + 1, "vecteur": vec_txt(t.v[k]), "arbre": t.tree[k],
                        "poids": poids_txt(t.w[k], t.d),
                        "poids_realisent_f": seuil(t.w[k], t.d) == t.f[k]} for k in ks]})


# ---------------------------------------------------------------------------
# Fiches

def controle_poids(tables):
    F = Fiche("Contrôle", "Les poids de chaque ligne réalisent ses fonctions de transition")
    import numpy as np
    for t in tables:  # même calcul que seuil(), vectorisé
        n, d, S = len(t), t.d, 2 ** t.d
        W = np.array(t.w, dtype=np.int64).reshape(n, d, d)
        B = np.array([[(s >> i) & 1 for i in range(d)] for s in range(S)], dtype=np.int64)
        actif = np.einsum("si,nij->njs", B, W) > 0
        f = np.frombuffer("".join("".join(x) for x in t.f).encode(), dtype=np.uint8).reshape(n, d, S) == ord("1")
        F.compte(f"lignes où f ≠ seuil(w), {t.nom}", int((actif != f).any(axis=(1, 2)).sum()), 0)
    return F


def fiche_C1(PU, dossier):
    F = Fiche("C1", "Programme de Laurent : les dynamiques à faces identiques qu'il écarte")
    ks = [k for k in range(len(PU)) if PU.v[k] == V0200]
    dyn = {PU.f[k] for k in ks}
    F.compte("dynamiques de ⟨0,2,0,0⟩ (PSBN_undercontrol)", len(dyn), 225)

    cand = [k for k in ks if not faces_distinctes(PU.f[k], ARBRE_FIXE_0200)]
    identiques = {PU.f[k] for k in cand}
    F.compte("dont faces x₃ = 0 et x₃ = 1 identiques", len(identiques), 36)
    laurent = REPO / "SBN_pluripotent_Laurent/SBN_pluripotent/3d_<0,2,0,0>_output.csv"
    if laurent.exists():
        rows = list(csv.reader(laurent.read_text().splitlines()))
        jf = [rows[0].index(f"f_{j}") for j in (1, 2, 3)]
        L = {tuple("".join(str((int(r[c]) >> s) & 1) for s in range(8)) for c in jf) for r in rows[1:]}
        F.compte("dynamiques de Laurent", len(L), 189)
        F.compte("Laurent = les autres dynamiques de ⟨0,2,0,0⟩", L == dyn - identiques, True)
    else:
        F.note("Fichier de Laurent absent (non versionné) : comparaison avec ses 189 dynamiques non refaite.")
    choix = min(libres(PU, cand), key=PU.t7)
    F.extraire(PU, [choix], "3d_C1_PSBN_undercontrol.csv", dossier)
    return F


def fiche_C2_C3(PU, PT_u, dossier):
    F2 = Fiche("C2", "PTBN_undercontrol : un réseau non PSBN")
    ks = [k for k in range(len(PT_u)) if PT_u.v[k] == V0200]
    F2.compte("dynamiques de ⟨0,2,0,0⟩ (PTBN_undercontrol)", len({PT_u.f[k] for k in ks}), 1024)
    hors = {PT_u.f[k] for k in ks} - PU.dyn(V0200)
    F2.compte("dont absentes de PSBN_undercontrol", len(hors), 799)
    c2 = min(libres(PT_u, [k for k in ks if PT_u.f[k] in hors]), key=PT_u.t7)
    F2.extraire(PT_u, [c2], "3d_C2_PTBN_undercontrol.csv", dossier)

    F3 = Fiche("C3", "PSBN_undercontrol : un PSBN proche de celui de C2")
    ks = [k for k in range(len(PU)) if PU.v[k] == V0200]
    F3.compte("dynamiques de ⟨0,2,0,0⟩ (PSBN_undercontrol)", len({PU.f[k] for k in ks}), 225)

    def l1(k):
        return sum(abs(a - b) for a, b in zip(PU.w[k], PT_u.w[c2]))
    c3 = min(libres(PU, ks), key=lambda k: (l1(k),) + PU.t7(k))
    F3.compte("distance L1 aux poids de C2", l1(c3))
    F3.extraire(PU, [c3], "3d_C3_PSBN_undercontrol.csv", dossier)
    return F2, F3


def plus_fin(t):
    """Pour chaque dynamique, la plus grande somme des coefficients de ses vecteurs."""
    best = defaultdict(int)
    for v, f in zip(t.v, t.f):
        best[f] = max(best[f], sum(v))
    return best


C4_ATTENDU = {(1, 0, 0, 0): (32768, 658), (0, 2, 0, 0): (658, 139), (0, 1, 2, 0): (139, 73),
              (0, 1, 1, 2): (70, 34), (0, 1, 0, 4): (31, 10), (0, 0, 4, 0): (16, 13),
              (0, 0, 3, 2): (13, 10), (0, 0, 2, 4): (10, 4), (0, 0, 1, 6): (4, 1), (0, 0, 0, 8): (1, 0)}


def fiche_C4(PS, dossier):
    F = Fiche("C4", "Table « échelles de décomposition » (d = 3)")
    best = plus_fin(PS)
    lignes = ["vecteur,dynamiques,plus_finement_decomposables"]
    for v in sorted(set(PS.v), reverse=True):
        dyn = PS.dyn(v)
        fines = sum(best[f] > sum(v) for f in dyn)
        att = C4_ATTENDU.get(v, (None, None))
        F.compte(f"{vec_txt(v)} : dynamiques", len(dyn), att[0])
        F.compte(f"{vec_txt(v)} : plus finement décomposables", fines, att[1])
        lignes.append(f"\"{vec_txt(v)}\",{len(dyn)},{fines}")
    (dossier / "C4_table_d3.csv").write_text("\n".join(lignes) + "\n")
    F.note("Table écrite dans C4_table_d3.csv.")
    return F


def fiche_C5(PS, dossier):
    F = Fiche("C5", "Un PSBN « trop décomposable » sur ⟨0,2,0,0⟩")
    best = plus_fin(PS)
    cand = {f for f in PS.dyn(V0200) if best[f] > 2}
    F.compte("dynamiques de ⟨0,2,0,0⟩ plus finement décomposables", len(cand), 139)
    par_f = defaultdict(list)
    for k in range(len(PS)):
        if PS.f[k] in cand:
            par_f[PS.f[k]].append(k)
    # Une paire (ligne ⟨0,2,0,0⟩, ligne la plus fine) par dynamique ; on préfère
    # les paires de mêmes poids, pour que les deux captures montrent le même réseau.
    paires = [(a, b) for ks in par_f.values() for a in libres(PS, ks) if PS.v[a] == V0200
              for b in ks if sum(PS.v[b]) == best[PS.f[b]]]
    a, b = min(paires, key=lambda p: (PS.w[p[0]] != PS.w[p[1]],) + PS.t7(p[0]) + PS.t7(p[1]))
    F.compte("dynamiques dont une ligne ⟨0,2,0,0⟩ et une ligne la plus fine ont les mêmes poids",
             len({PS.f[x] for x, y in paires if PS.w[x] == PS.w[y]}))
    F.extraire(PS, [a, b], "3d_C5_PSBN_undercontrol_taggedtree.csv", dossier,
               "la même dynamique avec l'arbre ⟨0,2,0,0⟩ puis l'arbre le plus fin")
    return F


def fiche_C6_C7(PU, PT_u, PS, PT, PS_tis, PT_tis, dossier):
    F6 = Fiche("C6", "PTBN_undercontrol_treeinsolver : autre orientation, TBN seulement")
    cand = (PT_tis.dyn(V0200) - PS_tis.dyn(V0200)) - PT_u.dyn(V0200)
    F6.compte("dynamiques de ⟨0,2,0,0⟩ dans PTBN_treeinsolver, absentes de PSBN_treeinsolver "
              "et de PTBN_undercontrol", len(cand), 1538)
    ks = [k for k in range(len(PT)) if PT.v[k] == V0200 and PT.f[k] in cand]
    F6.compte("candidates sans ligne ⟨0,2,0,0⟩ dans PTBN_taggedtree (T4)", len(cand - {PT.f[k] for k in ks}), 0)
    F6.extraire(PT, [min(libres(PT, ks), key=PT.t7)], "3d_C6_PTBN_undercontrol_taggedtree.csv", dossier,
                "capture depuis taggedtree, qui porte l'arbre (T4)")

    F7 = Fiche("C7", "PSBN_undercontrol_treeinsolver : décomposable en SBN, autre orientation")
    cand = PS_tis.dyn(V0200) - PU.dyn(V0200)
    F7.compte("dynamiques de ⟨0,2,0,0⟩ dans PSBN_treeinsolver, absentes de PSBN_undercontrol",
              len(cand), 433)
    ks = [k for k in range(len(PS)) if PS.v[k] == V0200 and PS.f[k] in cand]
    F7.compte("candidates sans ligne ⟨0,2,0,0⟩ dans PSBN_taggedtree (T4)", len(cand - {PS.f[k] for k in ks}), 0)
    F7.extraire(PS, [min(libres(PS, ks), key=PS.t7)], "3d_C7_PSBN_undercontrol_taggedtree.csv", dossier,
                "capture depuis taggedtree, qui porte l'arbre (T4)")
    return F6, F7


C8_ARBRES = ["2[1[*,3[*,*]],3[*,1[*,*]]]", "3[1[*,2[*,*]],2[1[*,*],*]]"]


def fiche_C8(PT, dossier):
    F = Fiche("C8", "PTBN_undercontrol_taggedtree sur ⟨0,0,2,4⟩ : moitiés coupées selon des nœuds différents")
    ks = []
    for a in C8_ARBRES:
        ka = [k for k in range(len(PT)) if PT.tree[k] == a]
        F.compte(f"lignes de l'arbre {a}", len(ka), 2)
        ks += ka
    F.extraire(PT, ks, "3d_C8_PTBN_undercontrol_taggedtree.csv", dossier,
               "les lignes des deux arbres cités dans la fiche, au choix")
    return F


P0_F = ("00110011", "01010101", "00001000")
P0_W = {(1, 2): 2, (1, 3): -2, (2, 1): 2, (2, 2): -1, (2, 3): -1, (3, 3): 1}


def fiche_P0(PS, PT, PS_tis, dossier):
    F = Fiche("P0/P5", "Figure existante refaite : partie contrôle (1, 2), partie opérative (3)")
    w0 = tuple(P0_W.get((i, j), 0) for i in (1, 2, 3) for j in (1, 2, 3))
    F.compte("les poids de la fiche réalisent la dynamique", seuil(w0, 3) == P0_F, True)
    ks = [k for k in range(len(PS_tis)) if PS_tis.f[k] == P0_F]
    F.compte("réalisations distinctes dans PSBN_treeinsolver", len({PS_tis.w[k] for k in ks}), 5)
    F.compte("vecteurs de la dynamique dans PSBN_taggedtree",
             sorted(vec_txt(PS.v[k]) for k in range(len(PS)) if PS.f[k] == P0_F), ["⟨1,0,0,0⟩"])
    F.compte("vecteurs de la dynamique dans PTBN_taggedtree",
             sorted(vec_txt(PT.v[k]) for k in range(len(PT)) if PT.f[k] == P0_F), ["⟨1,0,0,0⟩"])
    F.compte("nœuds autonomes", coordonnees_autonomes(P0_F), [(1, 2)])
    choix = min(ks, key=PS_tis.t7)
    F.compte("la réalisation retenue (T7) a les poids de la fiche", PS_tis.w[choix] == w0, True)
    F.extraire(PS_tis, [choix], "3d_P0_PSBN_undercontrol_treeinsolver.csv", dossier,
               "réseau et hypercube depuis la même ligne")
    return F


def fiche_P1(PS, dossier):
    F = Fiche("P1", "Une dynamique décomposable sous nœuds de contrôle")
    best = plus_fin(PS)
    F.compte("dynamiques de ⟨0,1,2,0⟩", len(PS.dyn(V0120)), 139)
    F.compte("dynamiques de ⟨0,2,0,0⟩", len(PS.dyn(V0200)), 658)
    cand = [k for k in range(len(PS)) if PS.v[k] == V0200 and best[PS.f[k]] == 2]
    F.compte("dont ⟨0,2,0,0⟩ est la décomposition la plus fine", len({PS.f[k] for k in cand}))
    cand = [k for k in cand if faces_distinctes(PS.f[k], PS.tree[k])]
    F.compte("et dont les faces sont distinctes", len({PS.f[k] for k in cand}))
    v0120 = [k for k in range(len(PS)) if PS.v[k] == V0120 and best[PS.f[k]] == 3]
    F.compte("dynamiques dont ⟨0,1,2,0⟩ est la plus fine et dont les faces sont distinctes à chaque coupe",
             len({PS.f[k] for k in v0120 if faces_distinctes(PS.f[k], PS.tree[k])}))
    F.note("Candidates restreintes aux dynamiques dont ⟨0,2,0,0⟩ est le vecteur le plus fin (pour ne "
           "pas recouper C5) et dont les faces sont distinctes (sinon le nœud de contrôle ne change "
           "rien au reste, comme en C1). Pas de ligne ⟨0,1,2,0⟩ : en d = 3, aucune dynamique dont "
           "c'est le vecteur le plus fin n'a de faces distinctes à la coupe intérieure.")
    F.extraire(PS, [min(libres(PS, cand), key=PS.t7)], "3d_P1_PSBN_undercontrol_taggedtree.csv", dossier)
    return F


def non_triviales(t):
    return {t.f[k] for k in range(len(t)) if t.v[k][0] != 1}


def fiche_P2(PS, PT, dossier):
    F = Fiche("P2", "Décomposable en TBN mais pas en SBN")
    cand = non_triviales(PT) - non_triviales(PS)
    F.compte("dynamiques non triviales en PTBN, triviales en PSBN", len(cand), 2319)
    best = plus_fin(PT)
    ks = [k for k in range(len(PT)) if PT.f[k] in cand and sum(PT.v[k]) == best[PT.f[k]]]
    F.extraire(PT, [min(libres(PT, ks), key=PT.t7)], "3d_P2_PTBN_undercontrol_taggedtree.csv", dossier,
               "la ligne de sa décomposition la plus fine en TBN")
    return F


def fiche_P3(PI, dossier):
    F = Fiche("P3", "Un PSBNI : arcs entre nœuds distincts inhibiteurs ou absents")
    F.compte("dynamiques distinctes (PSBNI_undercontrol)", len(PI.dyn()), 216)
    ks = [k for k in range(len(PI)) if PI.v[k] == V0200]
    F.compte("dont ⟨0,2,0,0⟩", len({PI.f[k] for k in ks}), 36)
    d = PI.d
    F.compte("lignes avec un arc activateur entre nœuds distincts",
             sum(any(PI.w[k][(i - 1) * d + j - 1] > 0 for i in range(1, d + 1)
                     for j in range(1, d + 1) if i != j) for k in range(len(PI))), 0)
    cand = [k for k in ks if faces_distinctes(PI.f[k], ARBRE_FIXE_0200)
            and any(PI.w[k][(i - 1) * d + j - 1] < 0 for i in range(1, d + 1) for j in range(1, d + 1) if i != j)]
    F.compte("⟨0,2,0,0⟩ à faces distinctes et à arc inhibiteur entre nœuds distincts",
             len({PI.f[k] for k in cand}))
    F.note("Candidates restreintes aux réseaux qui ont au moins un arc inhibiteur entre nœuds "
           "distincts (le minimum de poids seul donne une simple boucle 3→3) et des faces distinctes.")
    F.extraire(PI, [min(libres(PI, cand), key=PI.t7)], "3d_P3_PSBNI_undercontrol.csv", dossier)
    return F


def fiche_P4(PS, PT, dossier):
    F = Fiche("P4", "Supports stables sans décomposition complète")
    cand = {f for f in PT.dyn() - non_triviales(PT) if faces_invariantes(f)}
    F.compte("dynamiques à sous-cube invariant, sans décomposition même en TBN", len(cand), 25697)
    partielles = {f for f in cand if set().union(*faces_invariantes(f)) != set(range(8))}
    F.compte("dont les sous-cubes invariants ne couvrent pas l'hypercube", len(partielles))
    sans_pc = {f for f in partielles if not coordonnees_autonomes(f)}
    F.compte("dont sans nœuds autonomes (pas de partie contrôle, contrairement à P0)", len(sans_pc))
    F.note("La fiche demande des supports invariants qui ne couvrent pas l'hypercube, contrairement "
           "à P0. Lu en sous-cubes, P0 passerait ce filtre (ses sous-cubes invariants laissent 101 "
           "et 110 de côté) : ce qui l'écarte est sa partie contrôle (x1, x2) autonome, d'où le "
           "second filtre.")
    ks = [k for k in range(len(PS)) if PS.v[k][0] == 1 and PS.f[k] in sans_pc]
    choix = min(libres(PS, ks), key=PS.t7)
    faces = [sorted(etiquette(s, 3) for s in Fc) for Fc in faces_invariantes(PS.f[choix])]
    F.note("Sous-cubes invariants de la ligne retenue (étiquettes x3x2x1), à signaler sur la "
           "capture : " + " ; ".join("{" + ", ".join(fc) + "}" for fc in sorted(faces)))
    F.extraire(PS, [choix], "3d_P4_PSBN_undercontrol_taggedtree.csv", dossier)
    return F


OL1_ATTENDU = {2: (36, 0.62), 3: (32768, 0.81), 4: (100000, 0.78), 5: (100000, 0.69)}


def fiche_OL1(PS2, PS, M4, M5, dossier):
    from scipy.stats import spearmanr
    F = Fiche("OL1", "Robustesse et évolutivité : ρ de Spearman par dimension")
    lignes = ["d,source,n,rho,p"]
    for d, t, triv in [(2, PS2, True), (3, PS, True), (4, M4, False), (5, M5, False)]:
        R, E = t.col("Robustness_mean"), t.col("Evolvability")
        ks = [k for k in range(len(t)) if not triv or t.v[k][0] == 1]
        rho, p = spearmanr([R[k] for k in ks], [E[k] for k in ks])
        F.compte(f"d = {d} : dynamiques", len(ks), OL1_ATTENDU[d][0])
        F.compte(f"d = {d} : ρ", round(float(rho), 4), OL1_ATTENDU[d][1], tol=0.005)
        F.compte(f"d = {d} : p", float(p))
        lignes.append(f"{d},{t.nom},{len(ks)},{rho:.6f},{p:.6g}")
    (dossier / "OL1_spearman.csv").write_text("\n".join(lignes) + "\n")
    F.note("En d = 2 et 3, une ligne par dynamique (vecteur trivial) ; en d = 4 et 5, les tirages MCSBN.")
    return F


OL2C_ATTENDU = {0: (29791, 0.0, 0.25, 0.022), 1: (2883, 0.17, 0.33, 0.017),
                2: (93, 0.33, 0.42, 0.010), 3: (1, 0.5, 0.5, 0.0)}
COULEURS_K = {0: "#2a78d6", 1: "#eb6834", 2: "#1baf7a", 3: "#0b0b0b"}


def fiche_OL2c(PS, dossier):
    F = Fiche("OL2c", "Groupes du nuage Robustness_mean / Robustness_std selon les fonctions constantes 0")
    R, S = PS.col("Robustness_mean"), PS.col("Robustness_std")
    groupes = defaultdict(list)
    for k in range(len(PS)):
        if PS.v[k][0] == 1:
            groupes[sum(set(fj) == {"0"} for fj in PS.f[k])].append(k)
    for kk in sorted(groupes):
        g = groupes[kk]
        att = OL2C_ATTENDU.get(kk, (None,) * 4)
        F.compte(f"k = {kk} : dynamiques", len(g), att[0])
        F.compte(f"k = {kk} : Robustness_mean min", round(min(R[i] for i in g), 4), att[1], tol=0.005)
        F.compte(f"k = {kk} : Robustness_mean max", round(max(R[i] for i in g), 4), att[2], tol=0.005)
        F.compte(f"k = {kk} : moyenne de Robustness_std", round(sum(S[i] for i in g) / len(g), 4),
                 att[3], tol=0.0005)
    figure_OL2c(groupes, R, S, dossier)
    F.note("k : nombre de nœuds dont la fonction est la constante 0. Figure : 3d_OL2c_robustesse_k.{pdf,png}.")
    return F


def figure_OL2c(groupes, R, S, dossier):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for kk in sorted(groupes):
        g = groupes[kk]
        n = f"{len(g):,}".replace(",", " ")
        # Les valeurs sont discrètes en d = 3 : les points se superposent sur une
        # centaine de positions, d'où des marqueurs pleins, k croissant au-dessus.
        ax.scatter([R[i] for i in g], [S[i] for i in g], s=16, linewidths=0,
                   color=COULEURS_K.get(kk, "#52514e"), zorder=2 + kk, label=f"k = {kk} ({n})")
        if len(g) == 1:  # un seul point : étiquette directe
            ax.annotate(f"k = {kk}", (R[g[0]], S[g[0]]), xytext=(-6, 6), textcoords="offset points",
                        ha="right", fontsize=9, color="#52514e")
    ax.set_xlabel("Robustness_mean")
    ax.set_ylabel("Robustness_std")
    ax.grid(True, color="#e4e3df", linewidth=0.6, zorder=0)
    for c in ("top", "right"):
        ax.spines[c].set_visible(False)
    ax.legend(title="nœuds de fonction constante 0", frameon=False, fontsize=9,
              title_fontsize=9)
    fig.tight_layout()
    fig.savefig(dossier / "3d_OL2c_robustesse_k.pdf")
    fig.savefig(dossier / "3d_OL2c_robustesse_k.png", dpi=200)
    plt.close(fig)


def fiche_O2_O3(PS2, PS, PT):
    F = Fiche("O2/O3", "Comptes de la pipeline (d = 2) et du garde-fou (d = 3)")
    c2 = Counter(PS2.v)
    for v, att in [((1, 0, 0), 36), ((0, 2, 0), 6), ((0, 1, 2), 6), ((0, 0, 4), 2)]:
        F.compte(f"d = 2, PSBN taggedtree, lignes {vec_txt(v)}", c2[v], att)
    F.compte("d = 2, lignes", len(PS2), 50)
    c3 = Counter(PS.v)
    F.compte("d = 3, PSBN taggedtree, vecteurs", len(c3), 10)
    F.compte("d = 3, PSBN, lignes", len(PS), 34343)
    F.compte("d = 3, PSBN, lignes ⟨1,0,0,0⟩", c3[(1, 0, 0, 0)], 32768)
    F.compte("d = 3, PSBN, lignes des 9 autres vecteurs", len(PS) - c3[(1, 0, 0, 0)], 1575)
    F.compte("d = 3, PSBN, vecteurs à 1000 lignes ou plus (subdivisés)",
             sorted(vec_txt(v) for v, n in c3.items() if n >= 1000), ["⟨1,0,0,0⟩"])
    tranches = Counter(PS.f[k][0][:3] for k in range(len(PS)) if PS.v[k] == (1, 0, 0, 0))
    F.compte("d = 3, PSBN, tranches de ⟨1,0,0,0⟩ (3 premiers bits de f_1)", dict(sorted(tranches.items())),
             {"000": 6144, "001": 10240, "010": 10240, "011": 6144})
    cT = Counter(PT.v)
    F.compte("d = 3, PTBN taggedtree, lignes", len(PT), 39020)
    F.compte("d = 3, PTBN, lignes ⟨0,2,0,0⟩", cT[V0200], 3072)
    F.compte("d = 3, PTBN, lignes ⟨0,1,2,0⟩", cT[V0120], 1344)
    F.compte("d = 3, PTBN, vecteurs à 1000 lignes ou plus (subdivisés)",
             sorted(vec_txt(v) for v, n in cT.items() if n >= 1000),
             sorted(["⟨1,0,0,0⟩", "⟨0,2,0,0⟩", "⟨0,1,2,0⟩"]))
    return F


def fiche_MCSBN(M4, M5):
    F = Fiche("MCSBN", "Part des dynamiques sans décomposition dans un tirage uniforme")
    for t, att, tol in [(M4, 98.9, 0.05), (M5, 99.97, 0.005)]:
        part = 100 * sum(v[0] == 1 for v in t.v) / len(t)
        F.compte(f"d = {t.d} : % de vecteurs triviaux ({len(t)} dynamiques)", round(part, 3), att, tol=tol)
    return F


# ---------------------------------------------------------------------------

def toutes(csvdir, dossier):
    dossier.mkdir(parents=True, exist_ok=True)
    DEJA.clear()

    def T(nom):
        return Table(csvdir / nom)
    PU = T("3d_PSBN_undercontrol_output.csv.gz")
    PT_u = T("3d_PTBN_undercontrol_output.csv.gz")
    PI = T("3d_PSBNI_undercontrol_output.csv.gz")
    PS2 = T("2d_PSBN_undercontrol_taggedtree_output.csv.gz")
    PS = T("3d_PSBN_undercontrol_taggedtree_output.csv.gz")
    PT = T("3d_PTBN_undercontrol_taggedtree_output.csv.gz")
    PS_tis = T("3d_PSBN_undercontrol_treeinsolver_output.csv.gz")
    PT_tis = T("3d_PTBN_undercontrol_treeinsolver_output.csv.gz")
    M4 = T("4d_MCSBN_variety_100000.csv.gz")
    M5 = T("5d_MCSBN_variety_100000.csv.gz")

    fiches = [controle_poids([PU, PT_u, PI, PS2, PS, PT, PS_tis, PT_tis, M4, M5]),
              fiche_C1(PU, dossier), *fiche_C2_C3(PU, PT_u, dossier), fiche_C4(PS, dossier),
              fiche_C5(PS, dossier), *fiche_C6_C7(PU, PT_u, PS, PT, PS_tis, PT_tis, dossier),
              fiche_C8(PT, dossier), fiche_P0(PS, PT, PS_tis, dossier), fiche_P1(PS, dossier),
              fiche_P2(PS, PT, dossier), fiche_P3(PI, dossier), fiche_P4(PS, PT, dossier),
              fiche_OL1(PS2, PS, M4, M5, dossier), fiche_OL2c(PS, dossier),
              fiche_O2_O3(PS2, PS, PT), fiche_MCSBN(M4, M5)]
    par_ligne = defaultdict(list)
    for F in fiches:
        for fi in F.r["fichiers"]:
            for l in fi["lignes"]:
                par_ligne[(fi["source"], l["n"])].append(F)
    for (source, n), Fs in par_ligne.items():
        for F in Fs:
            autres = [G.r["fiche"] for G in Fs if G is not F]
            if autres:
                F.note(f"La ligne n° {n} de {source} est aussi retenue par {', '.join(autres)}.")
    for F in fiches:
        ecarts = [c["quoi"] for c in F.r["comptes"] if c["ok"] is False]
        print(f"  {F.r['fiche']:9s} {'écarts : ' + ' ; '.join(ecarts) if ecarts else 'conforme'}")
    return [F.r for F in fiches]
