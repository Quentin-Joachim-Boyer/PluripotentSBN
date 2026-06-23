# MCSBN — Générateur Monte-Carlo de SBN

Génère un CSV de SBN (réseaux booléens à seuil signés) de dimension `d`,
**compatible avec le format de la pipeline ASP** (mêmes colonnes, donc lisible
directement dans `metagraphe.html`), mais en **tirant des réseaux au hasard** et
en **inférant toutes les propriétés en post-traitement** — sans aucun appel à un
solveur.

Objectif : explorer le plus largement possible la **variété des dynamiques** avec
des ressources raisonnables.

## L'idée centrale

Les colonnes de la matrice de poids d'un SBN sont **indépendantes** : la fonction
de transition `f_j` du nœud `j` ne dépend que de la colonne `j`. Chaque `f_j` est
une *fonction seuil signée* (SBF). Comme n'importe quel n-uplet de SBF est
réalisable, l'espace des dynamiques distinctes est **exactement** `(SBF_n)^n`.

Conséquence : pour représenter fidèlement la variété, il suffit de tirer chaque
colonne **uniformément parmi les SBF distinctes**. La loi résultante est alors
**uniforme sur l'ensemble des dynamiques distinctes** — aucune dynamique n'est
favorisée, contrairement à un tirage uniforme sur les matrices de poids qui
sur-représenterait les dynamiques à grand nombre de réalisations.

| d | #SBF distinctes | #dynamiques distinctes |
|---|----------------:|-----------------------:|
| 3 | 32              | 32³ ≈ 3,3 × 10⁴        |
| 4 | 370             | 370⁴ ≈ 1,9 × 10¹⁰      |
| 5 | 11 292          | 11292⁵ ≈ 1,8 × 10²⁰    |

L'espace étant gigantesque dès `d=4`, **presque chaque tirage est une dynamique
inédite** (nouveauté ≈ 100 %) : l'exploration est quasi optimale.

## Les deux lois de tirage

- `--measure variety` (**défaut**) : chaque colonne uniforme parmi les SBF
  distinctes → uniforme sur les dynamiques distinctes. **Variété maximale.**
- `--measure genotype` : chaque colonne tirée proportionnellement à son nombre de
  matrices de poids (`ColumnSet`) → approche l'uniforme sur les matrices de poids
  (mesure « naturelle » des génotypes). Explore beaucoup moins la variété.

  *Vérifié :* en `d=3`, le `GenotypeCount` moyen est ~13× plus élevé en mode
  genotype (754) qu'en mode variety (59) — le mode genotype concentre bien sur
  les dynamiques communes.

## Propriétés inférées (colonnes du CSV)

Identiques à la pipeline :

- `v_n..v_0` — vecteur de décomposition « sous contrôle » (voir ci-dessous) ;
- `f_1..f_n` — tables de transition (bitstrings de longueur `2^n`) ;
- `w_i,j` — une réalisation **exacte** des poids (`f_j = seuil(colonne j)`) ;
- `CycleLenMSQ` — moyenne des (longueurs de cycle)² sur les attracteurs ;
- `NumAttractors` — nombre d'attracteurs ;
- `GenotypeCount` — nombre **exact** de matrices réalisant la dynamique (produit
  des tailles de `ColumnSet`, grand entier) ;
- `Robustness_std`, `Robustness_mean`, `Evolvability` — à la Wagner (2008),
  calcul exact par colonne.

La colonne `dynamics` de la pipeline (encodage des attracteurs pour les distances
dDA) est volontairement omise.

### Le vecteur de décomposition

C'est la seule propriété délicate. Elle est inférée en réimplémentant la
décomposition « sous contrôle » de l'ASP (`decompose.py`) :

- une face de l'hypercube (contexte = nœuds figés) se scinde sur un **nœud de
  contrôle** vérifiant les **inégalités exactes** de non-activation /
  non-désactivation, testées sur la **matrice de poids échantillonnée** ;
- une face est une **feuille** valide si la fonction restreinte de chaque nœud
  libre est une SBF réalisable (avec le bound de la dimension du sommet, comme
  l'ASP) ;
- le vecteur retenu est le plus fin (maximum de feuilles).

**Nuance importante.** On rapporte la décomposition du **génotype échantillonné**
(la matrice de poids effectivement tirée). La pipeline rapporte, elle, le maximum
sur *toutes* les réalisations d'une dynamique. Les deux coïncident pour la quasi
totalité des dynamiques :

- en `d=3` (espace complet), la distribution des vecteurs produite par MCSBN est
  **identique au bit près** à celle de la pipeline ;
- en `d≥4`, la valeur MCSBN est exacte pour le réseau montré et constitue une
  borne inférieure du maximum-phénotype (rarement atteinte par défaut).

## Deux implémentations

- **C (`mcsbn.c`)** — la version de production, **rapide**. Mêmes options, sortie
  CSV numériquement identique (cf. validation croisée). À utiliser par défaut.
- **Python (`mcsbn.py`)** — implémentation de référence, lisible, qui a servi à
  valider la logique contre la pipeline ASP. Plus lente d'un ordre de grandeur.

```bash
make                       # compile ./mcsbn

# 1 000 000 de dynamiques distinctes en dimension 4
./mcsbn -d 4 -n 1000000 -o sortie_4d.csv

# vers stdout puis compression au fil de l'eau
./mcsbn -d 5 -n 1000000 | gzip > sortie_5d.csv.gz

# enumeration EXHAUSTIVE (petites dimensions) : produit TOUT l'espace
./mcsbn -d 3 --exhaustive -o complet_3d.csv

# mesure « genotype » au lieu de « variete », CSV compact sans poids
./mcsbn -d 4 -n 1000000 --measure genotype --no-weights -o geno_4d.csv
```

Options : `-d`, `-n`, `-o` (`-` = stdout), `--measure variety|genotype`,
`--seed`, `--max-draws`, `--exhaustive`, `--no-weights`. Le binaire C cherche son
cache de table dans `$MCSBN_DIR/.cache/` (défaut `./.cache/`).

La version Python a exactement les mêmes options (`python3 mcsbn.py ...`).

## Performances (C, `-O3 -march=native`)

Génération (un seul cœur — c'est le débit qui compte) :

| d | débit (avec poids) | nouveauté | table SBF (1ère fois) |
|---|-------------------:|----------:|----------------------:|
| 4 | ~380 000 dyn/s     | 100 %     | < 0,1 s               |
| 5 | ~260 000 dyn/s     | 100 %     | ~0,1 s                |
| 6 | ~90 000 dyn/s      | 100 %     | ~9 s (12 cœurs)       |

Soit **20 à 40× la version Python**. En `--no-weights`, `d=4` dépasse 500 000
dyn/s. Mémoire : ~55–130 Mo pour 1 M de dynamiques (dominée par la table de
déduplication).

Le **calcul de la table SBF est parallélisé (OpenMP)** : énumération des colonnes
et statistiques de voisinage réparties par SBF sur tous les cœurs (≈ 4× en `d=6`,
limité par la phase d'indexation des 567 414 SBF distinctes, séquentielle). La
table est ensuite mise en cache binaire dans `.cache/` : recalcul inutile aux
exécutions suivantes. Pour `d≤5` elle est de toute façon quasi instantanée.

La nouveauté de 100 % confirme la conception : l'espace des dynamiques étant
gigantesque, presque chaque tirage est inédit — l'exploration est quasi optimale.

## Validation

Deux niveaux de validation.

**Contre la pipeline** (`python3 test_mcsbn.py`, nécessite les CSV de référence
dans `../JPPipeline/out/`) :

- **décomposition exacte** vs pipeline en `d=3` (32768 dynamiques) ;
- **distribution des vecteurs + toutes les statistiques identiques** en `d=3` ;
- **invariants d'encadrement** de la décomposition par poids en `d=3` et `d=4`
  (la valeur MCSBN n'est jamais inférieure à ce que le solveur a prouvé) ;
- **nouveauté ≈ 100 %** du tirage variety ;
- **séparation** des deux lois de tirage.

**Entre les deux implémentations** : C et Python partagent le même représentant
canonique (colonne lexicographiquement la plus petite), donc leurs sorties sont
**byte-pour-byte identiques** (au format flottant près, équivalent à 10⁻¹⁶). Vérifié
en `d=3` (exhaustif, poids compris) et `d=4` (vecteurs de décomposition).

## Limites et pistes

- Décomposition **phénotype-finest** exacte en `d≥4` : nécessiterait un maximum
  sur les réalisations (essentiellement le CSP que résout l'ASP). On rapporte ici
  la décomposition du génotype **canonique** échantillonné (exacte pour ce réseau,
  identique au finest-phénotype en `d=3`). Approximation peu coûteuse possible :
  tirer plusieurs réalisations par dynamique et garder la plus fine.
- `d=6` : pleinement supporté en C (table construite en ~9 s puis mise en cache,
  génération ~90 000 dyn/s). `GenotypeCount` y dépasse parfois 128 bits et bascule
  alors en flottant. La version Python, elle, n'est pas pratique au-delà de `d=5`.

## Fichiers

- `mcsbn.c` — **générateur rapide en C** (production). `make` pour compiler.
- `mcsbn.py` — générateur Python (référence lisible, mêmes options).
- `sbf.py` — énumération des SBF et de leurs statistiques (cache disque).
- `decompose.py` — inférence du vecteur de décomposition (`Decomposer` : depuis la
  seule dynamique ; `DecomposerW` : depuis la matrice de poids, exact).
- `test_mcsbn.py` — suite de validation contre la pipeline.
- `Makefile` — `make`, `make test`, `make clean`.
