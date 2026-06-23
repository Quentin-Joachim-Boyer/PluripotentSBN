%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Ceci est une extension du PTBN_undercontrol_treeinsolver.lp vérifiant que les 
% sous réseaux sont effectivement des SBNs.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#include "PTBN_undercontrol_treeinsolver.lp"

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

