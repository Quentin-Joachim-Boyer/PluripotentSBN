% Version intermédiaire de PSBN_undercontrol_taggedtree.lp, écrite le 2026-07-03 à 08:04 UTC
% (conversation e37f3aaa) et jamais commitée : réification par pos_side (théorie en tête
% seulement) mais copies auxiliaires des poids encore présentes. Récupérée du transcript le
% 2026-10-04 pour la comparaison de formulations (plan_figures.md, fiche O1). Elle s'utilise
% avec la base PTBN du commit 88ccf0e (git show 88ccf0e:SBN_pluripotent/PTBN_undercontrol_taggedtree.lp),
% placée dans le même dossier. Mesure du 2026-10-04 : 675 modèles en 2,9 s sur <0,2,0,0> en d = 3.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Ceci est une extension du PTBN_undercontrol_taggedtree.lp vérifiant que les
% sous réseaux sont effectivement des SBN (et pas seulement des PTBN/TBN).
%
% Validation croisée (juil. 2026) : sur arbre fixé équivalent, produit
% exactement les mêmes ensembles de dynamiques que PSBN_undercontrol.lp
% (d=2 controle 2 : 3=3 ; d=3 controle 3, poids ±2 : 225=225).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#include "PTBN_undercontrol_taggedtree.lp".

% Contexte d'un sous-réseau : (nouveau Ctx, nouveau CtxOn) engendré par la
% branche "controle activé" d'un branch_node. Contrairement à
% PSBN_undercontrol.lp (arbre en INPUT, control_node = index D fixe), ici le
% noeud de controle est choisi librement par le solveur (taggedtree), donc la
% portée du sous-réseau (les noeuds encore disponibles) n'est plus un simple
% seuil d'indice mais le prédicat choice-dépendant ctx_chain/ctxon_chain.
context(c(CN,Ctx), c(CN,CtxOn)) :- branch_node(CN,_,Ctx,CtxOn).

% Cible valide du sous-réseau : noeud N encore disponible dans le contexte C
% (le noeud de contrôle et ses ancêtres n'appartiennent plus au sous-réseau).
sub_target(N,C,O) :- context(C,O), node(N), not ctx_chain(N,_,C).

% Poids propres (frais) du sous-réseau, un jeu par contexte.
&dom{(-Wb)..Wb} = w(I,J,context(C,O)) :- node(I), node(J), context(C,O), wb(Wb).

% ATTENTION clingcon (pièges découverts empiriquement, cf. PTBN taggedtree) :
%  1. ctx_chain/ctxon_chain descendent du choix { leaf_node } : interdits comme
%     CONDITION d'un élément de &sum ("invalid sum constraint"). On passe par
%     des copies auxiliaires "gelées à 0 hors champ", choix dans le CORPS.
%  2. Ne PAS mettre de garde négative (not ctx_chain(N,_,C)) dans le corps des
%     &dom ni geler via "not sub_target" : le solveur part en thrashing
%     (>20s sans modèle en d=2). Domaines déclarés sur le sur-ensemble fixe,
%     égalités définies pour TOUT N (variables du noeud de contrôle pinnées
%     mais inutilisées), le filtre sur N est porté par les règles de pont.
%  3. Pas d'atome de théorie en CORPS de règle quand context descend d'un
%     choix (même symptôme de thrashing) : le pont passe par un booléen de
%     décision pos_side, théorie en TÊTE uniquement.
%   root_scoped(I,N,C,O)    = w(I,N)              si I disponible, sinon 0.
%   sub_scoped(I,N,C,O)     = w(I,N,context(C,O)) si I disponible, sinon 0.
%   offset_contrib(I,N,C,O) = w(I,N)              si I contrôle ACTIF (ctxon_chain), sinon 0.
&dom{(-Wb)..Wb} = root_scoped(I,N,C,O) :- node(I), node(N), context(C,O), wb(Wb).
&sum{ root_scoped(I,N,C,O) ; -1*w(I,N) } = 0 :- context(C,O), node(N), node(I), not ctx_chain(I,_,C).
&sum{ root_scoped(I,N,C,O)              } = 0 :- context(C,O), node(N), node(I), ctx_chain(I,_,C).

&dom{(-Wb)..Wb} = sub_scoped(I,N,C,O) :- node(I), node(N), context(C,O), wb(Wb).
&sum{ sub_scoped(I,N,C,O) ; -1*w(I,N,context(C,O)) } = 0 :- context(C,O), node(N), node(I), not ctx_chain(I,_,C).
&sum{ sub_scoped(I,N,C,O)                           } = 0 :- context(C,O), node(N), node(I), ctx_chain(I,_,C).

&dom{(-Wb)..Wb} = offset_contrib(I,N,C,O) :- node(I), node(N), context(C,O), wb(Wb).
&sum{ offset_contrib(I,N,C,O) ; -1*w(I,N) } = 0 :- context(C,O), node(N), node(I), ctxon_chain(I,_,O).
&sum{ offset_contrib(I,N,C,O)              } = 0 :- context(C,O), node(N), node(I), not ctxon_chain(I,_,O).

% Offset du noeud N sous contexte (C,O) = somme des poids racine des noeuds de
% contrôle activés menant à ce contexte (condition finale = fait node(I), donc valide).
&dom{(-Wb*d)..(Wb*d)} = offset(N,C,O) :- node(N), context(C,O), wb(Wb).
&sum{ offset(N,C,O) ; -1*offset_contrib(I,N,C,O) : node(I) } = 0 :- context(C,O), node(N).

% Cohérence dynamique : le sous-réseau (poids w(.,.,context(C,O))) doit réaliser
% la même dynamique que le réseau racine restreint à ses noeuds disponibles,
% décalée de l'offset des contrôles actifs (Cf. rapport Danwen).
% pos_side(N,C,O,S) <-> somme racine+offset > 0, et la somme sous-réseau suit.
{ pos_side(N,C,O,S) } :- sub_target(N,C,O), state(S).
&sum{ root_scoped(NI,N,C,O) : node(NI), activated(NI,S) ; offset(N,C,O) } >  0 :- pos_side(N,C,O,S).
&sum{ root_scoped(NI,N,C,O) : node(NI), activated(NI,S) ; offset(N,C,O) } <= 0 :- sub_target(N,C,O), state(S), not pos_side(N,C,O,S).
&sum{ sub_scoped(NI,N,C,O) : node(NI), activated(NI,S) } >  0 :- pos_side(N,C,O,S).
&sum{ sub_scoped(NI,N,C,O) : node(NI), activated(NI,S) } <= 0 :- sub_target(N,C,O), state(S), not pos_side(N,C,O,S).
