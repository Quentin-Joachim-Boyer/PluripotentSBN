% INPUT : encodage décimal des fonctions de transition, borne des poids.
% OUTPUT clingo : SBNs de poids bornés vérifiant la fonction de transition donnée.
% OUTPUT Approxasp : Leur nombre.

% #const f_1 = 0.
% #const f_2 = 0.
% #const f_3 = 0.
% #const f_4 = 0.
% #const f_5 = 0.
% #const f_6 = 0.

% fixed_f(1, f_1).
% fixed_f(2, f_2).
% fixed_f(3, f_3).
% fixed_f(4, f_4).
% fixed_f(5, f_5).
% fixed_f(6, f_6).

% Dimension de travail
#const d = 3.

% Borne de l'espace des poids. 
#const w_bound = 3.
% (La valeur par défaut d ne garantie pas nécessairement l'obtention 
% de tout les fonctions de transition en dimension d>5)

% Contrainte bit à bit : le bit S de fixed_f(N,F) doit coïncider avec
% transition_function_bit(N,S).
% :- node(N), fixed_f(N,F), state(S), (F / (2**S)) \ 2 = 1, not transition_function_bit(N,S).
% :- node(N), fixed_f(N,F), state(S), (F / (2**S)) \ 2 = 0,     transition_function_bit(N,S).

% Declaration des noeuds.
node(1..d).

% Declaration des états du graphes de transition.
state(0..2**d-1).

% association d'un poids (de valeur V) à l'arc N1-1.
{w(N1,1,V): V =(-w_bound)..w_bound} = 1 :- node(N1).


#sum {2**(N-1) : activated(N,S) : node(N)} = S :- state(S).


transition_function_bit(N,S) :- node(N), state(S), #sum {V,NI:w(NI,N,V),node(NI),activated(NI,S)} > 0.
transition_function_bit_1(S) :- state(S), transition_function_bit(1,S).

% Independent support pour approxasp : les assignations de poids determinent
% uniquement tout le reste.
#show transition_function_bit_1/1.
% #show w/3.