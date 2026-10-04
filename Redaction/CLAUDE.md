# Rapport de stage — consignes de rédaction pour Claude

Relire ce fichier avant toute séance de rédaction (rapport ou annexes).

## Contexte

- Rapport de stage M1 AM (UGA, Grenoble INP Ensimag) de Quentin Boyer, équipe BCM du laboratoire TIMC (Grenoble), encadré par Nicolas Glade et Laurent Trilling.
- Stage commencé le 11 mai 2026 ; développement tracé par le git (commits du 17 mai au 3 juillet 2026). Rédaction reprise en octobre 2026 : les souvenirs de Quentin sont certes un peu émoussés, mais il a encore en tête pas mal d'élément, mais surtout les traces font foi.
- Sujet : exploration du paysage des réseaux booléens à signe (SBN) pluripotents. Énumération (ASP/clingcon, pipeline Java JPP, Monte-Carlo MCSBN), statistiques à la Wagner, visualisations HTML.
- Fichiers : `rapport_stage.tex` (compilation pdflatex, biber, pdflatex), `references.bib`, `figures/`, `annexes/` (une seule annexe, « Guide d'utilisation des programmes », dont chaque partie est dans un fichier : `A_vue_ensemble.tex` pour l'organisation du dépôt et le format des CSV, puis `B_asp.tex`, `C_jppipeline.tex`, `D_mcsbn.tex` et `F_scripts.tex` ; la partie sur les visualisations a été retirée), `sources/` (traces et outils), `brouillons/` (passages écartés des annexes, à reprendre dans le corps ; non compilés).

## Lecteurs et versions

1. **Version « sans limite » pour les collègues du labo** (prioritaire) : ceux qui reprendront le sujet et le code. Le but est de faire avancer le sujet : ce qui a été fait, comment le refaire, ce qui reste ouvert. La reproductibilité compte plus que la longueur.
2. **Version condensée selon les consignes UGA**, plus tard, à partir de la première.

L'« article » évoqué en 1.3 est un futur papier distinct, pas ce rapport.

Le lecteur est compétent : ne pas lui expliquer l'évident (par exemple qu'il faut un compilateur Java pour compiler du Java), ni lui proposer de procédure pour vérifier son installation, ni lui décrire une interface qui s'explique d'elle-même (les pages HTML n'ont pas de partie dans l'annexe). On ne lui donne que les informations qui pourraient lui poser problème s'il ne les avait pas, comme une dépendance inhabituelle. Le rapport n'est pas une réponse serviable à un utilisateur d'assistant.

## Honnêteté et fidélité (non négociable)

- Ne jamais inventer un chiffre, un résultat, une date, une intention ou une motivation.
- Chaque affirmation factuelle doit pouvoir pointer vers une source : commit, fichier du repo, CSV, figure, conversation Claude, notes manuscrites, rapport de l'équipe, ou Quentin lui-même quand les traces ne tranchent pas (lui poser la question). Mettre la source en commentaire LaTeX à côté de la phrase (`% src : commit 7dc415c`, `% src : conv a5891d3a 2026-06-12`, `% src : Quentin`). Sans source : écrire `[À VÉRIFIER]`.
- Distinguer explicitement ce qui est fait et vérifié, tenté sans succès, ou pas fait. Les échecs et les pistes abandonnées font partie du rapport.
- Ne pas formuler plus fort que la preuve. Exemple : sans régression ni p-valeur, les scatter robustesse/évolutivité sont « compatibles avec » Wagner, ils ne le « confirment » pas.
- Signaler à Quentin toute incohérence entre le rapport, le code et les traces plutôt que de la lisser.
- Fidélité ne veut pas dire exhaustivité : tout ce qui est écrit doit être vrai et sourcé, mais tout ce qui est vrai n'a pas à être écrit. La clarté et la concision priment sur les détails mineurs que le lecteur peut comprendre seul (exemples écartés de l'annexe A : bug de la colonne `tree`, écrasement des fichiers de sortie, fichiers vides ou tronqués). Ces détails se signalent à Quentin en conversation, pas dans le rapport. Quand plusieurs cas particuliers relèvent d'une même prudence, préférer une mise en garde générale à leur liste (exemple, annexe A : rien de ce qui n'est pas présenté comme fonctionnel n'est garanti sans lire le code, données anciennes comprises).
- Ne pas évoquer dans le rapport ce qui n'est pas encore fait (par exemple la passe unifiée, ni ses résultats ni la transmission de ses CSV) : on l'ajoutera quand ce sera fait.

## Collaboration

- Ne jamais réécrire le texte de Quentin sans demande explicite. Garder ses placeholders `[...]` tant qu'il ne les retire pas.
- Une section (ou une annexe) à la fois. Quentin repasse toujours derrière : proposer des brouillons, pas des versions finales.
- Quand Quentin donne un conseil de portée générale (style, contenu, méthode), l'inscrire aussitôt dans ce fichier, sans attendre qu'il le demande, pour qu'il n'ait pas à se répéter.
- Pendant la rédaction, ne pas ouvrir de réflexion méthodologique ni de développement nouveau : quand une figure ou un résultat en demande un (par exemple une méthode d'estimation en d ≥ 4), le noter comme reporté et passer à la suite.
- Quand une remarque du rapport ne sert qu'à contourner un défaut facile à corriger (dépendance manquante, environnement non versionné, petit bug), proposer de corriger le défaut plutôt que de le documenter. Exemple : `environment.yml` a remplacé la liste des prérequis de l'annexe A.
- Les passages écrits par Claude (borne des poids par ILP, complétude du parcours, table des échelles et sa légende, ancien guide MCSBN) sont des points de départ à remplacer ou réécrire dans la voix de Quentin. Même chose pour les documentations existantes (`MCSBN/README.md`) : bases à améliorer.
- Les équations et preuves formelles sont bienvenues, mais toujours accompagnées d'une explication en prose qui en donne l'intuition (ce que ça dit, pourquoi c'est vrai, à quoi ça sert) : Quentin doit pouvoir les comprendre et les défendre.

## Style de Quentin (à imiter, pas à lisser)

- Phrases longues portées par des incises entre parenthèses.
- « Nous » pour la démarche scientifique, « je » pour le vécu du stage.
- Autodérision légère (« j'ai deux mois, ce n'est pas énorme », `\sout{s'amuser avec}`).
- Franchise sur les échecs, les limites et les pistes non explorées.
- Invitations au lecteur à aller voir ou tester par lui-même ; questions en guise de titres ou de relances.
- Majuscules d'emphase pour les concepts clés (STRUCTURE, DYNAMIQUE) ; cadrage philosophique (le modèle sert à forger des concepts).
- Collègues désignés par leur prénom (« la thèse de Rémi », « le rapport de Danwen »).
- Concision demandée : garder la voix, pas d'incises imbriquées, pas de répétitions. Jusqu'où garder les incises : à arbitrer avec Quentin au cas par cas.
- Concis ne veut pas dire haché. Pas de successions d'affirmations courtes et juxtaposées (une phrase, un fait, phrase suivante) : c'est la prose typique d'une réponse de Claude. Lier les idées par la logique (car, donc, si bien que, alors que, mais), laisser une phrase porter un raisonnement, varier la longueur des phrases. Éviter aussi l'abus des deux-points explicatifs (« X : Y »).
- Pas de comptes rendus de vérification dans le texte (« vérifié en d = 3 », « testé avec… ») : c'est le registre d'une conversation où Claude rend compte de ce qu'il a exécuté. Le texte affirme, et la vérification va dans le commentaire de source (`% src : test 2026-10-03 …`).
- Pas d'affirmations en gras en tête de paragraphe pour en résumer l'idée (`\paragraph{...}`, `\textbf{...}`, ou `\emph{...}` en tête d'item) : c'est un tic de réponse conversationnelle, et le rapport n'est pas une réponse. Structurer par les sections et sous-sections, et enchaîner les paragraphes par la prose.

## Conventions LaTeX

- Tableaux : cellules courtes, pas de colonne « Remarques » rédigée en phrases. L'information passe par la structure, avec une ligne par cas (par exemple une ligne par usage) et des colonnes à valeurs brèves (oui, non, version).
- Commandes à taper : sur une ligne à part (`verbatim`), sans cadre ni autre mise en valeur appuyée.
- Arguments d'un programme : à la manière d'une doc, avec une ligne de synopsis aux arguments nommés (`<dim> <nSolutions> [option]`) et la liste de ces arguments (environnement `description`). Un exemple seulement s'il apporte quelque chose, comme une configuration réellement utilisée (le `launch.json` de JPP).
- Hors mode maths, `_` s'écrit `\_`. Dans `\texttt{}`, `--` devient un tiret : écrire `-{}-` (`\texttt{-{}-seed}`), sauf dans `verbatim`. Noms de fichiers et de programmes dans `\texttt{}` (`\texttt{PTBN\_undercontrol.lp}`).
- Vecteurs de décomposition en maths : `$\langle 0,2,0,0\rangle$`.
- Citations avec `\cite{clé}` et les clés de `references.bib` : glade2022, segretain2023, segretain2020, bonnet2023, defossez2021, wu2024, wagner2008, kauffman1969, hopfield1982, elena2009, banbara2017, kabir2022, zhu2020.
- Figures dans `figures/`, sous-figures côte à côte avec `subfigure`. Labels uniques (`fig:`, `tab:`, `ann:`), renvois avec `\Cref`.
- Vérifier que le document compile après chaque modification.

## Plan de travail

1. **Guide d'utilisation des programmes** (annexe unique, `annexes/`, une partie à la fois). Il doit permettre à Quentin, puis aux collègues, de relancer chaque programme. Ses parties sont des modes d'emploi des programmes au point (JPP avant tout, MCSBN dans une moindre mesure), pas un historique détaillé de tout ce qui a été fait, ni une cartographie exhaustive du dépôt. Elles se bornent à expliquer comment utiliser les programmes : ce que font les programmes et la définition des statistiques vont dans le corps du rapport. Elles ne rappellent pas ce que le corps du rapport a déjà établi, comme les limites de l'énumération exhaustive. Rien de propre à une machine (HPC, poste du labo) : l'exécution est la même partout. Présenter la version aboutie d'un programme. Ne signaler les versions intermédiaires, en une phrase (objectif atteint ou non, pas maintenues jusqu'au bout), que si le lecteur risque de les confondre avec la version aboutie, comme les programmes ASP du dossier de référence ; sinon, la mise en garde générale de A.1 suffit (ex. : ne pas citer w_bound.py ni w_bound_bfs.py). Regrouper ce qui relève d'une même annexe plutôt que de le disperser.
2. **Fiches de figures** (décidé le 2026-10-03, terminé le 2026-10-04) : section par section, transformer chaque placeholder du corps en fiche précise (ce que la figure montre, programme, dimension, vecteur, nombre de solutions, page et vue), dans `Redaction/plan_figures.md`. Quentin tranche chaque fiche.
3. **Passe unifiée** (faite le 2026-10-04, commit `3b331d8`) : `Redaction/passe_unifiee/passe.py` lance toutes les générations décidées dans les fiches, avec des paramètres fixés ; ses résultats (`sortie/resume.md`, non versionné) documenteront toutes les parties du rapport, avec `% src : passe unifiée 3b331d8`.
4. **Sections manquantes**, une à la fois, à partir de ces résultats.
5. Résumé et abstract en dernier.
6. Plus tard : la version UGA condensée.

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
- **Présentation de fin de stage** : `figures/Exploration de la pluripotence dans le paysage des SBN..pdf` (15 diapos, fil narratif validé à l'oral).
- **Travaux de l'équipe** : `../biblio/` (HDR de Nicolas, thèse et article de Rémi, rapports d'Ai-Ling, de Rémy et de Danwen).

## Points connus

À expliciter dans le rapport :

- Exhaustivité : pas raisonnable à partir de d = 4 ; données non représentatives à partir de d = 5.
- Borne des poids en d = 6 : le code utilise 6 (choix antérieur au calcul des bornes), l'ILP donne 9. Biais sur les poids assumé, qui s'ajoute au biais d'exploration. Non corrigé car d = 6 est marginal dans ce travail (la plupart des programmes ASP ne le gèrent pas) ; les graphiques en d = 6 valent preuve de concept, pas plus.

- Analogie à proposer à la rédaction (Quentin, 2026-10-03) : partie contrôle / partie opérative (PC/PO), le paradigme par lequel Quentin a appris le fonctionnement d'un processeur, pour le réseau de contrôle et le réseau contrôlé.

Petites corrections en attente :

- Labels dupliqués dans `rapport_stage.tex` : `fig:mon-label` (3 fois), `fig:structure-pluripotente-3d` et `fig:dynamique-pluripotente-3d` (2 fois chacun). Sans effet tant qu'aucun `\Cref` ne pointe dessus ; à renommer avec l'accord de Quentin.

Décisions :

- Programmes ASP : la copie de référence est `JPPipeline/src/asp/`, celle qu'utilise JPP (confirmé par Quentin). `SBN_pluripotent/` garde des versions antérieures (4 fichiers divergent) et des programmes de test (`*_HS.lp`) : ne pas s'en servir pour la passe unifiée.
