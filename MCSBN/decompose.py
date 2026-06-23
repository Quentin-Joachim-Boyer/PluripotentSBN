"""
decompose.py — Inference du vecteur de decomposition (le plus fin) d'une dynamique.

On reimplemente, en termes de la SEULE dynamique T (sans les poids), la
decomposition "sous controle" definie cote ASP (PSBN_undercontrol_treeinsolver.lp).

Idee. Un sous-cube est une face de l'hypercube {0,1}^n : certains noeuds sont
figes a une valeur (le "contexte"), les autres sont libres. Sur cette face :

  * un noeud libre c est un NOEUD DE CONTROLE s'il est invariant : pour tout
    etat s de la face, T(s)_c = s_c (c ne change jamais). On peut alors scinder
    la face en deux sous-faces (c=0 et c=1), chacune de dimension k-1.

  * la face est une FEUILLE valide de dimension k si la dynamique restreinte de
    chaque noeud libre est une SBF de dimension k realisable (test d'appartenance
    a la table SBF de dimension k). Comme les colonnes sont independantes, ce
    test se factorise noeud par noeud.

Le vecteur de decomposition = nombre de feuilles par dimension dans l'arbre.
Le "plus fin" = celui qui maximise le nombre total de feuilles (exactement le
critere `decompSum` retenu cote visualisation pour dedupliquer les orbites).

Tout depend uniquement de la face (partition figee/libre + valeurs figees), pas
de l'ordre des scissions : on memoise donc sur les 3^n faces possibles.
"""

from sbf import get_key_set_bounded, wbound


def _states_in_face(fixed_nodes, fixed_vals, free, n):
    """Liste des etats de la face, indexes par la config des noeuds libres.

    free : liste triee des indices de noeuds libres.
    L'etat de la config c a le bit free[t] = bit t de c, et les bits figes =
    fixed_vals.
    """
    k = len(free)
    base = fixed_vals  # bits figes deja places
    states = []
    for c in range(1 << k):
        s = base
        cc = c
        t = 0
        while cc:
            if cc & 1:
                s |= (1 << free[t])
            cc >>= 1
            t += 1
        states.append(s)
    return states


def _restricted_tt(fnode, states):
    """Table de verite de la fonction restreinte du noeud `fnode` sur la face."""
    tt = 0
    for c, s in enumerate(states):
        if (fnode >> s) & 1:
            tt |= (1 << c)
    return tt


def _finer(a, b, n):
    """Vrai si la decomposition a est strictement plus fine que b.

    Critere principal : plus de feuilles au total (== max decompSum, le meme
    critere que la deduplication des orbites cote metagraphe). Departage
    secondaire deterministe : davantage de feuilles de basse dimension.
    """
    ta = sum(a.values())
    tb = sum(b.values())
    if ta != tb:
        return ta > tb
    for k in range(n + 1):
        if a.get(k, 0) != b.get(k, 0):
            return a.get(k, 0) > b.get(k, 0)
    return False


class Decomposer:
    """Inference memoisee, reutilisable sur plusieurs dynamiques de meme dim."""

    def __init__(self, n):
        self.n = n
        # Tous les sous-reseaux sont realises avec le bound du sommet wb(n).
        top_bound = wbound(n)
        self.key_sets = {k: get_key_set_bounded(k, top_bound)
                         for k in range(0, n + 1)}

    def finest(self, f):
        """Vecteur de decomposition le plus fin de la dynamique f.

        f : liste de n entiers ; f[i] est la table de verite (bit s = T(s)_i)
        du noeud i. Retourne un dict {dimension: nombre de feuilles}.
        """
        self.f = f
        self.memo = {}
        res = self._decompose(0, 0)        # face vide : tous les noeuds libres
        # La face de depart est toujours valide (c'est le SBN complet), donc res
        # n'est jamais None.
        return res

    def _decompose(self, fixed_nodes, fixed_vals):
        memo = self.memo
        key = (fixed_nodes, fixed_vals)
        if key in memo:
            return memo[key]

        n = self.n
        f = self.f
        free = [i for i in range(n) if not (fixed_nodes >> i) & 1]
        k = len(free)

        if k == 0:
            res = {0: 1}
            memo[key] = res
            return res

        states = _states_in_face(fixed_nodes, fixed_vals, free, n)

        # PRECONDITION : la face est un sous-SBN valide ssi la fonction restreinte
        # de CHAQUE noeud libre est une SBF realisable de dimension k. C'est
        # essentiel : les deux moitiees d'une scission partagent la meme colonne
        # de poids (le noeud de controle ajoute un offset constant), donc une face
        # qui n'est pas elle-meme une SBF (ex. un XOR) ne peut pas figurer dans
        # l'arbre, meme si on pouvait la scinder en feuilles triviales.
        keyset = self.key_sets[k]
        for n_idx in free:
            if _restricted_tt(f[n_idx], states) not in keyset:
                memo[key] = None
                return None

        # La face est valide : au minimum une feuille de dimension k.
        best = {k: 1}

        # Noeuds de controle = noeuds libres invariants sur la face.
        for c in free:
            inv = True
            for s in states:
                if ((f[c] >> s) & 1) != ((s >> c) & 1):
                    inv = False
                    break
            if not inv:
                continue
            d0 = self._decompose(fixed_nodes | (1 << c), fixed_vals)
            if d0 is None:
                continue
            d1 = self._decompose(fixed_nodes | (1 << c), fixed_vals | (1 << c))
            if d1 is None:
                continue
            combined = dict(d0)
            for dim, cnt in d1.items():
                combined[dim] = combined.get(dim, 0) + cnt
            if _finer(combined, best, n):
                best = combined

        memo[key] = best
        return best


def vector_from_counts(counts, n):
    """Convertit {dim: count} en liste [v_n, v_{n-1}, ..., v_0] (ordre du CSV)."""
    return [counts.get(n - i, 0) for i in range(n + 1)]


class DecomposerW:
    """Decomposition "sous controle" d'un reseau CONCRET de matrice de poids W.

    A la difference de Decomposer (qui ne voit que la dynamique T et surestime
    donc la decomposabilite), on dispose ici de la matrice de poids et on teste
    les noeuds de controle avec les INEGALITES EXACTES de l'ASP
    (non-activation / non-desactivation), une seule colonne par noeud : le
    couplage global entre tous les contextes est donc respecte, exactement comme
    le solveur.

    W[i][j] = poids de l'arc i -> j (donc la colonne j, W[:,j], determine f_j).
    Le resultat est le vecteur de decomposition le plus fin REALISE PAR CE W.
    Le vecteur de la pipeline est le maximum de cette quantite sur toutes les
    matrices realisant une dynamique donnee ; ici on rapporte celui du genotype
    effectivement echantillonne.
    """

    def __init__(self, n):
        self.n = n
        top_bound = wbound(n)
        self.key_sets = {k: get_key_set_bounded(k, top_bound)
                         for k in range(0, n + 1)}

    def finest(self, W):
        self.W = W
        # Dynamique f[c] (table de verite, bit s = f_c(s)) derivee de W.
        n = self.n
        f = [0] * n
        for s in range(1 << n):
            for c in range(n):
                ssum = 0
                for i in range(n):
                    if (s >> i) & 1:
                        ssum += W[i][c]
                if ssum > 0:
                    f[c] |= (1 << s)
        self.f = f
        self.memo = {}
        return self._decompose(0, 0)

    def _decompose(self, fixed_nodes, fixed_vals):
        memo = self.memo
        key = (fixed_nodes, fixed_vals)
        if key in memo:
            return memo[key]

        n = self.n
        f = self.f
        W = self.W
        free = [i for i in range(n) if not (fixed_nodes >> i) & 1]
        k = len(free)

        if k == 0:
            res = {0: 1}
            memo[key] = res
            return res

        states = _states_in_face(fixed_nodes, fixed_vals, free, n)

        # Realisabilite de la face comme sous-SBN (fonctions restreintes = SBF).
        keyset = self.key_sets[k]
        for nidx in free:
            if _restricted_tt(f[nidx], states) not in keyset:
                memo[key] = None
                return None

        best = {k: 1}

        # Noeuds actifs du contexte (figes a 1) = offset_node.
        active = [i for i in range(n) if (fixed_nodes >> i) & 1 and (fixed_vals >> i) & 1]

        for c in free:
            # Inegalites de noeud de controle exactes sur W.
            offset = sum(W[on][c] for on in active)
            sum_pos = sum(max(0, W[i][c]) for i in free if i != c)
            sum_neg = sum(min(0, W[i][c]) for i in free if i != c)
            if offset + sum_pos > 0:           # peut etre active de l'exterieur
                continue
            if offset + sum_neg + W[c][c] <= 0:  # peut etre desactive de l'exterieur
                continue
            d0 = self._decompose(fixed_nodes | (1 << c), fixed_vals)
            if d0 is None:
                continue
            d1 = self._decompose(fixed_nodes | (1 << c), fixed_vals | (1 << c))
            if d1 is None:
                continue
            combined = dict(d0)
            for dim, cnt in d1.items():
                combined[dim] = combined.get(dim, 0) + cnt
            if _finer(combined, best, n):
                best = combined

        memo[key] = best
        return best
