%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% I / O %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% INPUT : Un arbre de décomposition.

% OUTPUT clingcon : Dynamiques (projection sur les bits des fonctions de transition) 
%   de SBNs de poids bornés vérifiant un arbre de decomposition donné (décomposition en TBN).
% 
% OUTPUT Approxasp : Leur nombre


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% PARAMETRAGE %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Declaration d'un arbre de decomposition pour lancer ce programme seul.
% Il est recommandé d'utiliser les fichier setup_btree{d}d.lp pour une 
% utilisation systématique, auquel cas aucun arbre ne doit être spécifié ici.

% Dimension 1
% btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil).

% Dimension 2
% btree(btree(nil,nil,1,nil),btree(nil,nil,1,nil),2,nil).
% btree(nil,nil,2,nil).
% btree(btree(nil,nil,1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil).
% btree(btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),btree(nil,nil,1,nil),2,nil).


% Dimension 3
% btree(btree(btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil),btree(btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil),3,nil).
btree(btree(nil,nil,2,nil),btree(nil,nil,2,nil),3,nil).
% btree(nil,nil,3,nil).
% btree(btree(nil,nil,2,nil),btree(btree(nil,nil,1,nil),btree(nil,nil,1,nil),2,nil),3,nil).

% Dimension 4
% btree(btree(btree(btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil),btree(btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil),3,nil),btree(btree(btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil),btree(btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil),3,nil),4,nil).
% btree(btree(nil,nil,3,nil),btree(btree(nil,nil,2,nil),btree(btree(nil,nil,1,nil),btree(btree(nil,nil,0,nil),btree(nil,nil,0,nil),1,nil),2,nil),3,nil),4,nil).
% btree(btree(nil,nil,3,nil),btree(nil,nil,3,nil),4,nil).
% btree(btree(nil,nil,3,nil),btree(btree(btree(nil,nil,1,nil),btree(nil,nil,1,nil),2,nil),btree(btree(nil,nil,1,nil),btree(nil,nil,1,nil),2,nil),3,nil),4,nil).
% btree(btree(nil,nil,3,nil),btree(btree(nil,nil,2,nil),btree(nil,nil,2,nil),3,nil),4,nil).
% btree(nil,nil,4,nil).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% CONTRAINTES %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Dimension de Travail (du réseau principal).
d(D) :- D = #max {Dd:btree(_,_,Dd,_)}.

% Declaration des noeuds et de l'espace des états associé.
node(1..D) :- d(D).
state(0..2**D-1) :- d(D).

% Declaration de l'activation du noeud N dans l'état S.
activated(N,S) :- node(N), state(S), (S / 2**(N-1)) \ 2 = 1.

% Declaration du domaine des poids des noeuds du réseau principal.
&dom{(-D)..(D)} = w(I,J) :- node(I), node(J), d(D).

% &dom{(-D)..(0)} = w(I,J) :- node(I), node(J), d(D), I != J.
% &dom{(0)..(D)} = w(I,I) :- node(I), d(D).


% Déballage de l'arbre de décomposition. 
% (Les listes chaînées des noeuds de contrôle activés O sont ainsi générées).
btree(T11,T12,D1,O0)       :- btree(btree(T11,T12,D1,_),btree(_,_,_,_),_,O0).
btree(T21,T22,D2,c(D0,O0)) :- btree(btree(_,_,_,_),btree(T21,T22,D2,_),D0,O0).

% Déclaration des noeuds de contrôle sous chaîne d'activation O 
% et des contextes associés à leur fils droit (le gauche est forcement déjà un SBN).
context(D-1,c(D,O)) :- btree(btree(_,_,_,_),btree(_,_,_,_),D,O), D > 1.
control_node(D,O)   :- btree(btree(_,_,_,_),btree(_,_,_,_),D,O).


% Déballage de la chaîne des noeuds de contrôle activés dans un contexte.
offset_node(N,C,c(N,C)) :- context(_,c(N,C)).
offset_node(N,C,O) :- offset_node(_,c(N,C),O).

% % Contrainte assurant que le noeud CN soit bien un noeud de contrôle sous la chaîne d'activation O (Cf rapport Danwen)
% Contrainte de non activation externe.
&sum{w(ON,CN) : offset_node(ON,_,O) ; pos_w(I,CN) : node(I), I < CN} <= 0 :- control_node(CN,O), d(D).
% Variables auxiliaires : pos_w(I,J) >= max(0,w(I,J)).
&dom{0..D} = pos_w(I,J) :- node(I),control_node(J,_), d(D),I < J.
&sum{pos_w(I,J) ; -1*w(I,J)} >= 0 :- node(I),control_node(J,_), d(D),I < J.
% Contrainte de non désactivation externe.
&sum{w(ON,CN) : offset_node(ON,_,O) ; neg_w(I,CN) : node(I), I < CN ; w(CN,CN)} > 0 :- control_node(CN,O), d(D).
% Variables auxiliaires : neg_w(I,J) <= min(0,w(I,J)).
&dom{-(D)..0} = neg_w(I,J) :- node(I),control_node(J,_), d(D), I < J.
&sum{neg_w(I,J) ; -1*w(I,J)} <= 0 :- node(I),control_node(J,_), d(D),I < J.


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% OUTPUT %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Prédicats servant à l'output des bits des fonctions de transitions du reseau principal.
transition_function_bit(N,S) :- node(N), state(S), &sum{w(NI,N) : node(NI), activated(NI,S)} > 0.

% % ATTENTION : Le bout de code ci-dessous fais exploser le grouding à partir de D=4.
% % (C'est probablement dû à l'unification sur X à partir de prédicats dépendant de Clingcon)
% % Déclaration de l'encodage binaire de la fonction de transition du réseau principal.
% % transition_function(N,X) :- node(N), d(D), 
% %     X = #sum {2**S : state(S),transition_function_bit(N,S)}.


% Instruction d'affichage.
#show transition_function_bit/2.
&show{w/2}.


% Instruction d'affichage à modifier uniquement pour le débug
% #show transition_function/2.
% &show{transition_function/1}.
% #show transition_function_bit/3.
% #show offset_node/3.
% #show control_node/2.
% #show context/2.
% #show btree/4.
% #show node/2.
% #show state/1.
% #show activated/3.
% #show fixed_state/2.