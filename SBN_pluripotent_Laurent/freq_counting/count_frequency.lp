% INPUT : encodage décimal des fonctions de transition, borne des poids.
% (Ne fonctionne que pour d = 3 actuellement, TODO généraliser en dimension d)
% OUTPUT clingo : SBNs de poids bornés vérifiant la fonction de transition donnée.
% OUTPUT Approxasp : Leur nombre.


% Dimension de travail
#const d = 3.

% Borne de l'espace des poids. 
#const w_bound = d.
% (La valeur par défaut d ne garantie pas nécessairement l'obtention 
% de tout les fonctions de transition en dimension > 3 ou 4)

% Fixation des fonctions de transition
#const f0 = 0.
#const f1 = 0.
#const f2 = 0.

:- not transition_function(0,f0).
:- not transition_function(1,f1).
:- not transition_function(2,f2).

% Declaration des noeuds.
node(0..d-1).

% Declaration des états du graphes de transition.
state(0..2**d-1).

% association d'un poids (de valeur V) à l'arc N1-N2
{w(N1,N2,V): V =(-w_bound)..w_bound} = 1 :- node(N1),node(N2).


#sum {2**N : activated(N,S) : node(N)} = S :- state(S).


transition_function_bit(N,S) :- node(N), state(S), #sum {V:w(NI,N,V),node(NI),activated(NI,S)} > 0.
transition_function(N,X) :- node(N), X = #sum {2**S : state(S),transition_function_bit(N,S)}.
 
% L'utilisation de count_frequency.py necessite l'instruction suivante pour que le parsing fonctionne
#show.