#include "PSBN_undercontrol.lp".

transition_function_bit(N,S,context(D,O)) :- node(N), state(S), context(D,O), N<=D, &sum{w(NI,N,context(D,O)) : node(NI), activated(NI,S), NI <= D} >  0.

different_bit(N,S,control_node(CN,nil)) :- node(N), state(S), control_node(CN,nil), N < CN, 
    1 {transition_function_bit(N,S); transition_function_bit(N,S,context(CN-1,c(CN,nil)))} 1.

different_bit(N,S,control_node(CN,c(N1,O1))) :- node(N), state(S), control_node(CN,c(N1,O1)), N < CN, 
    1 {transition_function_bit(N,S,context(CN,c(N1,O1))); transition_function_bit(N,S,context(CN-1,c(CN,c(N1,O1))))} 1.

:- not 1 {different_bit(N,S,control_node(CN,O)): node(N), state(S), N < CN }, control_node(CN,O).

% :- not &sum{w(1,1)}=2.
% :- not &sum{w(1,2)}=1.
% :- not &sum{w(1,3)}=0.

% :- not &sum{w(2,1)}=3.
% :- not &sum{w(2,2)}=1.
% :- not &sum{w(2,3)}=0.

% :- not &sum{w(3,1)}= -1.
% :- not &sum{w(3,2)}=0.
% :- not &sum{w(3,3)}=1.

#show different_bit/3.
#show context/2.
#show transition_function_bit/3.
#show control_node/2.
&show{offset/2}.
&show{w/3}.