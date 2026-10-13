# Rapport de stage — consignes de rédaction pour Claude

Relire ce fichier avant toute séance de rédaction (rapport ou annexes).

## Contexte

- Rapport de stage M1 AM (UGA, Grenoble INP Ensimag) de Quentin Boyer, équipe BCM du laboratoire TIMC (Grenoble), encadré par Nicolas Glade et Laurent Trilling.
- Stage du 11 mai au 3 juillet 2026 (dates officielles, confirmées par Quentin le 2026-10-07, sur la page de titre) ; développement tracé par le git (commits du 17 mai au 3 juillet 2026). Rédaction reprise en octobre 2026 : les souvenirs de Quentin sont certes un peu émoussés, mais il a encore en tête pas mal d'élément, mais surtout les traces font foi.
- Sujet : exploration du paysage des réseaux booléens à signe (SBN) pluripotents. Énumération (ASP/clingcon, pipeline Java JPP, Monte-Carlo MCSBN), statistiques à la Wagner, visualisations HTML.
- Fichiers : `rapport_stage.tex` (compilation pdflatex, biber, pdflatex), `references.bib`, `figures/`, `annexes/` (une seule annexe, « Guide d'utilisation des programmes », dont chaque partie est dans un fichier : `A_vue_ensemble.tex` pour l'organisation du dépôt et le format des CSV, puis `B_asp.tex`, `C_jppipeline.tex`, `D_mcsbn.tex` et `F_scripts.tex` ; la partie sur les visualisations a été retirée), `sources/` (traces et outils), `brouillons/` (passages écartés des annexes, à reprendre dans le corps ; non compilés).

## Lecteurs et versions

1. **Version « sans limite » pour les collègues du labo** (prioritaire) : ceux qui reprendront le sujet et le code. Le but est de faire avancer le sujet : ce qui a été fait, comment le refaire, ce qui reste ouvert. La reproductibilité compte plus que la longueur.
2. **Version condensée selon les consignes UGA**, à partir de la première (commencée le 2026-10-07). Consignes dans `sources/consignes_UGA.pdf`, parties 1 et 2 (« stage assistant ingénieur ») : 15 à 20 pages hors garde et table des matières, 12 pt, marges ≤ 2,5 cm, interligne simple, page de garde du modèle de l'intranet (mention « stage assistant ingénieur », enseignant membre du jury, adresse de la structure, dates et durée), problématique lisible par un non-spécialiste, sigles explicités, titres sans sigles seuls, synthèse et non récit chronologique, contribution personnelle sans ambiguïté, contexte de la structure d'accueil (2 p. max), bilan personnel (1 p.) et obstacles, pas d'abus d'illustrations. Fichier : `rapport_uga.tex`, copie du rapport labo (2026-10-10). Décisions de Quentin (2026-10-10) : modifier le texte le moins possible, donc condenser en coupant ou en déplaçant en annexe plutôt qu'en réécrivant ; style impersonnel conservé, la contribution étant dite par une seule phrase en 1.3 ; le bilan personnel est la conclusion. Ce qui est gardé se discute point par point : `plan_uga.md`.

La phrase de 1.3 sur un futur article a été supprimée (Quentin, 2026-10-06) : le rapport n'en parle pas.

Le lecteur est compétent : ne pas lui expliquer l'évident (par exemple qu'il faut un compilateur Java pour compiler du Java), ni lui proposer de procédure pour vérifier son installation, ni lui décrire une interface qui s'explique d'elle-même (les pages HTML n'ont pas de partie dans l'annexe). On ne lui donne que les informations qui pourraient lui poser problème s'il ne les avait pas, comme une dépendance inhabituelle. Le rapport n'est pas une réponse serviable à un utilisateur d'assistant.

## Honnêteté et fidélité (non négociable)

- Ne jamais inventer un chiffre, un résultat, une date, une intention ou une motivation.
- Chaque affirmation factuelle doit pouvoir pointer vers une source : commit, fichier du repo, CSV, figure, conversation Claude, notes manuscrites, rapport de l'équipe, ou Quentin lui-même quand les traces ne tranchent pas (lui poser la question). Mettre la source en commentaire LaTeX à côté de la phrase (`% src : commit 7dc415c`, `% src : conv a5891d3a 2026-06-12`, `% src : Quentin`). Sans source : écrire `[À VÉRIFIER]`.
- Distinguer explicitement ce qui est fait et vérifié, tenté sans succès, ou pas fait. Les échecs et les pistes abandonnées font partie du rapport.
- Ne pas formuler plus fort que la preuve. Exemple : sans régression ni p-valeur, les scatter robustesse/évolutivité sont « compatibles avec » Wagner, ils ne le « confirment » pas.
- Signaler à Quentin toute incohérence entre le rapport, le code et les traces plutôt que de la lisser.
- Fidélité ne veut pas dire exhaustivité : tout ce qui est écrit doit être vrai et sourcé, mais tout ce qui est vrai n'a pas à être écrit. La clarté et la concision priment sur les détails mineurs que le lecteur peut comprendre seul (exemples écartés de l'annexe A : bug de la colonne `tree`, écrasement des fichiers de sortie, fichiers vides ou tronqués). Ces détails se signalent à Quentin en conversation, pas dans le rapport. Quand plusieurs cas particuliers relèvent d'une même prudence, préférer une mise en garde générale à leur liste (exemple, annexe A : rien de ce qui n'est pas présenté comme fonctionnel n'est garanti sans lire le code, données anciennes comprises).
- Ne pas évoquer dans le rapport ce qui n'est pas encore fait : on l'ajoutera quand ce sera fait.
- La passe unifiée n'apparaît pas dans le rapport (Quentin, 2026-10-04, « pas la peine ») : ses résultats sont la source des chiffres et des figures, citée en commentaire (`% src : passe unifiée ae10d77`), mais le texte ne parle ni d'elle ni de `passe.py`.

## Collaboration

- Ne jamais réécrire le texte de Quentin sans demande explicite. Garder ses placeholders `[...]` tant qu'il ne les retire pas.
- Une section (ou une annexe) à la fois. Quentin repasse toujours derrière : proposer des brouillons, pas des versions finales.
- Quand Quentin donne un conseil de portée générale (style, contenu, méthode), l'inscrire aussitôt dans ce fichier, sans attendre qu'il le demande, pour qu'il n'ait pas à se répéter.
- Pendant la rédaction, ne pas ouvrir de réflexion méthodologique ni de développement nouveau : quand une figure ou un résultat en demande un (par exemple une méthode d'estimation en d ≥ 4), le noter comme reporté et passer à la suite.
- Le plan d'une section est celui de Quentin : ses puces et ses placeholders, dans leur ordre. Les étoffer en gardant ses formulations, sans imposer de plan ni réorganiser (les plans en commentaires proposés par Claude en juin ont tous été remplacés).
- Viser court : la première version de l'annexe A était « sans doute trop ». Mieux vaut un brouillon un peu court que Quentin complète qu'un brouillon long qu'il doit élaguer. Une partie qui n'aurait presque rien à dire (comme celle sur les pages HTML) s'omet plutôt que de se remplir.
- Avant de rendre un brouillon, le relire contre la section Style ci-dessous. Certaines consignes ont dû être répétées alors qu'elles étaient notées (décrire l'usage et non le fonctionnement dans l'annexe, prose hachée, réponse serviable) : la relecture sert à les attraper avant Quentin.
- Quand une remarque du rapport ne sert qu'à contourner un défaut facile à corriger (dépendance manquante, environnement non versionné, petit bug), proposer de corriger le défaut plutôt que de le documenter. Exemple : `environment.yml` a remplacé la liste des prérequis de l'annexe A.
- Les passages écrits par Claude (borne des poids par ILP, complétude du parcours, table des échelles et sa légende, ancien guide MCSBN) sont des points de départ à remplacer ou réécrire dans la voix de Quentin. Même chose pour les documentations existantes (`MCSBN/README.md`) : bases à améliorer.
- Les équations et preuves formelles sont bienvenues, mais toujours accompagnées d'une explication en prose qui en donne l'intuition (ce que ça dit, pourquoi c'est vrai, à quoi ça sert) : Quentin doit pouvoir les comprendre et les défendre. Cette explication se donne en conversation, ou autour de la preuve (texte, figure) ; la preuve elle-même garde une structure mathématique nette (« Soit… Posons… Ou bien…, auquel cas… Donc… »), sans être délayée en prose, car la prose la rend moins claire (Quentin, 2026-10-06).

## Style de Quentin (à imiter, pas à lisser)

- Phrases longues portées par des incises entre parenthèses. Mais Quentin doute de l'élégance de ses nombreuses parenthèses et compte les reprendre lui-même (2026-10-05) : ne pas en ajouter pour l'imiter.
- Style impersonnel (Quentin, 2026-10-05) : « je » très rare, « nous » rare, tournures impersonnelles et passives de préférence (ancienne consigne « nous » pour la démarche, « je » pour le vécu, abandonnée).
- Autodérision légère (« j'ai deux mois, ce n'est pas énorme », `\sout{s'amuser avec}`).
- Franchise sur les échecs, les limites et les pistes non explorées.
- Invitations au lecteur à aller voir ou tester par lui-même ; questions en guise de titres ou de relances, mais seulement dans l'introduction et les passages peu techniques : dans les sections techniques, elles alourdissent (Quentin, 2026-10-05).
- Majuscules d'emphase pour les concepts clés (STRUCTURE, DYNAMIQUE) ; cadrage philosophique (le modèle sert à forger des concepts).
- Collègues désignés par leur prénom (« la thèse de Rémi », « le rapport de Danwen »).
- Concision demandée : garder la voix, pas d'incises imbriquées, pas de répétitions. Jusqu'où garder les incises : à arbitrer avec Quentin au cas par cas.
- Concis ne veut pas dire haché. Pas de successions d'affirmations courtes et juxtaposées (une phrase, un fait, phrase suivante) : c'est la prose typique d'une réponse de Claude. Lier les idées par la logique (car, donc, si bien que, alors que, mais), laisser une phrase porter un raisonnement, varier la longueur des phrases. Éviter aussi l'abus des deux-points explicatifs (« X : Y »).
- Pas de dates dans le texte du rapport (Quentin, 2026-10-05), par exemple « à partir du 12 juin » ou « version du 3 juillet » : elles restent dans les commentaires de source. Une estimation non mesurée se dit comme un ordre de grandeur (« environ »), en précisant qu'aucune mesure précise n'a été faite, et non « de mémoire ».
- Moins de chiffres (Quentin, 2026-10-06) : un nombre n'apparaît que s'il porte un argument (écart avec Laurent, échec d'un programme, validation), pas pour décrire. Compter des dynamiques et non des lignes de CSV (sauf pour mesurer une charge de calcul), et préférer un nombre qui renvoie au tableau des échelles (658 PSBN en dimension 3) à un nombre isolé.
- Pas de comptes rendus de vérification dans le texte (« vérifié en d = 3 », « testé avec… ») : c'est le registre d'une conversation où Claude rend compte de ce qu'il a exécuté. Le texte affirme, et la vérification va dans le commentaire de source (`% src : test 2026-10-03 …`).
- Style indirect (Quentin, 2026-10-05) : préférer les tournures impersonnelles aux assertions directes à sujet « nous ». Mesuré chez Quentin, pour 1 000 mots : « il est / il a été / il s'agit / il faut » 5, « permet » 5, passifs 2, atténuations (« semble », « pourrait », « sans doute ») 4, sujets abstraits (« L'idée », « L'objectif ») 3. Les atténuations ne s'appliquent pas à un fait établi (un compte exact reste affirmé).
- Tics de Claude mesurés le 2026-10-05 (fréquence dans ses brouillons contre celle chez Quentin) : enchaîner plusieurs connecteurs dans une même phrase (« si bien que », « , ce qui », « puisque », « alors que », « de sorte que », participes absolus), « nous » partout, verbes techniques (« se lit », « se déduit », « revient à », « réaliser », « porter une sous-dynamique »), « exactement », « précisément », « bien plus », « en permanence », « justement », « d'ailleurs », paragraphes ouverts par « Reste à » ou « Enfin ». Quentin écrit plutôt « donc », « mais », « on », « cela », « permet », « il est possible », pose des questions en relance (dans l'introduction seulement, voir plus haut), et fait des phrases plus courtes (33 mots en moyenne contre 42). Éviter les chaînes de trois connecteurs ou plus dans une phrase, mais ne pas sur-découper non plus (Quentin, 2026-10-05) : relier une affirmation et sa justification par « car » plutôt qu'en deux phrases avec « en effet », et viser environ 30 mots par phrase en moyenne.
- Pas d'affirmations en gras en tête de paragraphe pour en résumer l'idée (`\paragraph{...}`, `\textbf{...}`, ou `\emph{...}` en tête d'item) : c'est un tic de réponse conversationnelle, et le rapport n'est pas une réponse. Structurer par les sections et sous-sections, et enchaîner les paragraphes par la prose.

Déduit des réécritures de Quentin (passages de Claude dans le corps, juin-juillet, et annexe A, octobre) :

- Supprimer les marques de rigueur et les justifications que le lecteur fait seul : « exactement », « sans approximation », « (facteur $n!$ en moins) », « le cas $\mathbf{x}=\mathbf{0}$ donne $0 \le 0$, cohérent avec… ». Quentin les a toutes retirées.
- Pas de liste de « Remarques » en fin de passage : une remarque utile s'intègre à la prose, sinon elle disparaît (Quentin a supprimé celles de la borne des poids, et a fait de la remarque finale de l'annexe A un paragraphe général).
- Préférer le verbe simple à la construction savante : « ce qui permet d'écrire le problème comme un programme linéaire » plutôt que « ce qui rend le problème linéaire ; $W(f)$ est donc la valeur d'un programme linéaire ».
- Dans le corps, raisonner avec les concepts et la notation mathématique, sans renvoyer au code (pas de « c'est exactement le test `&sum{...}` de l'encodage ASP ») ni de noms de variables du code dans les formules (`w_bound(n)` est devenu $\max_{f_w} W(f)$). Le code a sa place dans l'annexe.
- Légendes courtes, qui disent ce qu'on voit avec le vocabulaire du rapport et relient les sous-figures (« Une structure quelconque », « Sa dynamique », « Un réseau et son graphe de transition en dimension 3 »).
- Un tableau ne contient que ce que le propos demande. Pour le tableau des SBF en dimension 2, Quentin a fait retirer deux colonnes qui « n'ont pas à être là », remettre la colonne $f(0,0)$, qui « permet de capter les bases », plutôt que de l'expliquer dans la légende, et ordonner les colonnes selon la logique du propos (les poids, puis la fonction qu'ils réalisent, puis son expression logique).
- Ne pas mêler l'explication d'une méthode de calcul et l'exposé de ses résultats numériques : les valeurs (tableau, lecture, conséquences) dans un bloc, la méthode dans un autre (Quentin, 2026-10-04, à propos de la borne des poids en 2.2).
- Définir chaque notation là où elle apparaît pour la première fois, pas plus loin (Quentin, 2026-10-04 : $S_n$ servait dans la comparaison avec les travaux de Rémi avant d'être défini).
- Choisir le mot juste plutôt que le mot générique (Quentin a contesté « prérequis logiciels »), et des titres courts (« Chaîne de traitement et format » plutôt que « Vue d'ensemble de la chaîne de traitement et format des CSV »).
- Pour un mécanisme (comme le garde-fou de JPP), dire à quoi il sert et ce qui a été envisagé, plutôt que ses détails d'exécution (Quentin a fait retirer « le premier appel est perdu »). Un paramètre codé en dur se note par un littéral ($s$) et non par sa valeur, laquelle peut apparaître dans un exemple chiffré (Quentin, 2026-10-06).
- Ouvrir une partie par une phrase qui la situe par rapport à ce qui précède (« Pour ce qui est des autres scripts mis au point, … »), au lieu d'entrer directement dans la matière.

## Conventions LaTeX

- Tableaux : cellules courtes, pas de colonne « Remarques » rédigée en phrases. L'information passe par la structure, avec une ligne par cas (par exemple une ligne par usage) et des colonnes à valeurs brèves (oui, non, version).
- Commandes à taper : sur une ligne à part (`verbatim`), sans cadre ni autre mise en valeur appuyée.
- Pas de commande dans le corps du rapport : elles sont dans l'annexe (guide d'utilisation), à laquelle le corps renvoie par `\Cref`, justement pour ne pas les répéter (Quentin, 2026-10-06).
- Arguments d'un programme : à la manière d'une doc, avec une ligne de synopsis aux arguments nommés (`<dim> <nSolutions> [option]`) et la liste de ces arguments (environnement `description`). Un exemple seulement s'il apporte quelque chose, comme une configuration réellement utilisée (le `launch.json` de JPP).
- Hors mode maths, `_` s'écrit `\_`. Dans `\texttt{}`, `--` devient un tiret : écrire `-{}-` (`\texttt{-{}-seed}`), sauf dans `verbatim`. Noms de fichiers et de programmes dans `\texttt{}` (`\texttt{PTBN\_undercontrol.lp}`).
- Vecteurs de décomposition en maths : `$\langle 0,2,0,0\rangle$`.
- États : toujours en chaîne de bits $x_d \cdots x_1$, le nœud 1 à droite, comme sur les hypercubes de `sbn_viz` (« l'état 100 », « $f(01)$ »), y compris en dimension 2 ; jamais en couple $(x_1, x_2)$, qui inverse l'ordre (Quentin, 2026-10-06). Les couples restent réservés aux vecteurs de poids $(w_1, w_2)$.
- La dimension se note $d$ partout ($\mathcal{T}_d$, $S_d$, $B_d$, $\{0,1\}^d$), jamais $n$ (Quentin, 2026-10-05). Les commentaires de source gardent la notation du code.
- Citations avec `\cite{clé}` et les clés de `references.bib` : glade2022, segretain2023, segretain2020, bonnet2023, defossez2021, wu2024, wagner2008, banbara2017, kabir2022, zhu2020. La bibliographie ne liste que les références citées (plus de `\nocite{*}` depuis le 2026-10-07) : une entrée ajoutée au `.bib` doit être citée pour apparaître.
- Figures dans `figures/`, sous-figures côte à côte avec `subfigure`. Labels uniques (`fig:`, `tab:`, `ann:`), renvois avec `\Cref`.
- Vérifier que le document compile après chaque modification.

## Plan de travail

1. **Guide d'utilisation des programmes** (annexe unique, `annexes/`, une partie à la fois). Il doit permettre à Quentin, puis aux collègues, de relancer chaque programme. Ses parties sont des modes d'emploi des programmes au point (JPP avant tout, MCSBN dans une moindre mesure), pas un historique détaillé de tout ce qui a été fait, ni une cartographie exhaustive du dépôt. Elles se bornent à expliquer comment utiliser les programmes : ce que font les programmes et la définition des statistiques vont dans le corps du rapport. Elles ne rappellent pas ce que le corps du rapport a déjà établi, comme les limites de l'énumération exhaustive. Rien de propre à une machine (HPC, poste du labo) : l'exécution est la même partout. Présenter la version aboutie d'un programme. Ne signaler les versions intermédiaires, en une phrase (objectif atteint ou non, pas maintenues jusqu'au bout), que si le lecteur risque de les confondre avec la version aboutie, comme les programmes ASP du dossier de référence ; sinon, la mise en garde générale de A.1 suffit (ex. : ne pas citer w_bound.py ni w_bound_bfs.py). Regrouper ce qui relève d'une même annexe plutôt que de le disperser.
2. **Fiches de figures** (décidé le 2026-10-03, terminé le 2026-10-04) : section par section, transformer chaque placeholder du corps en fiche précise (ce que la figure montre, programme, dimension, vecteur, nombre de solutions, page et vue), dans `Redaction/plan_figures.md`. Quentin tranche chaque fiche.
3. **Passe unifiée** (faite le 2026-10-04, commit `ae10d77`) : `Redaction/passe_unifiee/passe.py` lance toutes les générations décidées dans les fiches, avec des paramètres fixés ; ses résultats (`sortie/resume.md`, non versionné) documenteront toutes les parties du rapport, avec `% src : passe unifiée ae10d77`.
4. **Sections manquantes**, une à la fois, dans l'ordre du document (Quentin, 2026-10-04), à partir de ces résultats. Tant qu'une capture prévue par une fiche n'est pas faite, le brouillon met un emplacement de figure (cadre vide, légende proposée) avec le nom du fichier attendu et la fiche en commentaire ; Quentin fait les captures quand il veut.
5. Résumé et abstract en dernier.
6. La version UGA condensée (voir « Lecteurs et versions » et `plan_uga.md`).

## Gestion du contexte

- Toujours garder en tête : ce fichier, le plan du rapport (titres des sections) et les deux premières parties de l'annexe (organisation du dépôt et installation, format des CSV), déjà rédigées.
- Pour la section en cours : charger précisément le code, les CSV, les figures, les extraits de conversations et les notes manuscrites qui la concernent.
- Ne pas lire en entier les gros fichiers (CSV, transcripts de conversations) : les interroger.

## Sources

- **Notes manuscrites** de Quentin : `sources/notes_manuscrites/` (photo et `transcription.md`). Tableau des activités du 11 mai au 5 juin, écrit de mémoire vers le milieu du stage : l'enchaînement est fiable, les jours exacts moins ; la transcription les recoupe avec les commits. Après le 5 juin, les commits et les conversations prennent le relais.
- **Git** : `git log`. Messages parfois peu informatifs (« ? », « Cf previous commit ») : à recouper.
- **Conversations Claude Code** (`~/.claude/projects/-home-quentin-boyer-Bureau-asp-PSBN/*.jsonl`, environ 550 k tokens de dialogue). Les interroger avec `python3 sources/chercher_conversations.py "motif"` (options : `--session`, `--role`, `--contexte`, `--max`).
  - `e37f3aaa` : développement ASP/clingcon (27 mai – 3 juillet).
  - `a5891d3a` : pipeline JPP, MCSBN, table des échelles (4 juin – 2 juillet), la plus volumineuse.
  - `4b99165d` : visualisations HTML (22 juin – 3 juillet).
  - `d87eb3ff` : scatter et MCSBN (22 – 26 juin).
  - `27cfe6a9` : rédaction et LaTeX (depuis le 15 juin).
- **Captures d'écran du stage** : `figures/Captures d’écran/` (45 images, 11 juin – 3 juillet), inventoriées et vérifiées dans `plan_figures.md` (section « Captures d'écran du stage »). Anciennes conventions possibles : vérifier une capture avant de l'utiliser.
- **Présentation de fin de stage** : `figures/Exploration de la pluripotence dans le paysage des SBN..pdf` (15 diapos, fil narratif validé à l'oral).
- **Travaux de l'équipe** : `../biblio/` (HDR de Nicolas, thèse et article de Rémi, rapports d'Ai-Ling, de Rémy et de Danwen).

## Points connus

À expliciter dans le rapport :

- Exhaustivité : pas raisonnable à partir de d = 4 ; données non représentatives à partir de d = 5.
- Borne des poids en d = 6 : le code utilise 6 (choix antérieur au calcul des bornes), l'ILP donne 9. Non corrigé, et *retiré du rapport* (Quentin, 2026-10-05, « pas pertinent ») : seule l'annexe A signale que la valeur du code diffère de celle du tableau.

- Analogie partie contrôle / partie opérative (PC/PO) pour le réseau de contrôle et le réseau contrôlé (Quentin, 2026-10-03) : la présenter comme venant de l'architecture des processeurs, sans allusion à la façon dont Quentin l'a apprise (Quentin, 2026-10-05).
- Génération en d = 4 et 5 : placée en 3.2 Optimisation (Quentin, 2026-10-07), à partir du calcul du 2026-10-05 (treeinsolver sans vecteur trivial, 7 h 43). d = 6 n'y est pas traité. Pour le programme de Laurent (3.1, « utilisable que jusqu'en dimension 3 »), le renvoi à 3.2 ne montre toujours que d = 3 (commentaire `À FAIRE` dans le source).
- La colonne `v_*` des CSV de MCSBN est la décomposition en TBN (`decomp_tbn = 1`), pas en SBN : tout pourcentage tiré de ces CSV se dit « en TBN » (comparer au tableau des échelles, qui est en SBN, donnerait une contradiction apparente).

Décisions :

- Résumé : retrouver l'essentiel du rapport plutôt que des aspects précis (Quentin, 2026-10-07). Ni le lien avec Wagner ni la non-exhaustivité de l'énumération ne sont essentiels au travail : ils ne figurent pas dans le résumé.

- `CycleLenMSQ` (moyenne du carré des longueurs d'attracteurs) : choix jugé non pertinent avec le recul, mais on ne touche pas au code (Quentin, 2026-10-04) ; le rapport le dit.
- Orthographe : « Ai-Ling » partout (Quentin, 2026-10-04).
- Pages HTML : ce qu'elles font est présenté dans le corps (section Observation, Quentin 2026-10-04), après une brève introduction des enjeux ; leur usage, jugé intuitif, n'a pas de partie dans l'annexe.
- Plan du corps revu le 2026-10-04 (Quentin) : « Quel paysage explore-t-on ? » vient juste après les SBF (les décompositions sont définies avant les statistiques et les métagraphes) ; l'ancienne 4.1 (guide de génération des CSV) est fondue dans l'introduction de la section 4, devenue « Résultats », sans sous-section ; 3.3 s'appelle « Visualisation » ; la figure P1, doublon de X2, est supprimée.
- Grille de lecture du rapport : au niveau des dynamiques, pas des sous-dynamiques (Quentin, 2026-10-04) ; un réseau qui simule deux fois le même sous-réseau n'est pas écarté.
- Calcul de B_d (2.2.1) laissé tel quel (Quentin, 2026-10-06), après relecture : ni la borne a priori de Cramer (B_d ≤ plus grand déterminant 0/1, qui vaut 1, 1, 2, 3, 5, 9 et coïncide avec B_d), ni l'incise sur les points entiers des chambres, ni les retouches proposées. Ne pas les reproposer.
- Le manuscrit de Laurent (« Pluripotent Boolean network with respect to sub-networks », 2024) n'est pas publié : on ne le cite pas.
- Programmes ASP : la copie de référence est `JPPipeline/src/asp/`, celle qu'utilise JPP (confirmé par Quentin). `SBN_pluripotent/` garde des versions antérieures (4 fichiers divergent) et des programmes de test (`*_HS.lp`) : ne pas s'en servir pour la passe unifiée.
