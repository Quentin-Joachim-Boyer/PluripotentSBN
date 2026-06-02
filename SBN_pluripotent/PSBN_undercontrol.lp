#include "PTBN_undercontrol.lp".

% Declaration du domaine des poids des sous réseaux engendrés par les contextes.
&dom{(-D)..D} = w(I,J,context(D,O)) :- node(I), node(J), context(D,O), I <= D, J <= D. % Borne potentiellement à changer.


% Déclaration de l'offset d'un noeud N sous contexte context(D,O) 
%(somme des poids des arcs entrants provenant des noeuds de contrôles activés dans le contexte).
&dom{-(Dd**2)..(Dd**2)} = offset(N, context(D,O)) :- node(N),context(D,O), N <= D, d(Dd).
&sum{offset(N,context(D,O)); -1*w(NI,N) : offset_node(NI,_,O)} = 0 :- node(N),context(D,O), N<=D.

% Contraintes assurant que la dynamique du sous réseau sous contexte 
% correspondent bien à celle d'un SBN (avec d'autres poids, mais de seuil 0).
&sum{w(NI,N,context(D,O)) : node(NI), activated(NI,S), NI <= D} >  0 :- 
    &sum{w(NI,N) : node(NI), activated(NI,S), NI <= N; offset(N, context(D,O))} >  0, node(N), state(S), context(D,O), N <= D.
&sum{w(NI,N,context(D,O)) : node(NI), activated(NI,S), NI <= D} <= 0 :- 
    &sum{w(NI,N) : node(NI), activated(NI,S), NI <= N; offset(N, context(D,O))} <= 0, node(N), state(S), context(D,O), N <= D.
