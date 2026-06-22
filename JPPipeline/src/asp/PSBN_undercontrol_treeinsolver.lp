%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Génère les SBN (i.e. les bits de ses fonctions de transition) de dimension d 
% vérifiant (au moins) un vecteur de décomposition v, ainsi que leur permutation sur
% les noeuds.
%
% Il est possible de fixer la permutation identité pour supprimer ces permutations.
% Cf. environs de la ligne 61 (redirection instable)
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

#show transition_function_bit/2.

% Décommenter pour afficher le vecteur de décomposition 
% (peut être utile si on ne l'a pas spécifié dans les constantes).
% #show v/2. 

 
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
&dom{-Wb..Wb} = w(I,J) :- node(I), node(J), wb(Wb).

% Déclaration d'une permutation des noeuds. 
1 {sigma(N,M) : node(M)} 1 :- node(N).
1 {sigma(N,M) : node(N)} 1 :- node(M).
% :- sigma(N,M), N != M.

% Déclaration de la DYNAMIQUE. 
state(0..2**d-1).
activated(N,S) :- node(N), state(S), (S / 2**(N-1)) \ 2 = 1.


% Permutation des etats induite par sigma : sigma_state(S, S2) ou le bit (M-1) de S2
% vaut le bit (N-1) de S, avec M = sigma(N).
sigma_state(S, S2) :- state(S),
    S2 = #sum{ (2**(M-1)),N : sigma(N,M), (S / 2**(N-1)) \ 2 = 1 }.

% Dynamique permutée (la sortie).
transition_function_bit(M,S2) :- node(N), state(S), sigma(N,M), sigma_state(S,S2),
    &sum{ w(NI,N) : node(NI), activated(NI,S) } > 0.

% transition_function_bit(N,S) :- node(N), state(S),
%     &sum{ w(NI,N) : node(NI), activated(NI,S) } > 0.

% Vecteur de decomposition = compte des feuilles par dimension.
v(K, N) :- K = 0..d, N = #count{ O : leaf_node(K,O) }.

%%%%%%%%%%%%%%%%%%%%%%%%%% DECLARATION ARBRE DANS LE SOLVEUR %%%%%%%%%%%%%%%%%%%%%%%%%%

slot(d, nil).
{ leaf_node(D,O) } :- slot(D,O).
split_node(D,O) :- slot(D,O), not leaf_node(D,O), D >= 1.
:- slot(D,O), not leaf_node(D,O), not split_node(D,O).

control_node(D,O)    :- split_node(D,O).
context(D-1, c(D,O)) :- split_node(D,O), D > 1.
slot(D-1, O)         :- split_node(D,O).
slot(D-1, c(D,O))    :- split_node(D,O).

%%%%%%%%%%%%%%%%%%% CONTEXTES POSSIBLES  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

ctx_top(nil, d+1).
ctx_chain(nil).
ctx_chain(c(D,O)) :- ctx_chain(O), node(D), ctx_top(O,Tp), D < Tp.
ctx_top(c(D,O), D) :- ctx_chain(c(D,O)).

offset_node(D, c(D,O))  :- ctx_chain(c(D,O)).
offset_node(D, c(D2,O)) :- offset_node(D, O), ctx_chain(c(D2,O)).

possible_context(D-1, c(D,O)) :- ctx_chain(c(D,O)), D > 1.

possible_slot(D,O) :- ctx_chain(O), ctx_top(O,Tp), D = 0..Tp-1.

%%%%%%%%%%%%%%%%%%%%% CONTRAINTES DE NOEUD DE CONTROLE %%%%%%%%%%%%%%%%%%%%%%%%%%%

% Variables auxiliaires : pos_w(I,J) = max(0,w(I,J)), neg_w(I,J) = min(0,w(I,J)).
&dom{0..Wb}    = pos_w(I,J) :- node(I), node(J), I < J, wb(Wb).
&dom{-(Wb)..0} = neg_w(I,J) :- node(I), node(J), I < J, wb(Wb).
1 { pw_pos(I,J) ; pw_zero(I,J) } 1 :- node(I), node(J), I < J.
&sum{ pos_w(I,J) ; -1*w(I,J) } = 0 :- pw_pos(I,J).
&sum{ pos_w(I,J) }              = 0 :- pw_zero(I,J).
&sum{ pos_w(I,J) ; -1*w(I,J) } >= 0 :- node(I), node(J), I < J.
1 { nw_neg(I,J) ; nw_zero(I,J) } 1 :- node(I), node(J), I < J.
&sum{ neg_w(I,J) ; -1*w(I,J) } = 0 :- nw_neg(I,J).
&sum{ neg_w(I,J) }              = 0 :- nw_zero(I,J).
&sum{ neg_w(I,J) ; -1*w(I,J) } <= 0 :- node(I), node(J), I < J.

% Contraintes de non activation externe.
&sum{ w(ON,CN) : offset_node(ON,O) ; pos_w(I,CN) : node(I), I < CN } <= 0
    :- control_node(CN,O).

% Contraintes de non desactivation externe.
&sum{ w(ON,CN) : offset_node(ON,O) ; neg_w(I,CN) : node(I), I < CN ; w(CN,CN) } > 0
    :- control_node(CN,O).


%%%%%%%%%%%%%%%%%%%%% SOUS-RESEAUX SBN SOUS CONTEXTE %%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Déclaration des poids de tous les contextes possibles (sinon clingcon râle).
&dom{-Wb..Wb} = w(I,J,context(D,O)) :- node(I), node(J), possible_context(D,O), I<=D, J<=D, wb(Wb).
&dom{-(Wb*d)..(Wb*d)} = offset(N, context(D,O)) :- node(N), possible_context(D,O), N<=D, wb(Wb).

&sum{ offset(N,context(D,O)) ; -1*w(NI,N) : offset_node(NI,O) } = 0 :- context(D,O), node(N), N<=D.

&sum{ w(NI,N,context(D,O)) : node(NI), activated(NI,S), NI<=D } > 0 :-
    &sum{ w(NI,N) : node(NI), activated(NI,S), NI<=D ; offset(N,context(D,O)) } > 0,
    node(N), state(S), context(D,O), N<=D.
&sum{ w(NI,N,context(D,O)) : node(NI), activated(NI,S), NI<=D } <= 0 :-
    &sum{ w(NI,N) : node(NI), activated(NI,S), NI<=D ; offset(N,context(D,O)) } <= 0,
    node(N), state(S), context(D,O), N<=D.

