# Plan des figures du rapport

Document de travail (non compilé) : chaque placeholder du corps de `rapport_stage.tex` devient une fiche, que Quentin tranche (garder, modifier, supprimer). Les générations décidées ici alimenteront le script de la passe unifiée.

Les nombres de candidats viennent des CSV d = 3 régénérés le 2026-10-03 (conversation 12941938) avec JPP et `clingcon` 5.2.1 de `.conda/` ; les poids de `treeinsolver` sont ceux du correctif `sigma` réappliqué ce jour-là.

## Décisions transverses

- **T1. Ordre des lignes.** *Décidé : tri dans le script.* Les pages HTML ne trient pas les lignes : `sbn_viz` les affiche dans l'ordre du fichier, et ne trie que la liste des fichiers chargés. Or JPP écrit les lignes dans un ordre qui change d'une exécution à l'autre. Le script de la passe triera donc chaque CSV (par vecteur, arbre puis dynamique), pour qu'une capture désigne « la solution n° k » de façon reproductible.
- **T2. Liens vers les fichiers.** *Décidé (Quentin, 2026-10-03) :* les « [Lien vers un fichier utilisable] » deviennent la commande qui génère le fichier. Elle est donnée dans chaque fiche, `<sortie>` désignant le dossier de sortie.
- **T3. Fichiers de Laurent.** Les pages HTML ne gèrent pas les `f_*` écrits en entier : sur les 189 lignes du fichier de Laurent, `sbn-core.js` (exécuté avec `gjs`) calcule une dynamique différente de celle des poids, sur toutes les lignes. Seul le panneau des fonctions décode l'entier. *Sans objet si C1 se fait sur `PSBN_undercontrol` (voir C1).*
- **T4. Arbre des sorties `treeinsolver`.** *Décidé : capturer la même dynamique depuis le CSV `taggedtree`, qui porte l'arbre.* C'est toujours possible : vecteur par vecteur, `taggedtree` contient toutes les dynamiques de `treeinsolver`.
- **T5. Doublons de `treeinsolver`.** *Décidé :* cocher « dynamiques uniques » dans `sbn_viz`.

## Section Correction

### C1. Programme de Laurent : les dynamiques à faces identiques qu'il écarte (l. 457)
- Montre : une dynamique que le programme de Laurent écarte parce que ses deux faces portent la même sous-dynamique, alors qu'elle figure dans l'énumération de `PSBN_undercontrol`, dont les 189 solutions de Laurent sont une restriction (Quentin, 2026-10-03).
- Données vérifiées : les 189 dynamiques de Laurent sont exactement celles de `PSBN_distinct_faces_HS.lp`, et toutes figurent parmi les 225 de `PSBN_undercontrol` pour ⟨0,2,0,0⟩ en d = 3. Les **36** autres sont exactement celles dont les faces x₃ = 0 et x₃ = 1 portent la même sous-dynamique ; aucune des 189 n'est dans ce cas.
- Commande : `java -cp JPPipeline/bin:JPPipeline/lib/jpp.jar PSBN.Main 3 JPPipeline/src/asp/PSBN_undercontrol.lp JPPipeline/src/asp 0 <sortie> 1`
- Vue : `sbn_viz`, hypercube colorié par la décomposition, où les deux faces identiques se voient.

### C2. `PTBN_undercontrol` : un réseau non PSBN (l. 465)
- Montre : un réseau pluripotent dont un sous-réseau n'est pas un SBN.
- Données : JPP, `PTBN_undercontrol.lp`, d = 3, exhaustif. Le vecteur ⟨0,2,0,0⟩ a 1024 dynamiques, dont **799** absentes de `PSBN_undercontrol`.
- Commande : `java -cp JPPipeline/bin:JPPipeline/lib/jpp.jar PSBN.Main 3 JPPipeline/src/asp/PTBN_undercontrol.lp JPPipeline/src/asp 0 <sortie> 1`
- Vue : `sbn_viz`, réseau, décomposition et hypercube.
- *Décidé (Quentin, 2026-10-04) :* parmi les 799, le réseau qui a le moins de poids non nuls, pour une figure lisible.

### C3. `PSBN_undercontrol` (l. 471)
- Montre : un PSBN du même vecteur.
- Données : JPP, `PSBN_undercontrol.lp`, d = 3, exhaustif : **225** dynamiques pour ⟨0,2,0,0⟩.
- Commande : celle de C1 (même fichier).
- Vue : comme C2, idéalement un réseau proche de celui de C2 pour la comparaison.

### C4. Table « échelles de décomposition » (l. 480)
- Montre : pourquoi la question des décompositions plus fines « n'est pas si importante ».
- Proposition (données déjà calculées, PSBN `taggedtree`, d = 3) : pour chaque vecteur, le nombre de dynamiques et celles qui admettent aussi un vecteur plus fin.

  | Vecteur | Dynamiques | Plus finement décomposables |
  |---|---:|---:|
  | ⟨1,0,0,0⟩ | 32 768 | 658 |
  | ⟨0,2,0,0⟩ | 658 | 139 |
  | ⟨0,1,2,0⟩ | 139 | 73 |
  | ⟨0,1,1,2⟩ | 70 | 34 |
  | ⟨0,1,0,4⟩ | 31 | 10 |
  | ⟨0,0,4,0⟩ | 16 | 13 |
  | ⟨0,0,3,2⟩ | 13 | 10 |
  | ⟨0,0,2,4⟩ | 10 | 4 |
  | ⟨0,0,1,6⟩ | 4 | 1 |
  | ⟨0,0,0,8⟩ | 1 | 0 |
- *Reporté (Quentin, 2026-10-03) :* la table n'est pertinente qu'étendue au moins à d = 4 et d = 5, ce qui demande une méthode d'estimation. On y reviendra après la rédaction ; en attendant, seule la version d = 3 est générable. Notes pour plus tard :
  - L'énumération exhaustive n'est pas raisonnable dès d = 4. Le seul CSV `PTBN_undercontrol_taggedtree` en d = 4, du 1er juillet, est partiel (au plus 4 998 ou 9 996 lignes par vecteur), et la version PSBN en d = 4 est vide (exécution interrompue).
  - En d = 4 et d = 5, les proportions devront donc être estimées sur un échantillon. Or une énumération partielle de JPP n'est pas un échantillon uniforme (c'est l'ordre de `clingcon`), et MCSBN, qui tire uniformément les dynamiques, ne donne qu'un vecteur par dynamique (le plus fin pour le génotype tiré), pas la liste des vecteurs qu'elle admet.
  - Il faut donc choisir un estimateur, par exemple : tirer des dynamiques avec MCSBN, puis tester chacune avec `taggedtree`, en lui ajoutant des contraintes qui fixent la dynamique (le programme n'a pas de constantes pour cela), pour savoir quels vecteurs elle admet.
- Commande (d = 3) : `java -cp JPPipeline/bin:JPPipeline/lib/jpp.jar PSBN.Main 3 JPPipeline/src/asp/PSBN_undercontrol_taggedtree.lp JPPipeline/src/asp 0 <sortie> 1`

### C5. Un PSBN « trop décomposable » sur ⟨0,2,0,0⟩ (l. 482)
- Montre : une dynamique énumérée avec ⟨0,2,0,0⟩ alors qu'elle admet une décomposition plus fine.
- Données : CSV PSBN `taggedtree` d = 3 : **139** candidates. Le même fichier contient la même dynamique avec son arbre plus fin.
- Vue : deux captures `sbn_viz` de la même dynamique, avec l'arbre ⟨0,2,0,0⟩ puis avec l'arbre le plus fin.
- Commande : celle de C4 (d = 3).

### C6. `PTBN_undercontrol_treeinsolver` : autre orientation, TBN seulement (l. 488)
- Montre : un réseau que l'arbre fixé ne trouve pas (orientation différente) et qui n'est décomposable qu'en TBN.
- Données : **1538** candidates en ⟨0,2,0,0⟩ (dans `PTBN_treeinsolver`, absentes de `PSBN_treeinsolver` et de `PTBN_undercontrol`).
- Commande : `java -cp JPPipeline/bin:JPPipeline/lib/jpp.jar PSBN.Main 3 JPPipeline/src/asp/PTBN_undercontrol_treeinsolver.lp JPPipeline/src/asp 0 <sortie> 1`, puis la même dynamique dans le CSV de `PTBN_undercontrol_taggedtree` (T4).
- Vue : `sbn_viz`, depuis le CSV `taggedtree` (T4).

### C7. `PSBN_undercontrol_treeinsolver` : décomposable en SBN (l. 494)
- Montre : un PSBN que seule une autre orientation de l'arbre révèle.
- Données : **433** candidates en ⟨0,2,0,0⟩ (dans `PSBN_treeinsolver`, absentes de `PSBN_undercontrol`).
- Commande : comme C6, avec `PSBN_undercontrol_treeinsolver.lp` puis `PSBN_undercontrol_taggedtree.lp` (T4).
- Vue : comme C6.

### C8. `PTBN_undercontrol_taggedtree` sur ⟨0,0,2,4⟩ (l. 500, placeholder inachevé : « montrant ]»)
- *Décidé (Quentin, 2026-10-03) :* un arbre dont les deux moitiés sont coupées selon des nœuds de contrôle différents, ce que seul l'étiquetage permet. Par exemple `2[1[*,3[*,*]],3[*,1[*,*]]]` (2 dynamiques) ou `3[1[*,2[*,*]],2[1[*,*],*]]` (2 dynamiques).
- Commande : `java -cp JPPipeline/bin:JPPipeline/lib/jpp.jar PSBN.Main 3 JPPipeline/src/asp/PTBN_undercontrol_taggedtree.lp JPPipeline/src/asp 0 <sortie> 1`
- Vue : `sbn_viz`, décomposition et hypercube.

### Placeholders de Correction hors génération
- l. 439, 443, 445, 447, 451 : liens et références (programmes de Laurent dans le git, Potassco, clingcon, ApproxASP, papier de Laurent).
- l. 475 : « [préciser] » sur les hyper-faces distinctes (texte).
- l. 504 : « [explication du fonctionnement précis du code en annexe ?] » : l'annexe A.3 donne maintenant l'usage ; le fonctionnement relèverait du corps.
- Remarque sur la figure existante `fig:structure-pluripotente-3d` : voir la fiche P0 de la section suivante.

## Section « Quel paysage des réseaux explore-t-on ? »

### P0. Figure existante `fig:structure-pluripotente-3d` et `fig:dynamique-pluripotente-3d` (l. 411-428)
Vérifié le 2026-10-03 :
- **Origine.** Les deux images viennent de la ligne 6 374 de `JPPipeline/out/3d_PSBN_undercontrol_treeinsolver_output.csv` (22 juin), retrouvée par ses poids.
- **La structure ne réalise pas la dynamique affichée.** Les poids de l'image du réseau donnent une autre dynamique que l'hypercube. On retrouve l'hypercube en permutant les nœuds 2 et 3 : c'est le bug des poids de `treeinsolver`, corrigé depuis.
- **La dynamique n'est pas pluripotente.** Sa ligne porte le vecteur trivial ⟨1,0,0,0⟩, et `taggedtree` ne lui en trouve pas d'autre, ni en PSBN ni en PTBN. Elle a seulement des faces invariantes partielles : la face x₃ = 0 et les arêtes {000, 100} et {011, 111}, sans que le reste de l'hypercube se décompose.
- **Conséquence.** Les légendes (« structure pluripotente sous réseau de contrôle […] les nœuds 1 et 3 sont de contrôle », « supports disjoints […] ») ne correspondent pas à ce réseau.

- **Lecture de Quentin (2026-10-03)** : la dynamique est pluripotente d'une autre manière, ses sous-dynamiques étant décrites par plusieurs coordonnées et non par un seul bit de contrôle. Vérifié :
  - dans l'étiquetage de l'hypercube, les coordonnées (x₁, x₂) évoluent seules, comme un réseau à deux nœuds qui échange leurs valeurs (00 et 11 fixes, 01 ↔ 10) ;
  - l'hypercube se partage en trois supports invariants, {000, 100}, {011, 111} et {001, 010, 101, 110}, ce dernier n'étant pas un sous-cube ;
  - c'est ce qu'aucun arbre à un seul bit de contrôle ne capte, d'où le vecteur trivial.

*Décidé :* garder cette dynamique et refaire la figure avec une structure exacte. Les CSV régénérés en contiennent cinq réalisations ; la plus simple a six poids non nuls (1→2 : +2, 1→3 : −2, 2→1 : +2, 2→2 : −1, 2→3 : −1, 3→3 : +1). Les deux images doivent venir de la même ligne.
- La légende est à adapter : avec la structure qui réalise l'hypercube affiché, les nœuds de contrôle sont 1 et 2 (partie contrôle) et le nœud 3 est contrôlé (partie opérative). Les « nœuds 1 et 3 » de la légende actuelle valaient pour la structure non permutée.
- C'est exactement la structure à deux nœuds PC et un nœud PO de la fiche P5 : une seule figure peut servir aux deux placeholders. *Confirmé (Quentin, 2026-10-04).*
- Commande : celle de P1 (la dynamique y figure sous le vecteur ⟨1,0,0,0⟩), ou JPP avec `PSBN_undercontrol_treeinsolver.lp` corrigé.

### P1. Une dynamique décomposable sous nœud de contrôle (l. 388)
- Montre : une dynamique décomposable selon un vecteur complet (nœuds de contrôle).
- Données : PSBN `taggedtree`, d = 3, exhaustif ; par exemple 658 candidates en ⟨0,2,0,0⟩ ou 139 en ⟨0,1,2,0⟩ (deux niveaux de coupe).
- Commande : `java -cp JPPipeline/bin:JPPipeline/lib/jpp.jar PSBN.Main 3 JPPipeline/src/asp/PSBN_undercontrol_taggedtree.lp JPPipeline/src/asp 0 <sortie> 1`
- Vue : `sbn_viz`, réseau et hypercube colorié par la décomposition. Elle peut remplacer la figure existante (P0).

### P2. Décomposable en TBN mais pas en SBN (l. 394)
- Montre : une dynamique qui admet une décomposition quand on accepte des sous-réseaux quelconques, mais aucune quand on les veut signés.
- Données : en d = 3, **2 319** dynamiques ont un vecteur non trivial dans PTBN `taggedtree` et seulement le vecteur trivial dans PSBN `taggedtree`.
- Commande : comme P1 avec `PTBN_undercontrol_taggedtree.lp` (et P1 pour vérifier l'absence en PSBN).
- Vue : `sbn_viz` depuis le CSV PTBN.

### P3. Un PSBNI (l. 400)
- Montre : un PSBN dont les arcs entre nœuds distincts sont inhibiteurs ou absents.
- Données : seule la famille `undercontrol`, à arbre fixé, existe en version `I`. `PSBNI_undercontrol` donne 216 dynamiques en d = 3, dont 36 en ⟨0,2,0,0⟩.
- Commande : `java -cp JPPipeline/bin:JPPipeline/lib/jpp.jar PSBN.Main 3 JPPipeline/src/asp/PSBNI_undercontrol.lp JPPipeline/src/asp 0 <sortie> 1`
- Vue : `sbn_viz`, réseau (arcs inhibiteurs) et hypercube.

### P4. Supports stables et vecteur de décomposition partiel (l. 404)
- Montre : des faces invariantes qui ne forment pas une décomposition complète (piste non explorée).
- Données : aucun programme n'énumère les décompositions partielles. Les exemples se prennent parmi les dynamiques sans décomposition : en d = 3, **25 697** ont un sous-cube invariant sans aucune décomposition, même en TBN. Il faudra en choisir une dont les supports invariants ne couvrent pas tout l'hypercube, contrairement à la dynamique de P0, qui relève d'une autre forme de pluripotence.
- Commande : comme P1 (lignes de vecteur ⟨1,0,0,0⟩).
- Vue : `sbn_viz` ne colorie que les décompositions complètes ; *décidé (Quentin, 2026-10-03) :* les faces invariantes partielles seront signalées à la main sur la capture.

### P5. Structure à 2 nœuds PC et 1 nœud PO, et sa dynamique (l. 408)
- PC et PO : partie contrôle et partie opérative, d'après le paradigme d'architecture des processeurs (Quentin, 2026-10-03). PC désigne le réseau de contrôle, PO le réseau contrôlé.
- *Décidé (Quentin, 2026-10-04) :* la figure refaite de P0, dont les nœuds 1 et 2 forment la partie contrôle et le nœud 3 la partie opérative.

### Placeholders hors génération
- l. 386, 392, 398 : formalisations (rapport de Danwen ; contraintes d'existence des réseaux simulés ; restriction du domaine des poids).

## Section « Métagraphes dynamiques et structurels, règles de mutation »

### M1. Métagraphe du rapport d'Ai-Ling (« [figure métagraphe issue du rapport d'Ailing] »)
- La figure est déjà dans le rapport (`figures/robustesse_eps1_delta0.png`, `fig:métagraphe-Ailing`), juste sous le placeholder, qui semble donc obsolète. Il reste à citer sa source dans la légende (`\cite{bonnet2023}`). Hors génération.

### M2. Métagraphe issu de `metagraphe.html` (« [Figure métagraphe issu du html] »)
- Montre : le métagraphe structurel, un nœud par dynamique, deux dynamiques étant reliées quand une mutation d'un poids fait passer de l'une à l'autre.
- Existant : `figures/{2d,3d,4d}_PTBN_undercontrol_taggedtree_metagraphe.png` (1er et 2 juillet), coloriées par la décomposition, sans arêtes. Les captures en d = 2 et d = 3 viennent d'énumérations exhaustives. Celle en d = 4 vient du CSV partiel du 1er juillet, qui est moins représentatif : une énumération partielle laisse un métagraphe clairsemé et biaisé.
- Proposition pour la passe :
  - d = 3 exhaustif, avec `PTBN_undercontrol_taggedtree` comme les captures existantes, ou `PSBN` ;
  - pour d = 4, le paysage hybride de MCSBN (`core_then_walk.py`), conçu pour que le métagraphe ait des arêtes, plutôt qu'une énumération partielle de JPP.
- Commandes :
  - d = 3 : `java -cp JPPipeline/bin:JPPipeline/lib/jpp.jar PSBN.Main 3 JPPipeline/src/asp/PTBN_undercontrol_taggedtree.lp JPPipeline/src/asp 0 <sortie> 1`, puis `python3 MCSBN/src/python/add_metagraph_layout.py <csv>` ;
  - d = 4 : `python3 src/python/core_then_walk.py -d 4 -M <m> -n <n> -o <csv>` depuis `MCSBN/`, puis la même commande de placement.
- Vue : `metagraphe.html`, couleur par décomposition (comme l'existant) ou par une statistique.
- Point de reproductibilité : DRGraph tire au hasard (GSL). Le placement ne sera identique d'une passe à l'autre que si sa graine est fixe. *À vérifier lors de la passe.*
- *Décidé (Quentin, 2026-10-04) :* d = 3 seulement pour l'instant ; le paysage hybride en d = 4 reste une option pour plus tard. Par défaut, comme les captures existantes : `PTBN_undercontrol_taggedtree`, coloration par la décomposition, sauf avis contraire.

### M3. Équation définissant une arête du métagraphe
- Hors génération. Définition tirée du code pour la rédaction : deux dynamiques sont reliées quand elles ne diffèrent que par la fonction d'un seul nœud j, et que l'on passe de l'une à l'autre en changeant un seul poids de la colonne j (dans les bornes). Sources : `add_metagraph_layout.py` (docstring), `sbf.get_neighbor_map`, `metagraphe.html` (`sbfNeighbors`).

### M4. « [Cf partie utilisation de ma Pipeline pour modifier ces règles de mutations] »
- Hors génération. La règle de mutation est codée à quatre endroits, qu'il faudrait modifier ensemble :
  - `SBFStatTable.java`, pour la robustesse et l'évolutivité dans JPP ;
  - `mcsbn.c` et `sbf.py`, pour MCSBN, `core_then_walk.py` et `add_metagraph_layout.py` ;
  - `metagraphe.html`, pour les arêtes affichées.
- *Décidé (Quentin, 2026-10-04) :* à dire dans le corps du rapport (section Métagraphes), pas dans l'annexe.

### Ressource existante non demandée
- Les essais de métagraphes à distance DA (paragraphe sur l'approche abandonnée) ont laissé des images dans `JPPipeline/out/metagraphe/` (`2d_da_0.png` à `2d_da_4.png`), si une illustration de cette piste était souhaitée.


## Section Optimisation

### O1. Chiffres sur la base ASP (l. 508)
- Le placeholder avance deux affirmations : les contraintes sur les poids sont plus efficaces que les contraintes sur la structure, et la parallélisation directe en ASP est « généralement peu efficace ».
- **Poids contre structure.** *Décidé (Quentin, 2026-10-04) :* une comparaison de temps avec le programme de Laurent, qui contraint la structure, sur le seul cas où son énumération est exactement retrouvée : d = 3, ⟨0,2,0,0⟩, où `PSBN_distinct_faces_HS.lp` donne les mêmes 189 dynamiques.

  | Programme | Dynamiques | Temps |
  |---|---:|---:|
  | Laurent (15-07-2024, sa machine) | 189 | 2,52 s |
  | `PSBN_distinct_faces_HS.lp` (2026-10-04, machine locale) | 189 | 0,015 s |

  Le gain est donc d'environ ×170. Les deux chiffres viennent de machines différentes, mais l'écart dépasse de loin ce que la machine peut expliquer. Pour mémoire, sur la machine locale, `PSBN_undercontrol` donne ses 225 dynamiques en 0,011 s, et `taggedtree`, qui cherche aussi l'arbre, ses 675 lignes en 0,6 s.
  - Source du temps de Laurent : sortie `clingcon` 5.2.1 transmise par Quentin le 2026-10-04, dont une copie est dans `~/Bureau/asp/Pluripot-decomp.189-sol.d=3._0, 2, 0, 0_ .lp`, hors du dépôt (variante `dif_faces(c(V_c, Cont_path))`).
  - Le même dossier contient un résultat de Laurent en d = 4 (`Pluripot-decomp.18-sol.d=4._0, 0, 3, 2, 0_.lp` : 18 solutions en 88 à 101 s, presque tout en grounding). `distinct_faces` ne le reproduit pas, puisqu'il donne 193 solutions (test du 2026-10-04), si bien que ce cas ne sert pas à la comparaison.
  - Précaution (Quentin) : `distinct_faces` ne reproduit pas Laurent sur les autres vecteurs, ce que confirme ⟨0,1,2,0⟩, avec 11 dynamiques contre 6 chez Laurent (fichier `SBN_pluripotent_Laurent/Pluripot-decomp.6-sol…`, autre variante `dif_faces(Cont_path, Cont_pathp)`, 0,275 s). La comparaison se limite donc à ⟨0,2,0,0⟩.
  - Dans la passe, on rechronomètre `distinct_faces` ; le programme de Laurent ne l'est que si l'on retrouve la variante du 15 juillet dans les fichiers locaux (le `Test-decomp` local vise ⟨0,1,2,0⟩ avec l'autre variante). Sinon, on cite son temps en précisant qu'il vient de sa machine.
  - Commande : `PSBN_distinct_faces_HS.lp` n'existe que dans `SBN_pluripotent/`, et il inclut le `PSBN_undercontrol.lp` de ce dossier, qui diverge de la copie de référence. La passe copie donc `PSBN_distinct_faces_HS.lp` dans un dossier temporaire, avec `{PSBN,PTBN}_undercontrol.lp` et `setup_btree_3d.lp` de `JPPipeline/src/asp/`, puis lance `clingcon 0 --project -c d=3 -c v3=0 -c v2=2 -c v1=0 -c v0=0 setup_btree_3d.lp PSBN_distinct_faces_HS.lp`. Avec les programmes de référence, on obtient aussi 189 dynamiques sur ⟨0,2,0,0⟩ (en 0,013 s) et 11 sur ⟨0,1,2,0⟩ (test du 2026-10-04).
- **Exemple d'optimisation : la formulation de `taggedtree`.** *Décidé (Quentin, 2026-10-04) :* on le présente comme exemple d'optimisation. Il y a eu trois versions successives de `PSBN_undercontrol_taggedtree.lp`, remesurées le 2026-10-04 sur la machine locale (`clingcon` 5.2.1 de `.conda/`) :

  | Version | ⟨0,2,0,0⟩, d = 3 (675 lignes) | Énumération globale d = 3, lignes en 60 s |
  |---|---:|---:|
  | `88ccf0e` (2 juillet) : sommes de théorie dans le corps des règles | aucune solution, mémoire saturée (> 3,6 Go en 18 s) | aucune solution, idem |
  | intermédiaire (3 juillet, non commitée) : réification par `pos_side`, copies auxiliaires des poids | 2,9 s | 2 876 |
  | `7dc415c` (3 juillet) : appartenance à la chaîne calculée au grounding (`chain_member`), sans copies | 0,54 s | 28 686 |

  La base PTBN a été réécrite de la même façon. Son énumération globale complète en d = 3 (39 020 lignes) passe de 17,9 s (`88ccf0e`) à 0,82 s (`7dc415c`), avec les mêmes solutions.
  - Les mesures de juillet (conversation e37f3aaa, sur une autre machine) concordent : 2,84 s puis 0,58 s sur ⟨0,2,0,0⟩, et 19,9 s puis 1,0 s pour PTBN. La version `88ccf0e` n'y trouvait déjà aucune solution, ni en 32 s en d = 2, ni en 62 s en d = 3.
  - La version intermédiaire n'est pas dans git. Elle a été récupérée du transcript dans `Redaction/sources/PSBN_undercontrol_taggedtree_intermediaire_2026-07-03.lp` (en-tête : provenance et mode d'emploi). Elle s'utilise avec la base PTBN de `88ccf0e`, placée dans le même dossier.
  - Commandes pour la passe : extraire `git show 88ccf0e:SBN_pluripotent/{PTBN,PSBN}_undercontrol_taggedtree.lp` dans un dossier temporaire, y copier la version intermédiaire, puis lancer `clingcon 0 --project -q --time-limit=60` avec `-c d=3 -c v3=0 -c v2=2 -c v1=0 -c v0=0` (vecteur) ou `-c d=3` seul (global). Il faut borner la mémoire (`ulimit -v`) et la durée (`timeout`), car la version `88ccf0e` sature la machine : sans borne, un premier essai a été tué.
- **Parallélisation en ASP.** Mesuré le 3 juillet (conversation e37f3aaa) : `--parallel 4` accélère encore de ×2,9, soit environ 70 % du gain idéal, ce qui nuance le « généralement peu efficace » du placeholder.
- Proposition pour la passe : une table de temps sur une même machine, pour l'énumération globale PSBN en d = 3 (34 343 lignes), avec `clingcon --parallel 1, 2, 4, 8`, puis avec JPP, qui répartit le travail par vecteurs et par tranches.
  - Commande type : `clingcon 0 --project --parallel <k> -c d=3 JPPipeline/src/asp/PSBN_undercontrol_taggedtree.lp`, chronométrée, et pour JPP la commande de C4.
- *Décidé (Quentin, 2026-10-04) :* oui pour la parallélisation (`--parallel 1, 2, 4, 8` contre JPP).

### O2. Image globale de la pipeline (l. 518)
- Montre : les étapes de JPP, avec à chaque flèche un exemple de ce qui y circule.
- Proposition : un schéma TikZ, dans le style de `fig:a-chaine`, avec des exemples pris en d = 2, où une ligne de CSV tient sur la figure :
  - Décomposition : `2` → les 4 vecteurs ⟨1,0,0⟩, ⟨0,2,0⟩, ⟨0,1,2⟩, ⟨0,0,4⟩ ;
  - Énumération (au plus 10 vecteurs à la fois) : ⟨0,2,0⟩ → un SBNP (arbre `1[*,*]`, `f` et `w`) ;
  - Minimisation, aujourd'hui l'identité, en pointillés ;
  - Statistiques → la ligne `0,2,0,"1[*,*]",0101,0000,…,4,0.0,0.25,7` déjà vérifiée (`brouillons/corps_depuis_annexe_A.tex`) ;
  - Écriture du CSV.
- Comptes à afficher sous chaque étape. *Décidé (Quentin, 2026-10-04) :* ceux de d = 2, cohérents avec les exemples ; ceux de d = 3 vont dans le zoom O3.
  - d = 2 : 4 vecteurs, aucun débordement, 50 lignes (36 + 6 + 6 + 2) ;
  - d = 3 (PSBN `taggedtree`) : 10 vecteurs, dont 9 sous le garde-fou (1 575 solutions) et ⟨1,0,0,0⟩ subdivisé en 4 tranches (32 768 solutions), soit 34 343 lignes.
- Hors capture : rien à générer, sinon vérifier les comptes sur les CSV de la passe.

### O3. Zoom sur l'énumération avec garde-fou (l. 522)
- Montre : le chemin d'un vecteur dans l'étape d'énumération.
- Fonctionnement (`Pipe.java`, `EnumeratorPSBNFull`, `EnumeratorPSBN`, `RealizableSbfPrefixes`, `Subdivision.lp`) :
  - JPP demande d'abord au plus 1 000 solutions à `clingcon`. S'il en obtient moins, le vecteur est traité et ses solutions passent à la minimisation.
  - S'il en obtient 1 000, il les jette, si bien que ce premier appel est perdu, et subdivise le vecteur : chaque tranche fixe les d premiers bits de `f_1` (états 0 à d − 1), en ne gardant que les préfixes réalisables par des poids. Il y a 2, 4, 6, 12 et 18 tranches pour d = 2 à 6.
  - Chaque tranche est un appel `clingcon` indépendant, dont les solutions partent une à une vers la minimisation, sans être accumulées, ce qui borne la mémoire.
- Exemple en d = 3 : seul ⟨1,0,0,0⟩ déborde en PSBN, alors qu'en PTBN débordent aussi ⟨0,2,0,0⟩ (3 072 lignes) et ⟨0,1,2,0⟩ (1 344). Les 4 tranches correspondent aux signes de `w_1,1` et `w_2,1` (bits `f_1(001)` et `f_1(010)`, `f_1(000)` valant toujours 0) et reçoivent 6 144, 10 240, 10 240 et 6 144 dynamiques.
- Vue : schéma TikZ en arbre de décision, avec l'exemple en d = 3. Rien à générer.

### O4. « utilisation ? » (l. 524)
- Hors génération : un renvoi à l'annexe (`\cref{ann:jppipeline}`) suffit.

### O5. « post processing python relativement abandonné ici » (l. 527)
- Hors génération. Pour la rédaction, ce qui a remplacé le post-traitement Python : les statistiques sont calculées dans JPP (`Statifier`, `SBFStatTable`), et le comptage des génotypes par ApproxASP a cédé la place au `GenotypeCount` exact (annexe A.6).

### O6. Machine HPC : spécifications et gains (l. 529)
- Les traces disent seulement qu'une machine distante sous Ubuntu a servi à partir du 12 juin, avec un JDK réinstallé et les sources tirées par git.
- *Décidé (Quentin, 2026-10-04) :* il n'y a plus accès, et n'a ni ses spécifications ni ses mesures. De mémoire, elle accélérait les exécutions d'un facteur au moins 4, et jusqu'à 10. On l'évoque rapidement dans le corps, pour montrer qu'un outil de ce type a été employé. Rien à générer.
- Pour la rédaction : le facteur se cite comme un souvenir (`% src : Quentin, de mémoire, 2026-10-04`), sans spécifications inventées.

## Placeholders antérieurs aux sections déjà traitées

### S1. « [Scatter robustesse evolutivité] » (section Statistiques, l. 340)
- Même figure que OL1 (l. 596), qui la détaille.
- *Décidé (Quentin, 2026-10-04) :* une seule figure, placée dans Observations et limites, à laquelle l. 340 renvoie par `\Cref`.

### X1. « [Image issue des simulations] » (contexte, l. 193)
- Hors génération : c'est une image des simulations d'agents de Corentin Lacaze, à lui demander.

### G1. « [donner pseudo doc en annexe] » (Guide de génération des CSV, l. 572)
- Hors génération : un renvoi à l'annexe (`\Cref{ann:jppipeline}`). Pour la rédaction, tous les points de cette sous-section (arguments, changement d'énumérateur, garde-fou et parallélisme codés en dur, statistiques, gzip) sont désormais dans les annexes A.3 et A.4, si bien qu'elle pourra se réduire à ce renvoi.

## Section Observations et limites

### OL1. Scatter évolutivité–robustesse en plusieurs dimensions, avec p-valeur (l. 594-596)
- Montre : la corrélation positive entre robustesse phénotypique (`Robustness_mean`) et évolutivité phénotypique (`Evolvability`), comme chez Wagner, dans chaque dimension.
- Données : un point par dynamique, c'est-à-dire par phénotype. En d = 2 et d = 3, ce sont toutes les dynamiques, données par la ligne du vecteur trivial du CSV JPP, où chacune apparaît exactement une fois. En d = 4 et d = 5, c'est MCSBN avec `--measure variety` (toutes les dynamiques équiprobables), dont les lignes sont des dynamiques distinctes. Un tirage de 100 000 dynamiques prend moins d'une seconde.
- Mesure du 2026-10-04 (ρ de Spearman, à recalculer dans la passe) :

  | d | Dynamiques | ρ | p |
  |---|---:|---:|---:|
  | 2 | 36 (toutes) | 0,63 | 5·10⁻⁵ |
  | 3 | 32 768 (toutes) | 0,81 | < 10⁻³⁰⁰ |
  | 4 | 100 000 (tirées) | 0,78 | < 10⁻³⁰⁰ |
  | 5 | 100 000 (tirées) | 0,69 | < 10⁻³⁰⁰ |

  Avec autant de points, la p-valeur est toujours infime, si bien que c'est ρ qui porte l'information. La corrélation est positive dans les quatre dimensions, ce qui permet de dire plus que « compatible avec Wagner ». L'item « Régression linéaire pour confirmer Wagner » des travaux inachevés (l. 629) serait alors à revoir.
- Commandes : pour d = 2 et 3, celle de C4 (en changeant la dimension) ; pour d = 4 et 5, `./bin/mcsbn -d <d> -n 100000 -o <sortie>` depuis `MCSBN/` (graine fixe par défaut) ; enfin `scipy.stats.spearmanr` dans le script de la passe.
- Vue : `sbn_scatter.html`, x = `Robustness_mean`, y = `Evolvability`, une sous-figure par dimension, avec ρ et p dans la légende.
- Existant, moins adapté parce que non uniforme : `figures/4d_paysage_hybride_Robustness_mean_vs_Evolvability.png` (paysage hybride de `core_then_walk.py`, biaisé vers les pluripotents) et `figures/5d_PSBN_undecomposablePBN_beyond_R_P_mean_vs_E_P.png` (énumération partielle de JPP).
- *Décidé (Quentin, 2026-10-04) :* pas de d = 6. Pour la statistique, Quentin s'en remet au conseil de Claude, qui recommande le ρ de Spearman : c'est la statistique de Wagner (« Spearman's s = 0.55, p < 10⁻¹⁷, n = 2.5×10⁴ » pour la robustesse et l'évolutivité des structures d'ARN, `biblio/Robustness_and_evolvability_Wagner.pdf`, p. 93-94), ce qui rend nos chiffres directement comparables aux siens, et la relation n'a pas de raison d'être linéaire. Retenu sauf avis contraire.

### OL2. Graphiques annotés de flèches, un par assertion (l. 600-606)
- Comme pour P4, Quentin annote lui-même les captures. Données : CSV PSBN `taggedtree` en d = 3 (commande de C4), qui porte tous les vecteurs de chaque dynamique ; d'autres dimensions si l'assertion le demande.
- **OL2a.** La décomposition détermine les autres propriétés (l. 602). Vue : `sbn_scatter.html`, `Robustness_mean` contre `Evolvability`, coloré par vecteur (couleur par défaut). La page dessine les dynamiques les plus décomposées au-dessus, et la légende permet d'isoler un vecteur.
- **OL2b.** Les propriétés suivent la dimension de la plus grande hyper-face non décomposable, notamment `Robustness_std` (l. 604). Vue : `sbn_scatter.html`, `Robustness_mean` contre `Robustness_std`. La légende de la page regroupe déjà les vecteurs selon leur premier coefficient non nul, c'est-à-dire selon cette hyper-face. Existant en d = 4 : `figures/4d_paysage_hybride_Robustness_mean_vs_Robustness_std.png` (2 juillet, paysage hybride).
- **OL2c.** Des SBF particulières forment des groupes dans le graphique variance/moyenne de la robustesse (l. 606).
  - *Précisé (Quentin, 2026-10-04) :* ce sont généralement des groupes qui ont en commun une SBF particulière, typiquement celle des poids tous nuls, c'est-à-dire la fonction constante 0.
  - En d = 3 (toutes les dynamiques, 2026-10-04), le nombre k de nœuds dont la fonction est la constante 0 sépare presque les dynamiques selon `Robustness_mean` : de 0 à 0,25 pour k = 0 (29 791 dynamiques), de 0,17 à 0,33 pour k = 1 (2 883), de 0,33 à 0,42 pour k = 2 (93), et 0,5 pour k = 3 (1). La moyenne de `Robustness_std` baisse quand k augmente (0,022 ; 0,017 ; 0,010 ; 0).
  - `sbn_scatter.html` ne colore que par vecteur. *Décidé (Quentin, 2026-10-04), si c'est facilement faisable :* le script de la passe trace lui-même ce nuage (matplotlib, `Robustness_mean` contre `Robustness_std`, couleur selon k), et Quentin l'annote comme les autres. Sinon, on en reparle.

### OL3. « [Cf. règles de mutations] » (l. 608)
- Hors génération : renvoi à la section Métagraphes (`\Cref`), où la règle de mutation est définie (M3, M4).

### OL4. « [illustration] » : les PSBN les plus décomposés font le lien entre les orientations (l. 610)
- Montre : dans le métagraphe, les PSBN se regroupent par orientation (le nœud de contrôle choisi, à permutation près), et les plus décomposés, que les permutations affectent moins, relient ces groupes.
- `metagraphe.html` colore par décomposition (le vecteur le plus fin de chaque dynamique), par degré ou par une statistique, mais pas par orientation.
- *Décidé (Quentin, 2026-10-04) :* reprendre la figure de M2 (d = 3, PTBN `taggedtree`, couleur par décomposition), sur laquelle Quentin entoure à la main les groupes d'orientation. Une coloration par orientation demanderait de modifier la page : *reporté*.

## Ressource pour la section « Exploration randomisée : MCSBN » (sans placeholder)
- Pour « énumération brute puis post processing → on ne récupère quasiment que des non décomposés » (l. 556), un chiffre est disponible : dans un tirage uniforme MCSBN de 100 000 dynamiques, le vecteur est trivial pour 98,9 % d'entre elles en d = 4 et 99,97 % en d = 5 (tirages du 2026-10-04, graine par défaut).
