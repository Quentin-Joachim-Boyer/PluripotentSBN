#include "PTBN_undercontrol.lp".

leaf_node(N,O) :- btree(nil,nil,N,O).
noncontrol_node(N,LN,O) :- node(N), leaf_node(LN,O), N <= LN.

% % Contraintes assurant que le noeud N sous chaine d'activation O d'une feuille 
% % ne soit pas un noeud de contrôle.

% Une contrainte d'activation externe ou une de désactivation externe doit être vérifiée.
1 {external_activation(N,LN,O) ; external_deactivation(N,LN,O)} :- noncontrol_node(N,LN,O).

% Contrainte d'activation externe. 
&sum{w(ON,N) : offset_node(ON,_,O) ; pos_w(I,N) : node(I), I <= LN, I != N} > 0 :- external_activation(N,LN,O).
% Variable auxiliare : pos_w(I,J) = max(0,w(I,J)) pour un noeud feuille en cas d'activation externe.
&dom{0..D} = pos_w(I,N) :- node(I),external_activation(N,LN,_), d(D), I <= LN, I != N.
1 { decision_pos_w_pos(I,N) ; decision_pos_w_zero(I,N) } 1 :- node(I), external_activation(N,LN,_), I <= LN, I != N.
&sum{pos_w(I,N) ; -1*w(I,N)} = 0 :- decision_pos_w_pos(I,N).
&sum{pos_w(I,N)}               = 0 :- decision_pos_w_zero(I,N).
&sum{pos_w(I,N) ; -1*w(I,N)} >= 0 :- node(I),external_activation(N,LN,_), d(D), I <= LN, I != N.

% Contrainte de désactivation externe.
&sum{w(ON,N) : offset_node(ON,_,O) ; neg_w(I,N) : node(I), I <= LN, I != N ; w(N,N)} <= 0 :- external_deactivation(N,LN,O).
% Variable auxiliaire : neg_w(I,J) = min(0,w(I,J)) pour un noeud feuille en cas de desactivation externe.
&dom{-(D)..0} = neg_w(I,N) :- node(I),external_deactivation(N,LN,_), d(D), I <= LN, I != N.
1 { decision_neg_w_neg(I,N) ; decision_neg_w_zero(I,N) } 1 :- node(I), external_deactivation(N,LN,_), I <= LN, I != N.
&sum{neg_w(I,N) ; -1*w(I,N)} = 0 :- decision_neg_w_neg(I,N).
&sum{neg_w(I,N)}               = 0 :- decision_neg_w_zero(I,N).
&sum{neg_w(I,N) ; -1*w(I,N)} <= 0 :- node(I),external_deactivation(N,LN,_), d(D),I <= LN, I != N.


% :- not &sum{w(1,1)}= 3.
% :- not &sum{w(1,2)}= -3.
% :- not &sum{w(1,3)}= 0.

% :- not &sum{w(2,1)}= -3.
% :- not &sum{w(2,2)}= 0.
% :- not &sum{w(2,3)}= 0.

% :- not &sum{w(3,1)}= -3.
% :- not &sum{w(3,2)}= -3.
% :- not &sum{w(3,3)}= 1.

% #show leaf_node/2.
% #show external_activation/3.
% #show external_deactivation/3.
% #show offset_node/3.
% &show{pos_w/2}.
% &show{neg_w/2}. 

