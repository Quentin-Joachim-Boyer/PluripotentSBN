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

Comme la pipeline :

- `v_n..v_0` — vecteur de décomposition « sous contrôle » en **ThresholdBN**
  (PTBN, voir ci-dessous) ;
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

### Le vecteur de décomposition `v_*` (ThresholdBN / PTBN)

C'est la propriété la plus délicate. Elle réimplémente la décomposition « sous
contrôle » de l'ASP (`decompose.py`) :

- une face de l'hypercube (contexte = nœuds figés) se scinde sur un **nœud de
  contrôle** vérifiant les **inégalités exactes** de non-activation /
  non-désactivation, testées sur la **matrice de poids échantillonnée** ;
- une face est une **feuille valide dès qu'elle est un ThresholdBN** — ce qui est
  **toujours le cas** : restreindre un nœud à une face = fixer des entrées =
  ajouter un **biais** à une fonction qui reste une fonction seuil. Pas de
  contrainte de réalisabilité sur les feuilles ;
- le vecteur retenu est le plus fin (maximum de feuilles).

C'est la décomposition `PTBN_undercontrol` de l'ASP. La variante **SBN** (`PSBN`),
plus restrictive — elle exige *en plus* que chaque face soit ré-réalisable comme
SBF à seuil 0 bornée — reste disponible dans `decompose.py` (`DecomposerW(n,
"sbn")`) et sert à la validation. Côté ASP, `PSBN_undercontrol_treeinsolver.lp`
est d'ailleurs littéralement `PTBN_undercontrol_treeinsolver.lp` **plus** cette
vérification. Conséquence : pour une même dynamique la décomposition TBN est
**toujours au moins aussi fine** que la SBN (un réseau indécomposable en SBN peut
l'être en TBN — c'est précisément l'intérêt ; ~8 % des réseaux en `d=3`, ~1 % en
`d=4`).

**Nuance importante.** On rapporte la décomposition du **génotype échantillonné**
(la matrice de poids effectivement tirée). La pipeline rapporte, elle, le maximum
sur *toutes* les réalisations d'une dynamique. En pratique :

- la décomposition **SBN** recalculée en `d=3` est **identique au bit près** à la
  pipeline PSBN (vérifié exhaustivement, `test_full_match_d3`) ;
- la décomposition **TBN** émise (`v_*`) est exacte pour le génotype tiré et
  constitue une **borne inférieure** du maximum-phénotype (rarement atteinte par
  défaut), encadrée par la pipeline PTBN (`test_sandwich_dW_tbn`).

## Deux implémentations

- **C (`mcsbn.c`)** — la version de production, **rapide**. Mêmes options, sortie
  CSV numériquement identique (cf. validation croisée). À utiliser par défaut.
- **Python (`mcsbn.py`)** — implémentation de référence, lisible, qui a servi à
  valider la logique contre la pipeline ASP. Plus lente d'un ordre de grandeur.

```bash
make                       # compile ./bin/mcsbn

# 1 000 000 de dynamiques distinctes en dimension 4
./bin/mcsbn -d 4 -n 1000000 -o out/sortie_4d.csv

# sortie gz native : tout suffixe .gz active la compression zlib (aucun outil externe)
./bin/mcsbn -d 5 -n 1000000 -o out/sortie_5d.csv.gz

# enumeration EXHAUSTIVE (petites dimensions) : produit TOUT l'espace
./bin/mcsbn -d 3 --exhaustive -o out/complet_3d.csv

# mesure « genotype » au lieu de « variete », CSV compact sans poids
./bin/mcsbn -d 4 -n 1000000 --measure genotype --no-weights -o out/geno_4d.csv
```

Options : `-d`, `-n`, `-o` (`-` = stdout), `--measure variety|genotype`,
`--seed`, `--max-draws`, `--exhaustive`, `--no-weights`,
`--progress|--no-progress`. Si le fichier passé à
`-o` finit par `.gz`, le binaire C **compresse nativement** via zlib (comme la
version Python) ; `-` (stdout) reste non compressé — y enchaîner un `| gzip` au
besoin. Le binaire C cherche son cache de table dans `$MCSBN_DIR/.cache/` (défaut
`./.cache/`, relatif au répertoire courant — lancer les commandes depuis la racine
`MCSBN/`).

**Progression au runtime.** Le binaire C affiche une ligne de progression réécrite
sur `stderr` (compteur, débit, nouveauté, ETA), **activée automatiquement** quand
`stderr` est un terminal et silencieuse si la sortie est redirigée (logs propres).
Forcer avec `--progress`, désactiver avec `--no-progress`. Comme tout passe par
`stderr`, le CSV (stdout) n'est jamais pollué.

```
[d=5] 742000/1000000  74.2% | 261k dyn/s | nouveauté 99.97% | ETA 1s
```

La version Python a exactement les mêmes options de génération
(`python3 src/python/mcsbn.py ...`), à l'exception de l'affichage de progression,
propre au binaire C.

### Compilation sous Windows (MSYS2 / MinGW-w64)

Le code C se compile **sans modification** avec MinGW-w64. Installer une fois la
chaîne, puis lancer `make` depuis le shell **« MSYS2 MinGW64 »** :

```bash
pacman -S --needed mingw-w64-x86_64-gcc mingw-w64-x86_64-zlib make python  # une seule fois

cd MCSBN
make                       # -> bin/mcsbn.exe (lié statiquement, autonome)
./bin/mcsbn.exe -d 4 -n 1000000 -o out/sortie_4d.csv
./bin/mcsbn.exe -d 5 -n 1000000 -o out/sortie_5d.csv.gz   # gz natif (pas de gzip externe)
make test                  # suite de validation Python
```

Le Makefile détecte Windows (`OS=Windows_NT`) : il ajoute le suffixe `.exe` et
`-static`, ce qui embarque `libgomp`/`libwinpthread`/`libz` dans l'exécutable — il
tourne donc aussi hors du shell MSYS2 (cmd, PowerShell, double-clic). La sortie
`.gz` étant native (zlib), nul besoin d'un `gzip` externe : `-o fichier.gz`
fonctionne dans tous les shells. Si `python3` n'existe pas : `make test PYTHON=python`.

**Pré-requis matériel : BMI2.** `-march=native` active l'instruction `_pdep_u64`
(ligne 385 de `mcsbn.c`), qui exige un CPU x86 récent (Intel Haswell 2013+, AMD
Zen+). Sur un processeur **sans BMI2**, l'exe se compile mais s'arrête à
l'exécution sur une *illegal instruction* : il faudrait alors un repli logiciel
pour `_pdep_u64` (non implémenté). `-march=native` l'utilise automatiquement quand
le matériel le supporte.

Alternative sans rien recompiler côté natif : **WSL** (le binaire ELF y tourne
tel quel, `sudo apt install build-essential`).

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

**Contre la pipeline** (`python3 src/python/test_mcsbn.py`, nécessite les CSV de
référence dans `../JPPipeline/out/`) :

- **décomposition SBN exacte** vs pipeline PSBN en `d=3` (recalculée pour la
  comparaison, 32768 dynamiques) + **statistiques identiques** ;
- **invariants d'encadrement** des décompositions par poids (SBN vs PSBN, TBN vs
  PTBN) en `d=3` et `d=4` (jamais inférieures à ce que le solveur a prouvé) ;
- **invariant TBN ≥ SBN** : le vecteur émis (`v_*`, TBN) est toujours au moins
  aussi fin que la décomposition SBN — vérifié sur échantillon, sans référence ;
- **nouveauté ≈ 100 %** du tirage variety, **séparation** des deux lois de tirage.

**Entre les deux implémentations** : C et Python partagent le même représentant
canonique (colonne lexicographiquement la plus petite), donc leurs sorties sont
**byte-pour-byte identiques** (au format flottant près, équivalent à 10⁻¹⁶). Vérifié
en `d=3` (exhaustif, poids compris) et `d=4` (vecteurs de décomposition).

## Limites et pistes

- Décomposition **phénotype-finest** exacte en `d≥4` : nécessiterait un maximum
  sur les réalisations (essentiellement le CSP que résout l'ASP). On rapporte ici
  la décomposition (TBN) du génotype **canonique** échantillonné (exacte pour ce
  réseau). Approximation peu coûteuse possible : tirer plusieurs réalisations par
  dynamique et garder la plus fine.
- `d=6` : pleinement supporté en C (table construite en ~9 s puis mise en cache,
  génération ~90 000 dyn/s). `GenotypeCount` y dépasse parfois 128 bits et bascule
  alors en flottant. La version Python, elle, n'est pas pratique au-delà de `d=5`.

## Arborescence

Organisation calquée sur `JPPipeline/` (`src/` par langage, `bin/` compilé,
`out/` sorties, `archive/` archives) :

```
MCSBN/
├── Makefile               # make, make test, make clean
├── README.md
├── src/
│   ├── c/
│   │   └── mcsbn.c        # générateur rapide en C (production)
│   └── python/
│       ├── mcsbn.py       # générateur Python (référence lisible, mêmes options)
│       ├── sbf.py         # énumération des SBF + statistiques (cache disque)
│       ├── decompose.py   # inférence du vecteur de décomposition
│       │                  #   (Decomposer : depuis la dynamique ;
│       │                  #    DecomposerW : depuis la matrice de poids, exact)
│       └── test_mcsbn.py  # suite de validation contre la pipeline
├── bin/                   # binaire compilé ./bin/mcsbn (non versionné)
├── out/                   # CSV générés (non versionné)
├── archive/               # sorties archivées
└── .cache/                # tables SBF précalculées, partagées C ↔ Python
```
