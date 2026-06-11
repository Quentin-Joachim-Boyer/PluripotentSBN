% Ce programme à pour but de subdiviser l'espace des fonctions de transition à explorer
% pour que la parallélisation de JPP empêche le processus d'atteindre la limite mémoire, 
% et puisse potentiellement accélérer le processus. 

#const fixed_sbf = 0.
#const fixed_node = 1.
#sum{2**S : fixed_state(fixed_node,S) : state(S)} = fixed_sbf.


:- not transition_function_bit(1,S), fixed_state(fixed_node, S).
:- transition_function_bit(1,S), not fixed_state(fixed_node, S).