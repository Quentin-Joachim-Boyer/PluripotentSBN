% 12-06-2024. Contraintes que doivent satisfaire les expressions booleennes pour être des SBF (Sign Boolean Functions) en fonction d de la dimension du réseau enchassé.
% 25-06. Dernières mises au point en rajoutant un paramètre à edge/2, à weight/2, à pos_weight_sum_cp/é

%%% edge/2, weight/2, edge/3, weight_cp/3, dec_emb/2, dec_emb/1%%%%%%%%%%%%%%%

% edge(N1, N) : there is an edge from node N1 to node N in the global network.
edge(N1,N) :- node(N), node(N1).

% weight(N1,N) : weight of the edge N1 -> N. Domain TO BE REVISED.
&dom{(-D)..(D)} = weight(N,N) :- d(D), edge(N, N).

&sum{weight(N1,N)} = weight_cp(N1, N, nil) :- edge(N1, N).

% edge_cont(N1, N, Cont_path) : there is an edge from node N1 to node N in the embedded network reachable by Cont_path.
edge_cont(N1, N, Cont_path) :- d(D), K = 0..D,
				edge(N1, N), dec_emb(D-K, Cont_path), 
				N1 <= D-K, N <= D-K.

% weight_cp(N1,N, Cont_path) : weight of the edge N1 -> N, depending of the control path Cont_path that reaches the support of the network (global or embedded). Domain TO BE REVISED.
&dom{-(D-K)..D-K} = weight_cp(N1, N, Cont_path) :- d(D),  K= 0..D,
					cont_path(K, Cont_path), 
					edge_cont(N1, N, Cont_path),
					dec_emb(Cont_path).
				 
% dec_emb(D-K, Cont_path) : Cont_path is a control path of size K leading to the support of an embedded network of dimension D-K. Cont_path = nil leads to the global network.
dec_emb(D, nil) :- d(D).
dec_emb(D-K, Cont_path) :- d(D), K= 1..D, 
			cont_path(K, Cont_path), 
			dec_cont1(D-K, Cont_path, c(1,Dec_vec)).
			
dec_emb(Cont_path) :- d(D), K= 0..D, cont_path(K, Cont_path), 
			dec_emb(D-K, Cont_path).

%%% pos_weight_sum_cp/3 %%%%%%%%%%%%%%

% pos_weight_sum_cp(E, N, Cont_path) : equal to 1 if the sum weight_sum_cp(E, N, Cont_path)  is positive and 0 otherwise.
&dom{0..1} = pos_weight_sum_cp(E_var, N, Cont_path) :-
				N = 0..D, d(D),  
				entry_cont(Cont_path, _, E_var), 
				dec_emb(Cont_path).
% case node(N)				
&sum{pos_weight_sum_cp(E_var, N, Cont_path)} = 1 :- 
				entry_cont(Cont_path,_, E_var), node(N), 
				dec_emb(Cont_path), 
				&sum{weight_sum_cp(E_var, N, Cont_path)} > 0.
&sum{pos_weight_sum_cp(E_var, N, Cont_path)} = 0 :- 
				entry_cont(Cont_path,_,  E_var), node(N),
				dec_emb(Cont_path), 
				&sum{weight_sum_cp(E_var, N, Cont_path)} <= 0.
% case N= 0
&sum{pos_weight_sum_cp(E_var, 0, Cont_path)} = 0 :- 
				entry_cont(Cont_path,_,  E_var), 
				cont_path(D, Cont_path), d(D),
				dec_emb(Cont_path). 
								
				
%%%%%%% weight_sum_cp/3, inc_weight_sum_cp/4   %%%%%%%%%%%
				
% weight_sum_cp(E, N, Cont_path) : sum of all the weight_cp(N_i, N, Cont_path) where i is an index on the binary representation BE of the entry E such that BE_i = 1.
%Exp : if D = 3, E = 3 (bolean vector <1, 1, 0>) then weight_sum_cp(E, N, nil) = weight_cp(1, N, nil) + weight_cp(2, N, nil) for N = 1..3. 
% Defined recursively from inc_weight_sum_cp(E, N, J) with J >= 0, J<= d where J represents a node.
&dom{-(D-K)*(D-K)..(D-K)*(D-K)} = weight_sum_cp(E_var, N, Cont_path) :- 
				entry_cont(Cont_path, _, E_var), 
				node(N), d(D), K= 0..D, N <= D-K,
				dec_emb(D-K, Cont_path).
				
&sum{weight_sum_cp(E_var, N, Cont_path) ; - 
	inc_weight_sum_cp(E_var, N, Cont_path, D-K)} = 0 :- 
			entry_cont(Cont_path, _, E_var), 
			node(N), d(D), K= 0..D, N <= D-K,
			dec_emb(D-K, Cont_path).
						
% inc_weight_sum_cp(E, N, Cont_path, J) : sum accordingly to the entry E of the pondered weight_cp(N_i, N, Cont_path) with 1 <= N_i, N_i <= J. 
% Example :For J = D = 3, E =<1, 0, 1> = 5 then E >= 2**2 , recursion applies to J = 2 and E = (5 - 2**2) = 1. Then for J = 2, E = <1, 0> = 1, recursion applies to J=1 and E = <1> = 1. Then for J = 1, E = <1> >= 2**0, recursion applies to J = 0 and E = (1 - 2**0) = 1.
&dom{-((D-K)*J)..((D-K)*J)} = inc_weight_sum_cp(E, N, Cont_path, J) :- d(D), 
					edge_cont(J, N, Cont_path), K = 0..D, 
					E = 0..(2**J)-1, dec_emb(D-K, Cont_path).
					
&sum{inc_weight_sum_cp(0, N, Cont_path, 0)} = 0 :- node(N), dec_emb(Cont_path) .
&sum{inc_weight_sum_cp(E, N, Cont_path, J) ; 
		-inc_weight_sum_cp(E, N, Cont_path, J-1)} = 0 :-
	edge_cont(J, N, Cont_path), 
	E = 0..(2**J)-1, E < 2**(J-1), dec_emb(Cont_path).
&sum{inc_weight_sum_cp(E, N, Cont_path, J) ; 
	-inc_weight_sum_cp(E-2**(J-1), N, Cont_path, J-1);
	- weight_cp(J, N, Cont_path) } = 0 :-
	 edge_cont(J, N, Cont_path), 
	E = 0..(2**J)-1, E >= 2**(J-1), dec_emb(Cont_path).
		
%%%%% Integrity constraints between pos_weight_sum(E, N, Cont_path) and bit(N, E) 
%%%%%%%%%% for embedded netxworks%%%%%

% To insure that the only acceptable Boolean functions defining the global network and the embedded networks are SBF functions : value of  pos_weight_sum_cp(E_var, N, Cont_path) must be equal to bit(N, E) where E have as prefix E_var and suffix Cont_path, for all Cont_path leading to an embedded network. That is, a set of weights associated to Boolean functions of each node for each embedded network must exist which satifies the required inequalities.

% case where node(N).
 &sum{pos_weight_sum_cp(E_var, N, Cont_path)} = bit(N, E) :- 
 	node(N), N <= D-K, d(D), K = 0..D, 
 	dec_emb(D-K, Cont_path),
 	entry_cont(Cont_path, E, E_var).
 	
% case constant network where N = 0, K = D, /Cont_path/ = D
&sum{pos_weight_sum_cp(E_var, N, Cont_path)} = bit(1, E) :-
	N = 0, d(D), K = D, 
 	dec_emb(D-K, Cont_path),
 	entry_cont(Cont_path, E, E_var).
 	

 
 %%%  Checking the inequality between an embedded network and any other embedded network of same dimension %%%%%%
 
% dif_faces(Cont_path, Cont_pathp)) : the embedded network on the face reached by Cont_path is different from that one reached by Cont_pathp different of Cont_path. It means that there exists at least one node N with a different boolean equation for these networks. Note that N = 1..D-K.
 
 dif_faces(Cont_path, Cont_pathp) :- N = 1..D-K, d(D), K = 1..D, 
 	dec_emb(D-K, Cont_path), cont_path(K, Cont_path),
 	dec_emb(D-K, Cont_pathp), cont_path(K, Cont_pathp),
 	&sum{bf_node(N, Cont_path)} !=  bf_node(N, Cont_pathp).
 	
:- not dif_faces(Cont_path, Cont_pathp), 
	d(D), K = 1..D, 
	dec_emb(D-K, Cont_path), cont_path(K, Cont_path),
 	dec_emb(D-K, Cont_pathp), cont_path(K, Cont_pathp),
 	Cont_pathp != Cont_path.
 	
 	
%* A l'etude
 	
%%%  Checking (03-2026) the inequality between an embedded network and any other embedded network of same dimension %%%%%%
 
% eq_faces(Cont_path, Cont_pathp)) : the embedded network on the face reached by Cont_path is different from that one reached by Cont_pathp different of Cont_path. It means that there exists at least one node N with a different boolean equation for these networks. Note that N = 1..D-K.
 
% eq_faces(Cont_path, Cont_pathp) :- N = 1..D-K, d(D), K = 1..D, 
% 	dec_emb(D-K, Cont_path), cont_path(K, Cont_path),
% 	dec_emb(D-K, Cont_pathp), cont_path(K, Cont_pathp);
% 	clause(N,C, L_pp, S, Cont_path)
%	&sum{bf_node(N, Cont_path)} !=  bf_node(N, Cont_pathp).
 	
:-	clause(N,C, L, S, Cont_path) : clause(N,C, L, S, Cont_pathp);
	clause(N,C, L, S, Cont_pathp) : clause(N,C, L, S, Cont_path);
	N = 1..D-K,
	d(D), K = 1..D, 
	dec_emb(D-K, Cont_path), cont_path(K, Cont_path),
 	dec_emb(D-K, Cont_pathp), cont_path(K, Cont_pathp),
 	Cont_pathp != Cont_path;
 	clause(N,C, L, S, Cont_path) : clause(N,C, L, S, Cont_pathp);
	clause(N,C, L, S, Cont_pathp) : clause(N,C, L, S, Cont_path);
	constant(N, V, Cont_path) : constant(N, V, Cont_pathp);
	constant(N, V, Cont_pathp) : constant(N, V, Cont_path).

 *%%%Fin etude
	
%%%% A VOIR : minimisation des SBF obtenues et  aussi 1 seule solution SBF par fonction booleenne (à faire en Python ?). Avec show sur bf_node ca devrait marcher même si c'est couteux  ! Voir cautious ?
%%%%% A VOIR : tabuler les valeurs entières des SBFs de niveau bas (1, 2) et faire les contraintes d'intégrité correspondantes pour les functions booleenes partielles de ces niveaux.
	
	
	
	
	
	
	
	

