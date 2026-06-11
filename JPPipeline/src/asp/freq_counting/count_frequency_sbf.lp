% INPUT : encodage décimal des fonctions de transition, borne des poids.
% OUTPUT clingo : SBNs de poids bornés vérifiant la fonction de transition donnée.
% OUTPUT Approxasp : Leur nombre.

#const f_1 = 0.

fixed_f(1, f_1).

% Dimension de travail
#const d = 3.

% Borne de l'espace des poids Wb pour la dimension d. Données via un calcul
% indépendant (Cf rapport).
% Pour d > 5, d n'est pas nécéssairement suffisant pour obtenir toutes les SBF
% (et donc tous les SBN), mais il est difficile d'assurer une borne pour ces dimensions.
w_bound(1,1). w_bound(1,2). w_bound(2,3). w_bound(3,4). w_bound(5,5).
w_bound(d,d) :- d > 5.

% Contrainte bit à bit : le bit S de fixed_f(N,F) doit coïncider avec
% transition_function_bit(N,S).
:- node(1), fixed_f(1,F), state(S), (F / (2**S)) \ 2 = 1, not transition_function_bit(1,S).
:- node(1), fixed_f(1,F), state(S), (F / (2**S)) \ 2 = 0,     transition_function_bit(1,S).

% Declaration des noeuds.
node(1..d).

% Declaration des états du graphes de transition.
state(0..2**d-1).

% association d'un poids (de valeur V) à l'arc N1-1.
{w(N1,1,V): V =(-Wb)..Wb} = 1 :- node(N1), w_bound(Wb,d).


#sum {2**(N-1) : activated(N,S) : node(N)} = S :- state(S).


transition_function_bit(N,S) :- node(N), state(S), #sum {V,NI:w(NI,N,V),node(NI),activated(NI,S)} > 0.

% Independent support pour approxasp : les assignations de poids determinent
% uniquement tout le reste.
#show w/3.