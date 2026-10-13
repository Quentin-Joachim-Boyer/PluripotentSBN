# Version UGA — plan d'élagage

Fichier : `rapport_uga.tex`, copie de `rapport_stage.tex` (2026-10-10) qui partage `figures/`, `annexes/` et `references.bib`. Consignes : parties 1 et 2 (« stage assistant ingénieur ») de `sources/consignes_UGA.pdf`.

## Décisions de Quentin (2026-10-10)

- Consignes du stage assistant ingénieur : 15 à 20 pages de corps.
- Modifier le texte le moins possible : on condense en coupant ou en déplaçant, pas en réécrivant. Style impersonnel conservé.
- Contribution : une phrase en tête de 1.3 (faite).
- Bilan personnel : la conclusion, plus une phrase sur ce que ces difficultés ont appris (faite).
- Page de garde : Jean-Marc Brossier (enseignant membre du jury), 6 chemin Saint Ferjus, 38700 La Tronche (faite, en attendant le modèle de l'intranet).
- Obstacles : section « Difficultés rencontrées », avant la conclusion, avec le texte de Quentin à la première personne, qui remplace le brouillon de Claude.
- Conclusion laissée telle quelle pour l'instant.
- Ce qu'on garde ou non : points 1, 2 et 3 acceptés, sauf 3e (garder au moins une capture par page HTML) ; tableau des formulations de `PSBN_undercontrol_taggedtree.lp` retiré en plus. Appliqué le 2026-10-10.

## Mesures

Interligne simple appliqué : le corps fait 32 pages (introduction p. 3, conclusion terminée p. 34) avec 23 figures et 5 tableaux. Il faut donc gagner 12 pages. Les gains ci-dessous sont mesurés par la hauteur de chaque bloc dans le PDF : ils comptent les blancs laissés par les figures fixes et ne s'additionnent qu'approximativement.

## Propositions, à trancher une à une

### 1. Mise en page, sans toucher au texte (≈ 2 p.)

- 1a. Figures et tableaux flottants (`[htbp]` au lieu de `[H]`) : 32 → 30 pages, mesuré. Les figures ne sont plus forcément à l'endroit exact du texte, mais les renvois `\Cref` restent.

### 2. Déplacer en annexe, texte inchangé (≈ 4,8 p.)

Les annexes ne comptent pas dans les 20 pages. Une annexe « Compléments » avant le guide recevrait :

- 2a. 2.2.1 Calcul de la borne des poids, avec la preuve et la figure des chambres : 2,7 p. Dans 2.2, « dont le calcul est expliqué plus bas » renverrait à l'annexe.
- 2b. Les autres formes de pluripotence de 2.3, chacune avec sa figure : PSBNI (0,7 p.), décompositions partielles (0,55 p.), partie contrôle et partie opérative (0,9 p.). Elles sont déjà dans les perspectives de la conclusion.

### 3. Retirer des figures (≈ 5,5 p. pour l'ensemble)

Il resterait une dizaine de figures dans le corps. Les renvois vers une figure retirée seraient supprimés de la phrase, sans autre retouche.

- 3a. Figure 1 (une structure quelconque et sa dynamique) : 0,5 p. La figure X2, juste après, montre déjà une structure et sa dynamique ; les renvois de 2.1 pointeraient vers elle.
- 3b. Métagraphe d'Ai-Ling (2.5) : environ 0,6 p. pour la figure seule, 1,1 p. avec les deux paragraphes sur ses réseaux et sur la distance DA.
- 3c. Figures de 3.1 sauf celle de l'arbre étiqueté : PTBN et PSBN à arbre fixé (0,8 p.), dynamique écartée par Laurent (0,5 p.), dynamique trop décomposable (environ 0,5 p.), deux orientations de l'arbre (0,8 p.).
- 3d. Garde-fou de JPP (0,6 p.), déjà décrit dans le texte.
- 3e. Captures de `sbn_scatter.html` et `metagraphe.html` (1,4 p.), en ne gardant que celle de `sbn_viz.html`.

### 4. Autres candidats, si les points 1 à 3 ne suffisent pas

- Paragraphe de renvoi aux annexes en tête des Résultats (0,2 p.), utile surtout aux collègues du labo.
- Tableau des SBF en dimension 2 (0,25 p.).
- Les cinq endroits où la règle de mutation est codée, NVEIL, le post-traitement Python et la machine distante (0,25 p. en tout).
- Figures des résultats : OL1 réduite à deux dimensions (environ 0,7 p.), l'une de OL2a ou OL2b (0,65 à 1 p.), robustesse selon k (0,95 p. avec son paragraphe).
- Usage des grands modèles de langage (0,65 p.) : à garder plutôt, car c'est la partie la plus proche d'un bilan personnel.

Bilan si l'on retient 1, 2 et 3 : environ 32 − 2 − 4,8 − 5,5 ≈ 19,7 pages, à vérifier par la compilation.

## Après l'élagage du 2026-10-10

Corps de 21,7 pages (mesuré du haut de la p. 3 à la fin de la conclusion), 12 figures et 3 tableaux dans le corps, annexe A « Compléments » avant le guide. Pistes mesurées pour passer sous 20 pages, chacune sur une copie :

- Paramètres de placement des flottants, qui laissent les figures partager une page avec le texte au lieu d'occuper des pages à moitié vides (aucun changement de texte) : −0,65 p.
- Figure de la robustesse selon k (le paragraphe garde ses chiffres) : −0,45 p.
- Les deux paragraphes de renvoi aux annexes en tête des Résultats : −0,25 p.
- Les cinq endroits de la règle de mutation, NVEIL, le post-traitement Python et la machine distante : −0,2 p.
- Ces quatre pistes ensemble : 20,1 p. ; avec en plus les captures des pages HTML à 85 % de la largeur : 20,0 p. ; à 75 % : 19,8 p. ; ou sans la figure OL2b : 19,7 p.
- Réduire OL1, OL2a ou OL2b ne fait rien gagner tant qu'elles restent sur des pages de figures.

Appliqué ensuite (Quentin, 2026-10-10) : figure de la pipeline JPP passée à l'horizontale, et retrait des cinq endroits de la règle de mutation, du post-traitement Python et de la machine distante (NVEIL gardé). Corps : 20,9 pages. Restent mesurés : placement des flottants seul −0,2 p. ; avec la figure de la robustesse selon k, 20,2 p. ; avec en plus les paragraphes de renvoi aux annexes des Résultats, 20,0 p.

Appliqué ensuite (Quentin, 2026-10-10) : paramètres de placement des flottants, retrait de la figure de la robustesse selon k (paragraphe gardé) et des deux paragraphes de renvoi aux annexes en tête des Résultats. Corps : 19,97 pages (p. 3 à 22), sans marge.

Réductions de taille testées (OL1, OL2a, OL2b, captures) : au mieux −0,6 p., au prix de la lisibilité ; non appliquées. Quentin envoie la version à 19,97 pages telle quelle (2026-10-10).

## Page de garde

Faite le 2026-10-10 sur le modèle Ensimag de l'intranet (`couv_pfe_latex/garde/garde.tex`, modèle de PFE adapté : « Rapport de stage assistant ingénieur », durée, enseignant membre du jury). Logos dans `figures/garde/` : celui de l'Ensimag vient du modèle, celui du TIMC de la couverture du rapport de Danwen.
