%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Génère les SBN (i.e. les bits de ses fonctions de transition) de dimension d 
% vérifiant (au moins) un vecteur de décomposition v.
%
%
% Utilisation pour un vecteur de décomposition V0,V1,... VD en dimension D:
%   clingcon PSBN_undercontrol_insolver.lp --project 0 -c d=D -c v0=V0 ... -c vD=VD 
%
% Par défaut d = 2 et aucun vecteur n'est spécifié (énumère tous les SBNs)
%
% Le comportement pour des vecteurs de décomposition non complets 
% (<0,1,0> par exemple) est non documenté.
%
% ATTENTION ! L'utilisation en dimensions aberrantes (d > 5) nécessite une vigilance 
% particulière, et donc l'inspection des commentaires commençant par ATTENTION !   
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  INPUT  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#const d = 2.

% ATTENTION ! Il faut ajouter les prédicats, constantes et contraintes 
% qui vont bien pour l'utilisation en dimensions aberrantes.
#const v0 = -1. #const v1 = -1. #const v2 = -1.
#const v3 = -1. #const v4 = -1. #const v5 = -1.
:- v0 >= 0, not v(0,v0).
:- v1 >= 0, not v(1,v1).
:- v2 >= 0, not v(2,v2).
:- v3 >= 0, not v(3,v3).
:- v4 >= 0, not v(4,v4).
:- v5 >= 0, not v(5,v5).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  OUTPUT  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Arbre de decomposition etiquete : le post-traitement (ClingconUtil.buildTree)
% reconstruit et serialise l'arbre a partir de ces deux predicats.
#show branch_node/4.
#show leaf_node/3.
% #show v/2.
#show transition_function_bit/2.

% Décommenter pour afficher le vecteur de décomposition
% (peut être utile si on ne l'a pas spécifié dans les constantes).
% #show v/2. 

&show{w/2}.

 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Déclaration de la STRUCTURE.

% Noeuds du réseau.
node(1..d).

% Déclaration de la borne des poids du réseau et de leur domaine. En dimension 
% raisonnable elle est donnée par un calcul indépendant. 
% ATTENTION ! En dimensions aberrantes la borne des poids suffisante à l'obtention 
% de toutes les SBFs est inconnue, l'utilisation de d ne garantie rien du tout .
w_bound(1,1). w_bound(1,2). w_bound(2,3). w_bound(3,4). w_bound(5,5).
wb(Wb) :- w_bound(Wb,d).
&dom{(-Wb)..Wb} = w(I,J) :- node(I), node(J), wb(Wb).


% Déclaration de la DYNAMIQUE. 
state(0..2**d-1).
activated(N,S) :- node(N), state(S), (S / 2**(N-1)) \ 2 = 1.


transition_function_bit(N,S) :- node(N), state(S),
    &sum{ w(NI,N) : node(NI), activated(NI,S) } > 0.

% Vecteur de decomposition = compte des feuilles par dimension.
v(D, N) :- D = 0..d, N = #count{ Ctx,CtxOn :  leaf_node(D,Ctx,CtxOn)}.

%%%%%%%%%%%%%%%%%%%%%%%%%% DECLARATION ARBRE DANS LE SOLVEUR %%%%%%%%%%%%%%%%%%%%%%%%%%

tree(d, nil, nil).
{ leaf_node(D, Ctx, CtxOn) } :- tree(D, Ctx, CtxOn).
1 { branch_node(N, D, Ctx, CtxOn) : node(N), not ctx_chain(N,_,Ctx) } 1 :- tree(D, Ctx, CtxOn), not leaf_node(D, Ctx, CtxOn), D >= 1.
:- tree(D, Ctx, CtxOn), not leaf_node(D, Ctx, CtxOn), not branch_node(_, D, Ctx, CtxOn).

ctx_chain(N, SubCtx,c(N,SubCtx)) :- tree(_,c(N,SubCtx),_).
ctx_chain(N,SubSubCtx,Ctx) :- ctx_chain(_,c(N,SubSubCtx),Ctx).

ctxon_chain(N,SubCtxOn,c(N,SubCtxOn)) :- tree(_,_,c(N,SubCtxOn)).
ctxon_chain(N,SubSubCtxOn,CtxOn) :- ctxon_chain(_,c(N,SubSubCtxOn),CtxOn).

tree(D-1,c(ControlN,Ctx),CtxOn):- branch_node(ControlN, D, Ctx, CtxOn).
tree(D-1,c(ControlN,Ctx),c(ControlN,CtxOn)):- branch_node(ControlN, D, Ctx, CtxOn).


%%%%%%%%%%%%%%%%%%%%% CONTRAINTES DE NOEUD DE CONTROLE %%%%%%%%%%%%%%%%%%%%%%%%%%%

% Variables auxiliaires : pos_w(I,J) = max(0,w(I,J)), neg_w(I,J) = min(0,w(I,J)).
&dom{0..Wb}    = pos_w(I,J) :- node(I), node(J), wb(Wb).
&dom{-(Wb)..0} = neg_w(I,J) :- node(I), node(J), wb(Wb).
1 { pw_pos(I,J) ; pw_zero(I,J) } 1 :- node(I), node(J).
&sum{ pos_w(I,J) ; -1*w(I,J) } = 0 :- pw_pos(I,J).
&sum{ pos_w(I,J) }              = 0 :- pw_zero(I,J).
&sum{ pos_w(I,J) ; -1*w(I,J) } >= 0 :- node(I), node(J).
1 { nw_neg(I,J) ; nw_zero(I,J) } 1 :- node(I), node(J).
&sum{ neg_w(I,J) ; -1*w(I,J) } = 0 :- nw_neg(I,J).
&sum{ neg_w(I,J) }              = 0 :- nw_zero(I,J).
&sum{ neg_w(I,J) ; -1*w(I,J) } <= 0 :- node(I), node(J).

% ATTENTION clingcon : ctx_chain/ctxon_chain descendent du choix { leaf_node },
% donc sont interdits comme CONDITION d'un &sum ("invalid sum constraint").
% Mais l'appartenance d'un noeud a une chaine est inscrite dans le TERME
% lui-meme (c(2,c(1,nil)) contient 1 et 2) : on la precalcule au grounding par
% le predicat SYNTAXIQUE deterministe chain_member/2, utilisable, lui, en
% condition de &sum. Chaines de noeuds distincts generees avec l'ensemble
% porte en masque de bits M (recursion positive, stratifiee, terminaison
% garantie par M < 2**d ; une version recursive avec negation boucle au
% grounding). Egalement utilise par PSBN_undercontrol_taggedtree.lp.
chain(nil, 0).
chain(c(N,C), M + 2**(N-1)) :- chain(C,M), node(N), (M / 2**(N-1)) \ 2 = 0.
chain_member(N,C) :- chain(C,M), node(N), (M / 2**(N-1)) \ 2 = 1.

% Contribution de chaque noeud I (membres(CtxOn) inclus dans membres(Ctx),
% CN hors de Ctx par construction du choix branch_node) :
%   offset (I dans CtxOn) -> w(I,CN) ; externe (I hors Ctx, I != CN) ->
%   pos_w/neg_w ; pour la desactivation, I=CN (soi) -> w(CN,CN).

% Non activation externe :  sum_offset w(I,CN) + sum_ext pos_w(I,CN)  <= 0
&sum{ w(I,CN)     : node(I), chain_member(I,CtxOn) ;
      pos_w(I,CN) : node(I), I != CN, not chain_member(I,Ctx) } <= 0
    :- branch_node(CN,_,Ctx,CtxOn).

% Non desactivation externe : sum_offset w(I,CN) + sum_ext neg_w(I,CN) + w(CN,CN)  > 0
&sum{ w(I,CN)     : node(I), chain_member(I,CtxOn) ;
      neg_w(I,CN) : node(I), I != CN, not chain_member(I,Ctx) ;
      w(CN,CN) } > 0
    :- branch_node(CN,_,Ctx,CtxOn).


