#include "PTBN_undercontrol.lp".

1 { witness(N,S,D,O) : node(N), state(S), context(D,O), N <= D }.
1 { viol_pos_neg(N,S,D,O) ; viol_neg_pos(N,S,D,O) } :- witness(N,S,D,O).

&sum{w(NI,N) : node(NI), activated(NI,S), NI <= N ; offset(N,context(D,O))} >  0 :- viol_pos_neg(N,S,D,O).
&sum{w(NI,N,context(D,O)) : node(NI), activated(NI,S), NI <= D}             <= 0 :- viol_pos_neg(N,S,D,O).

&sum{w(NI,N) : node(NI), activated(NI,S), NI <= N ; offset(N,context(D,O))} <= 0 :- viol_neg_pos(N,S,D,O).
&sum{w(NI,N,context(D,O)) : node(NI), activated(NI,S), NI <= D}             >  0 :- viol_neg_pos(N,S,D,O).

#show witness/4.