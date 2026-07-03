%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Ceci est une extension du PTBN_undercontrol_taggedtree.lp vérifiant que les
% sous réseaux sont effectivement des SBN (et pas seulement des PTBN/TBN).
%
% Validation croisée (juil. 2026) : sur arbre fixé équivalent, produit
% exactement les mêmes ensembles de dynamiques que PSBN_undercontrol.lp
% (d=2 controle 2 : 3=3 ; d=3 controle 3, poids ±2 : 225=225, diff vide),
% et les mêmes comptes que l'encodage par copies auxiliaires (d=2 : 50,
% vecteur <0,2,0,0> d=3 : 675), en ~4-6x plus rapide.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#include "PTBN_undercontrol_taggedtree.lp".

% Idée clé : l'appartenance d'un noeud à une chaîne Ctx/CtxOn est inscrite
% dans le TERME lui-même (c(2,c(1,nil)) contient 1 et 2) et calculée au
% grounding par le prédicat SYNTAXIQUE déterministe chain_member/2, défini
% dans PTBN_undercontrol_taggedtree.lp — utilisable en CONDITION de &sum
% (contrairement à ctx_chain/ctxon_chain qui descendent du choix
% { leaf_node } : "invalid sum constraint"). Cela évite toutes les copies
% auxiliaires (root_scoped/sub_scoped/offset_contrib/offset) d'un encodage
% précédent, d'où le gain de vitesse.

% Contexte d'un sous-réseau : (nouveau Ctx, nouveau CtxOn) engendré par la
% branche "contrôle activé" d'un branch_node. Les noeuds disponibles du
% sous-réseau sont ceux hors de la chaîne C ; les contrôles ACTIFS (offset)
% sont les membres de la chaîne O (membres(O) inclus dans membres(C)).
context(c(CN,Ctx), c(CN,CtxOn)) :- branch_node(CN,_,Ctx,CtxOn).

% Poids propres (frais) du sous-réseau, un jeu par contexte.
&dom{(-Wb)..Wb} = w(I,J,context(C,O)) :- node(I), node(J), context(C,O), wb(Wb).

% Cohérence dynamique : le sous-réseau (poids w(.,.,context(C,O))) doit
% réaliser la même dynamique que le réseau racine restreint à ses noeuds
% disponibles, décalée de l'offset des contrôles actifs (Cf. rapport Danwen).
% ATTENTION clingcon : pas d'atome de théorie en CORPS quand context descend
% d'un choix (thrashing) -> réification par le booléen pos_side, théorie en
% TÊTE uniquement : pos_side(N,C,O,S) <-> somme racine restreinte + offset > 0,
% et la somme du sous-réseau suit pos_side.
{ pos_side(N,C,O,S) } :- context(C,O), node(N), not chain_member(N,C), state(S).
&sum{ w(NI,N) : node(NI), activated(NI,S), not chain_member(NI,C) ; w(NI,N) : node(NI), chain_member(NI,O) } >  0 :- pos_side(N,C,O,S).
&sum{ w(NI,N) : node(NI), activated(NI,S), not chain_member(NI,C) ; w(NI,N) : node(NI), chain_member(NI,O) } <= 0 :- context(C,O), node(N), not chain_member(N,C), state(S), not pos_side(N,C,O,S).
&sum{ w(NI,N,context(C,O)) : node(NI), activated(NI,S), not chain_member(NI,C) } >  0 :- pos_side(N,C,O,S).
&sum{ w(NI,N,context(C,O)) : node(NI), activated(NI,S), not chain_member(NI,C) } <= 0 :- context(C,O), node(N), not chain_member(N,C), state(S), not pos_side(N,C,O,S).
