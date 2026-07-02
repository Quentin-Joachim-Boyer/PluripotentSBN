%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Ceci est une extension du PTBN_undercontrol_taggedtree.lp vérifiant que les
% sous réseaux sont effectivement des SBN (et pas seulement des PTBN/TBN).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#include "PTBN_undercontrol_taggedtree.lp".

% Contexte d'un sous-réseau : (nouveau Ctx, nouveau CtxOn) engendré par la
% branche "controle activé" d'un branch_node. Contrairement à
% PSBN_undercontrol.lp (arbre en INPUT, control_node = index D fixe), ici le
% noeud de controle est choisi librement par le solveur (taggedtree), donc la
% portée du sous-réseau (les noeuds encore disponibles) n'est plus un simple
% seuil d'indice mais le prédicat choice-dépendant ctx_chain/ctxon_chain.
context(c(CN,Ctx), c(CN,CtxOn)) :- branch_node(CN,_,Ctx,CtxOn).

% Poids propres (frais) du sous-réseau, un jeu par contexte.
&dom{(-Wb)..Wb} = w(I,J,context(C,O)) :- node(I), node(J), context(C,O), wb(Wb).

% ATTENTION clingcon : ctx_chain/ctxon_chain descendent du choix { leaf_node },
% donc interdits comme CONDITION d'un &sum ("invalid sum constraint", cf.
% PTBN_undercontrol_taggedtree.lp). On passe par des copies auxiliaires
% "gelées à 0 hors champ", le choix restant dans le CORPS des règles :
%   root_scoped(I,N,C,O)   = w(I,N)         si I disponible (not ctx_chain(I,_,C)), sinon 0.
%   sub_scoped(I,N,C,O)    = w(I,N,context(C,O)) si I disponible, sinon 0.
%   offset_contrib(I,N,C,O) = w(I,N)        si I dans la chaine des controles ACTIFS (ctxon_chain(I,_,O)), sinon 0.
% N doit lui aussi être restreint aux noeuds disponibles du contexte (C,O) :
% le noeud de contrôle qui vient d'être choisi (dans ctx_chain(N,_,C)) n'est
% PLUS un noeud du sous-réseau restant, il ne doit donc PAS se voir imposer
% une cohérence de seuil ici (sinon un offset non nul devient impossible à
% satisfaire avec zéro entrée disponible -- bug détecté empiriquement : d=2
% avec 1 seul split donnait UNSATISFIABLE avant cette restriction).
&dom{(-Wb)..Wb} = root_scoped(I,N,C,O) :- node(I), node(N), context(C,O), not ctx_chain(N,_,C), wb(Wb).
&sum{ root_scoped(I,N,C,O) ; -1*w(I,N) } = 0 :- context(C,O), node(N), not ctx_chain(N,_,C), node(I), not ctx_chain(I,_,C).
&sum{ root_scoped(I,N,C,O)              } = 0 :- context(C,O), node(N), not ctx_chain(N,_,C), node(I), ctx_chain(I,_,C).

&dom{(-Wb)..Wb} = sub_scoped(I,N,C,O) :- node(I), node(N), context(C,O), not ctx_chain(N,_,C), wb(Wb).
&sum{ sub_scoped(I,N,C,O) ; -1*w(I,N,context(C,O)) } = 0 :- context(C,O), node(N), not ctx_chain(N,_,C), node(I), not ctx_chain(I,_,C).
&sum{ sub_scoped(I,N,C,O)                           } = 0 :- context(C,O), node(N), not ctx_chain(N,_,C), node(I), ctx_chain(I,_,C).

&dom{(-Wb)..Wb} = offset_contrib(I,N,C,O) :- node(I), node(N), context(C,O), not ctx_chain(N,_,C), wb(Wb).
&sum{ offset_contrib(I,N,C,O) ; -1*w(I,N) } = 0 :- context(C,O), node(N), not ctx_chain(N,_,C), node(I), ctxon_chain(I,_,O).
&sum{ offset_contrib(I,N,C,O)              } = 0 :- context(C,O), node(N), not ctx_chain(N,_,C), node(I), not ctxon_chain(I,_,O).

% Offset du noeud N sous contexte (C,O) = somme des poids racine des noeuds de
% contrôle activés menant à ce contexte (condition finale = fait node(I), donc valide).
&dom{(-Wb*d)..(Wb*d)} = offset(N,C,O) :- node(N), context(C,O), not ctx_chain(N,_,C), wb(Wb).
&sum{ offset(N,C,O) ; -1*offset_contrib(I,N,C,O) : node(I) } = 0 :- context(C,O), node(N), not ctx_chain(N,_,C).

% Cohérence dynamique : le sous-réseau (poids w(.,.,context(C,O))) doit réaliser
% exactement la même dynamique que le réseau racine restreint à ses noeuds
% disponibles, décalée de l'offset des contrôles actifs (Cf. rapport Danwen).
&sum{ sub_scoped(NI,N,C,O) : node(NI), activated(NI,S) } > 0 :-
    &sum{ root_scoped(NI,N,C,O) : node(NI), activated(NI,S) ; offset(N,C,O) } > 0,
    context(C,O), node(N), not ctx_chain(N,_,C), state(S).
&sum{ sub_scoped(NI,N,C,O) : node(NI), activated(NI,S) } <= 0 :-
    &sum{ root_scoped(NI,N,C,O) : node(NI), activated(NI,S) ; offset(N,C,O) } <= 0,
    context(C,O), node(N), not ctx_chain(N,_,C), state(S).
