% 16-12-2023 reprise avec une modélisation différentes des fonctions partielles : cette fois d'arité constante mais avec un suffixe fixé par le chemin de controle. On évite ainsi de formaliser les fonctions partielles autrement que comme des fonctions totales operant sur des chemins de controle.

% 27-04-2024. Révision des commentaires.
% 13-05-2024. Révision des commentaires.
% 8-07-2024. correction K = 0..D


%%% Predicates:  entry_cont/3, entry_cont/2,suf_entry/2, entry/1 %%%%%%%%%%%%%%%%%%%

% entry_cont(Cont_path, E, E_var) : E is an entry whose suffix is fixed by the control path Cont_path and whose prefix is E_var. Example:  D = 3, Cont_path = c(1, c(0, nil)). As E = E1 * 2**0 + E_2 * 2**1 + E_3* 2 **2 (or <E_1, E_2, E_3>) then E_3 = 0, E_2 = 1 and E_1 is free. It results that E = E_1 + 2 * E_2 + 4 * E_3 , and then for E_1 = 1, we have E = 1 + 2 * 1 + 4 * 0 = 3, for E_1 = 0, we have E = 0 + 2 * 1 + 4 * 0 = 2. Note that E = E1 + (2 **1)* (E_2 + E_3 * 2**1) where E_2 + E_3 * 2**1 is the entry corresponding to the control path c(E_2, c(E_3, nil)) = c(1, c(0, nil)) and that E_var = E1.
entry_cont(Cont_path, E, E_var) :-  d(D), cont_path(K, Cont_path),
			suf_entry(Cont_path, E_cont),
			E_var = 0..2**(D-K)-1,
			E = E_var + 2**(D-K) * E_cont.

entry_cont(Cont_path, E) :-  entry_cont(Cont_path, E, _).
			
% suf_entry(Cont_path, E_cont) : E_cont is the entry corresponding to the control path Cont_path			
suf_entry(nil, 0).
suf_entry(c(V_c, Cont_pathp), V_c + 2* E_contp) :- V_c =0..1,
					cont_path(_, Cont_pathp),
					suf_entry(Cont_pathp, E_contp).			

% entry(E) : E is an entry of dimension D .
entry(0.. (2**D)-1) :- d(D).


%%%%%%%%%%%%Predicate: node/1, funct/2, linear variables: bit/2, bf_node/1, bf_decomp/2 %%%%%%%%%%

%node(N) : number of a node (for non void networks of dimension > 0)
node(1..D) :- d(D).

% bf_node(N) : the integer representation of the Boolean function with D variables x_1, ..., x_D attached to the node N ( 1 <= N, N <= D). 
%for D = 2, we get the decomposition (truth table) of a function with two variables x_1, x_2  :
% bf_node(N) = bit(N, (2**2)-4) * 2**0  + bit(N, (2**2)-3) * 2**1 + bit(N, (2*2)-2) * 2**2 + bit(N, (2**2)-1) * 2**3. 
% The number of possible entries is 2**(D=2) = 4, ranging from 0..(2**D)-1 = 0..3
% The number of functions is 2**2**(D=2) = 2**4 = 16, ranging from 0..2**(2**D)-1 = 0..15
% This means that the application of this function to the entry <0,1> = 2 gives bit(N, 2).
% A void network is represented by a set of constant functions.
&dom{0..2**(2**D)-1} = bf_node(N) :- d(D), node(N).
&sum{bf_node(N)} = bf_decomp(N, (2**D)-1) :- d(D), node(N).

% funct(N, V): V is the value of the function attributed to the node N. Introduced to get the unique possible models of the networks satisfying the requirement of the decomposition vector, thanks to the option --project which operates only on predicates. 

 funct(N, V) :- &sum{bf_node(N)} = V, node(N), d(D),  V = 0..2**(2**D)-1.
% funct(N, V) :- &sum{bf_node(N)} = V, node(N), d(D),  V = 0..2**(2**(D-1))-1. %au rabais
% tous_function :- D{funct(N, V) : node(N) , V = 0..2**(2**D)-1 }D ; d(D).
% :- not tous_function.
% funct_cp(N, V, Cont_path): V is the value of the function attributed to the node N in the network reachable by Cont_path. Idem : introduced to get projected models with option --project . 
% funct_cp(N, V, Cont_path) :-  node(N), d(D),
%			cont_path(K, Cont_path),
%			dec_emb(D-K, Cont_path),  V = 0..2**(2**D)-1,
%			&sum{bf_node(N, Cont_path)} = V.

% bf_decomp(N, Nb_e) : the integer value of a partial decomposition of a Boolean function giving the values bit(N, i) for the entries i, 0<= i <= Nb_e, with 0<= Nb_e <= 2**D-1, attached to a node N in a polyhedron of dimension D (Nb_e is for number of entries).
% For D = 2 :
% 0 <= Nb_e <= 2**D-1 = 3,
% bf_decomp(N, Nb_e) = bit(N, 0) * 2**0  + bit(N, 1) * 2**1 + ... + bit(N, Nb_e) * 2**Nb_e
% Note that this value is less or equal to (2**(Nb_e +1)) -1, for example for Nb_e = 2 this bound is 2**(2 + 1)-1 = 7, for Nb_e = 3 this bound is 15..
&dom{0..2**(Nb_e +1)-1} = bf_decomp(N, Nb_e) :- node(N), d(D),
			Nb_e = 0..(2**D) -1.

&sum{bf_decomp(N, 0)} = bit(N, 0) :- node(N).
&sum{bf_decomp(N, Nb_e) ; -bit(N, Nb_e) * (2**Nb_e) ; -bf_decomp(N, Nb_e-1)} = 0 :- 
				node(N), d(D), 
				1 <= Nb_e, Nb_e = 0..(2**D)-1.
				
% bit(N, E) : Boolean value of the function associated to node N for the entry E.
&dom{0..1} = bit(N, E) :- node(N), entry(E).


%%%%%%%%%% predicates : bf_node/2, bf_nod1/2  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Determination des représentations entières des sous-fonctions booleennes

%bf_node(N, Cont_path) : the integer representation of the Boolean function with D-K variables x_1, ..., x_(D-K) attached to the node N ( 0 <= N, N <= D-K) for EMBEDDED networks reachable with Cont_path of size K, K = 0..D.
&dom{0..2**(2**(D-K))-1} = bf_node(N, Cont_path) :- 
				d(D), N = 0..D-K, K = 0..D,
				dec_emb(D-K, Cont_path).
				
&sum{bf_node(N, Cont_path) ; - bf_node1(N, Cont_path) } = 0 :- 
				d(D), N = 0..D-K, K = 0..D, 
				dec_emb(D-K, Cont_path).
				
%bf_node1(N, Cont_path) : the integer representation of the Boolean function with D-K variables x_1, ..., x_(D-K) attached to the node N ( 0 <= N, N <= D-K) for NOT NECESSARILY EMBEDDED networks reachable with Cont_path of size K, K = 0..D.
&dom{0..2**(2**(D-K))-1} = bf_node1(N, Cont_path) :- 
				d(D), N = 0..D-K, K = 0..D,
				cont_path(K, Cont_path).
%case K = 0		
&sum{bf_node1(N, nil)} = bf_node(N) :- node(N).
% case K = 1..D
&sum{bf_node1(N, Cont_path); 
-(bf_node1(N, c(0, Cont_path)) + 2**(2**(D-K))* bf_node1(N, c(1, Cont_path)))} = 0 :-
		node(N), d(D),
  		 K = 1..D, N = 0..D-K,
   		cont_path(K-1, Cont_path).



%%% Closure constraints. Predicates:  no_closure/2, no_any_closure_level/4, no_cc_level/4%%%%%%%

% no_closure(K, Cont_path) : the interaction graph of the subnetwork of dimension D-K, lying on the polyhedron reached by the control path Cont_path of size K (0 < K, K <= D)  targets a state outside this polyhedron. Then this network does not respect the closure constraints.
% Example for an embedded network in a cube lying on a segment : D = 3, K = 2, Cont_path = c(0, c(1, nil)).
% Note that for K = 0 then Cont_path = nil, therefore no_closure(0, nil) must not be true since the polyhedron of dimensio D-0 = D is the global one : every network lying on it respects the closure constraints. That it why we can state 0 < K.
% Note that for K = D, we get a polyhedron reduced to a point, i.e. with a void network lying on it (recall : represented by a set of constant functions).
no_closure(K, Cont_path) :- d(D), K = 0..D,
			no_any_clos_level(K, Cont_path, Cont_path).

% no_any_clos_level(K, Cont_path, Cont_path_0) : (for not any closure constraints from this level) the interaction graph of the subnetwork in the polyhedron P_0 reached by the control path Cont_path_0, contained in the polyhedron P of dimension D-K reached by the control path Cont_path of dimension D-K, targets at least one state of P outside P_0.
% Same example: D = 3, K = 2, Cont_path = c(0, c(1, nil)), K_0 = 2, Control pathp = c(1, nil). If the interaction graph of the network R_0 lying on the segment reachable with c(0, c(1, nil)) targets a state of the surface reachable by c(1, nil) outside of those of the segment, then R_0 does not satisfy the closure constraints. 
% The same for tagerting a state of the suffix nil of c(1, nil) representing the cube. This last case is only checked if the first one does not lead to a constraint closure failure. 
no_any_clos_level(K, Cont_path, Cont_path_0) :- d(D), 0 < K, K <= D,  
				K <= K_0, K_0 <= D,
				cont_path(K, Cont_path), cont_path(K_0, Cont_path_0),
				no_cc_level(K, Cont_path, Cont_path_0).

no_any_clos_level(K, Cont_path, Cont_path_0) :- d(D), 0 < K, K <= D,  
				K <= K_0, K_0 <= D,
				cont_path(K, Cont_path), cont_path(K_0, Cont_path_0),
				not no_cc_level(K, Cont_path, Cont_path_0),
				Cont_path = c(_, Cont_pathp),
				no_any_clos_level(K-1, Cont_pathp, Cont_path_0).
				
% no_cc_level(K, Cont_path, Cont_path_0) : (for no closure constraint due to the level) the interaction graph of the network R_0 lying on the polyhedron P_0 reached with Cont_path_0, contained in the polyhedron P of dimension D-K reached with the control path Cont_path, targets at least one state of P outside of those of P_0 and those of dimension less than D-K containing P_0  .            
% Example D=3, K=2, Cont_path = Cont_path_0 = c(0, c(1, nil)), V_c = 0 , K_0 = 2, D-K_0 = 3-2 = 1. Then R_0 relies on only one variable x_1 and lies on a segment. The considered closure constraint asks for considering the application of f_2 to entries (x_1, 0, 1) which are states of P_0 since the value of Cont_path_0 implies that x_2 = 0 and x_3 = 1. Both f_2(0, 0, 1) and f_2(1, 0, 1) should be equal to the value x_2 = 0 : that is required for avoiding that R_0 (lying on the segment) reaches any state of the surface S reachable with c(1, nil)) exept those of the segment.
% It is implemented by constructing an entry (x_1, 0, 1) as an entry E whose suffix is Cont_path_0. The node 2 is the one with rank D-(K-1) = 3-(2-1) = 2 since K = 2.
% For Cont_path = c(1, nil) then both f_3(0, 0, 1) and f_3(1, 0, 1) should be equal to the value x_3 = 1 required by Cont_path for avoiding that R_0 reaches any state of the cube (reachable by nil) outside those of the surface S and of the segment. 
% The entries are constructed in the same way but this time the node is 3-(1-1)= 3 since K = 1.

no_cc_level(K, Cont_path, Cont_path_0) :- d(D), 0 < K, K <= D, 
		0 < K_0, K <= K_0, 
		cont_path(K, Cont_path), cont_path(K_0, Cont_path_0),
		Cont_path = c(V_c, _), V_c = 0..1,
		entry_cont(Cont_path_0, E), % E: an entry with suffix Cont_path_0
		&sum{bit(D-(K-1), E)} != V_c.
		
	



























