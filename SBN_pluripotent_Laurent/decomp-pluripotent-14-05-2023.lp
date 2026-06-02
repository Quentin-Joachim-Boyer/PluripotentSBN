% 19-06-2022. Le résultat attendu, si le vecteur Dec_vec est donné, est l'ensemble des netww(D-K, Cont_path) et embedded(D-K, Cont_path) requis. Plus les equations du réseau avec K = 0. Ce réseau est défini complètement seulement si la décomposition est complète (ou obtenue comme une optimisation).

% Faire un module à part, extension de celui existant pour l'équivalence SBF-fonct bool, pour définir les fonctions obtenues par reccurrence pour un Cont-path donné. Ce sont des projections avec des couples de variables de controle et pour définir clos_constraint(D-K,Cont_path).

% 12-06-2023
% Mise en oeuvre de la détermination de R + réseaux enchassés selon un vecteur de decomposition <Nd,..., N0>.

% 17-07-2023 reprise du programme après avoir travaillé sur la formulation des contraintes de cloture.

% 8-09-2023 mise au point des intervalles de variation

% 22-01-2024. Tests

% 4-03-2024 Introduction de l'unicité du vecteur de decomposition.
% dec_cont1(D, Cont_path, Dec_vec)

%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% d : dimension de l'hypercube global

% K : varie de 0 à d+1, soit d + 2 valeurs, : c'est la taille du chemin de control. K=0 : un chemin vide, atteignant l' hypercube global, K = d : un chemin de taille d atteignant un point, K = d+1 : un chemin atteignant l'hypercube vide. Typiquement utilisé dans cont_path(K, Cont_path) signifiant que le vecteur Cont_path possède K valeurs, e.g. cont_path(0, nil) est vrai, et  cont_path(d, Cont_path) pour |Cont_path| = d.

% d-K : varie de d (avec K = 0) à -1 (avec K = d + 1) soit d+1 valeurs, c'est la dimension de l'hypercube courant. La taille du vecteur de décomposition courant est d-K +1 . La dimension d-(K = d) = 0 correspond à  un point. L'hypercube vide a pour dimension -1. Typiquement utilisé dans up_dec(d-K, Dec_vec) : |Dec_vec| = d-(K = 0) + 1 = d +1, |Dec_vec| = d-(K = d) + 1 = 1, |Dec_vec| = d-(K = d + 1) + 1 = 0
% L'invariant dans decomp(D-K, Cont_path, Dec_vec) est |Cont-path| + |Dec_vec| =  K + (d-K + 1) = d + 1.


 %%%%%%%%%%%%%%%%%%% The challenge. Predicates : decomp/2, dec_cont1/2 %%%%%%%%%%%%
 
% We are seeking for a pluripotent network of dimension D. It results from applying a decomposition vector Dec_vec to a global hypercube of dimension D. 
 :- not decomp(D, Dec_vec), dec_cont1(D, nil, Dec_vec), d(D).

% decomp(D, Dec_vec) : (decomposition) there is a pluripotent network of dimension D according to the decomposition vecteur Dec_vec (decomposition vector) of size D+1.
% NB. This network is given by according variables bit(N, E) giving the Boolean value of the function associated to node N for the entry E.
 decomp(D, Dec_vec) :- d(D),  decomp(D, nil, Dec_vec).


% dec_cont1(D, nil, Dec_vec) : Dec_vec is a unique decomposition vector for the global hypercube in the considered model.
1{dec_cont1(D, nil, Dec_vec) : up_dec(D, Dec_vec)}1 :- d(D). 



%%%%%%%%%%%% Decomposition vector. Predicates : up_dec/2, up_dec/3, up_dec/4, full_dec/2 %%%%%%%%%%%%%%

% up_dec(D-K, Dec_vec) : (upper bound decomposition vector) Dec_vec is a decomposition vector of size D-K+1, for a hypercube of dimension D. 
up_dec(D-K, Dec_vec) :- d(D), K = 0..D,
			 up_dec(D-K, Dec_vec, 0, W_sumN_tot), W_sumN_tot = 0..2**(D-K).
			
% up_dec(D-K, Dec_vec, W_sumN, W_sumN_tot) : Dec_vec is a decomposition vector of size D-K +1, for a hypercube of dimension D-K. W_sumN is the "weighted" sum of the inherited elements of a prefix of Dec_vec. Then W_sumN plus the first element N of Dec_vec, must be less or equal to 2**K. W_sumN_tot is the total sum of the weighted elements (those of the prefix included).
% For an empty polyhedron, Dec_vec is empty and Sum_wN and W_sumN_tot are equal.
up_dec(-1, nil, W_sumN_tot, W_sumN_tot) :- d(D), W_sumN_tot = 0..2**D.   
up_dec(D-K, c(N, Dec_vec), W_sumN, W_sumN_tot)  :- d(D), K = 0..D, 
				N = 0..2**K, W_sumN = 0..2**(K-1),
				W_sumNp = N + 2 * W_sumN,
				0 <= W_sumNp,  W_sumNp <= 2**K, 
				up_dec(D-(K+1), Dec_vec, W_sumNp, W_sumN_tot).

% up_dec(D-K, Dec_vec, W_sumN_tot) : W_sumN_tot the total sum of weighted elements of Dec_vec of dimension D-K + 1 (with an inherited weighted sum equal to 0).
up_dec(D-K, Dec_vec, W_sumN_tot) :- d(D), K = 0..D,  
				W_sumN_tot = 0..2**(D-K),
				up_dec(D-K, Dec_vec, 0, W_sumN_tot).

% full_dec(D, Dec_vec): Dec-vec is a full decomposition vector for the global hypercube of dimension D.
full_dec(D, Dec_vec) :- d(D), up_dec(D, Dec_vec, 2**D).

				
 %%% Control path vector. Predicates:  decomp/3, control_pos_neg/3, piecewise_sum/4, cont_path/2 %%%%%%

% decomp(D-K, Cont_path, Dec_vec) : there is a network of dimension D-K obtained via the control path Cont_path of dimension K with the decomposition vector Dec_vec of dimension D-K +1. Invariant : |Cont_path|+ |Dec_vec| = K + D-K + 1 = D + 1.
 % Example: 
% first step : d= 3, K = 0, Cont_path = nil,  Dec_vec = c(0, c(1, c(0, c(3, nil)))) of size 3 + 1 = 4.  
% second step ) D-K = 2, K = 1, two cases : <Cont_path = c(0, nil) , Dec_vec = c(1, c(0, c(0, nil)))> which is embedded (no successor), <Cont_path = c(1, nil) , Dec_vec = c(0, c(0, c(3, nil))> with successors.
% third step : D-K = 2, two cases : < Cont_path = c(0, c(1, nil)), Dec_vec = c(0, c(2, nil))>, < Cont_path = c(1, c(1, nil)), Dec_vec = c(0, c(1, nil))>
% fourth step 1: D-K = 0, K = 3 : < Cont_path = c(0, c(0, c(1, nil))), Dec_vec = c(1, nil)> which is embedded, < Cont_path = c(1, c(0, c(1, nil))), Dec_vec = c(1, nil)> which is embedded.
% fourth step 2 : D-K = 0, K = 3 : < Cont_path = c(0, c(1, c(1, nil))), Dec_vec = c(1, nil)> which is embedded, < Cont_path = c(1, c(1, c(1, nil))), Dec_vec = c(0, nil)> which is terminal and not embeded.

% Note :decomp(0, Cont_path, c(N, nil)) : case where D=K, is given by the two following rules .
 
% In case N = 1 an "embedded" network is attributed to the support represented by Cont_path. The decomposition does not continue because the limitations on Dec_vec (whose elements must be null due to up_dec(D-K, c(1, Dec_vec)) ). 
decomp(D-K, Cont_path, c(1, Dec_vec)) :- d(D), K = 0..D, 
			cont_path(K, Cont_path),
			dec_cont1(D-K, Cont_path, c(1, Dec_vec)).
%I n case N = O and Dec_vec is a null vector then the decomposition terminates successfully. It happens anyway in case of non full decomposition due to the definition of the decomposition vector Dec_vec. Testing this case allows to avoid to develop unnecessarily a tree of decomposition vectors with a zero prefix. The test is done by checking that the sum of weighted elements of Dec_vec is 0 (without inherited elements).
decomp(D-K, Cont_path, c(0, Dec_vec)) :-  d(D), K = 0..D,
				cont_path(K, Cont_path),
				dec_cont1(D-K, Cont_path, c(0, Dec_vec)),
				up_dec(D-K, c(0, Dec_vec), 0).								
% In case N = 0, and Dec_vec is not a null vector, two decompositions continue. The first one with the path of control Cont_path augmented with an appropriate control vector (represented by an integer) Cont_vec, and a decomposition vector Dec_vecp, part of Dec_vec. The second with the path of control Cont_path augmented with the control vector Cont_neg_vec (opposite to Cont_vec), and the decomposition vector Dec_vecpp such that Dec_vec = Dec_vecp + Dec_vecpp (vector-vector pointwise addition which could have several solutions). Avoiding redundant couples (Dec_vecp, Dec_vecpp) is insured (by breaking symmetry) by providing that the first not both null elements of Dec_vecp and Dec_vecpp are such that the one of Dec_vecp is higher or equal to that one of Dec_vecpp. The uniqueness of the couple (Dec_vecp, Dec_vecpp) in the ASP model is insured by using the predicate unique_sum/5 whose only one instance is required.
 decomp(D-K, Cont_path, c(0, Dec_vec)) :- d(D), K = 0..D,
 up_dec(D-K, c(0, Dec_vec), W_sum_N_tot), W_sum_N_tot != 0,
 dec_cont1(D-K, Cont_path, c(0, Dec_vec)),
 cont_path(K, Cont_path),
 control_pos_neg(D-K, Cont_vec, Cont_neg_vec),
 Cont_pathp = c(Cont_vec, Cont_path),
 Cont_pathpp = c(Cont_neg_vec, Cont_path),
 unique_sum(D-(K+1), Cont_path, Dec_vec, Dec_vecp, Dec_vecpp),
 decomp(D-(K+1), Cont_pathp, Dec_vecp), decomp(D-(K+1), Cont_pathpp, Dec_vecpp).

% unique_sum(D-(K+1), Cont_path, Dec_vec, Dec_vecp, Dec_vecpp) : Dec_vec is such that Dec_vec = Dec_vecp + Dec_vecpp with the appropriate conditions. This division into two parts is unique in the ASP model. The parameter Cont_path is used in the rule defining dec_cont1 
1{unique_sum(D-(K+1), Cont_path, Dec_vec, Dec_vecp, Dec_vecpp): 
 up_dec(D-(K+1), Dec_vecp, W_sum_Np_tot), 
 up_dec(D-(K+1), Dec_vecpp, W_sum_Npp_tot),
 sum_gt_first(D-(K+1), Dec_vec, Dec_vecp, Dec_vecpp), 
 W_sum_Np_tot >= W_sum_Npp_tot}1 :- 
  		d(D), K = 0..D, 
  		cont_path(K, Cont_path),
  		up_dec(D-K, c(0, Dec_vec), W_sum_N_tot), W_sum_N_tot != 0,
		dec_cont1(D-K, Cont_path, c(0, Dec_vec)).
			
% dec_cont1(D-(K+1), Cont_pathp, Dec_vecp) (resp. dec_cont1(D-(K+1), Cont_pathpp, Dec_vecpp)) : Dec_vecp and Dec_vecpp are the only decomposition vectors part of Dec_vec for the dimension D-(K+1), reached respectively by Cont_pathp and Cont_pathpp.			
dec_cont1(D-(K+1), Cont_pathp, Dec_vecp):-
 d(D), K = 0..D, dec_cont1(D-K, Cont_path, c(0, Dec_vec)),
 up_dec(D-(K+1), Dec_vecp),
 control_pos_neg(D-K, Cont_vec, _),
 Cont_pathp = c(Cont_vec, Cont_path), 
 unique_sum(D-(K+1), Cont_path, Dec_vec, Dec_vecp, Dec_vecpp).
 	
dec_cont1(D-(K+1), Cont_pathpp, Dec_vecpp) :-
 d(D), K = 0..D, dec_cont1(D-K, Cont_path, c(0, Dec_vec)),
 up_dec(D-(K+1), Dec_vecpp), 
 control_pos_neg(D-K, _, Cont_neg_vec),
 Cont_pathpp = c(Cont_neg_vec, Cont_path), 
 unique_sum(D-(K+1), Cont_path, Dec_vec, Dec_vecp, Dec_vecpp).

% sum_gt_first(D-K, Dec_vec, Dec_vecp, Dec_vecpp) : Dec_vec is such that Dec_vec = Dec_vecp + Dec_vecpp (point-wise vector addition) with the first not both null elements of Dec_vecp and Dec_vecpp such that the one of Dec_vecp is higher or equal to that one of Dec_vecpp.									
sum_gt_first(-1, nil, nil, nil).
sum_gt_first(D-K, c(0, Dec_vec), c(0, Dec_vecp), c(0, Dec_vecpp)) :-
				d(D), K = 0..D, 
				sum_gt_first(D-(K+1), Dec_vec, Dec_vecp, Dec_vecpp).
sum_gt_first(D-K, c(N, Dec_vec), c(Np, Dec_vecp), c(Npp, Dec_vecpp)) :-
		d(D), K = 0..D, N > 0,  Np >= Npp,
		piecewise_sum(D-K, c(N, Dec_vec), c(Np, Dec_vecp), c(Npp, Dec_vecpp)).
							
% piecewise_sum(D-K, Dec_vec, Dec_vecp, Dec_vecpp): with a piecewise addition Dec_vec = Dec_vecp + Dec_vecpp. The size of these decomposition vectors is D-K +1.
piecewise_sum(-1, nil, nil, nil).
piecewise_sum(D-K, c(N, Dec_vec), c(Np, Dec_vecp), c(Npp, Dec_vecpp)) :-
		d(D), K = 0..D, N = Np + Npp,
		N = 0..2**(K+1), Np = 0..2**K, Npp = 0..2**K,
		piecewise_sum(D-(K+1), Dec_vec, Dec_vecp, Dec_vecpp).

% control_pos_neg(D-K, Cont_vec, Cont_neg_vec) : at the dimension D-K the choosen control values v = Cont_vec and v_tilda = Cont_neg_vec (used to reach the dimension D-(K+1)) are respectively 0 and 2**(2**(D-K))-1 according to the paper.
% we limit us to Cont_vec = 0, and to Cont_neg_vec = 1 as 0  and v_tilda of the paper, for the sake of simplifying the expression of the predicate "no closure".
% The cases where K = D are : 1) Dec_vec = <1>, then the decomposition terminates with Cont_path finishing with (Cont_v, Cont_neg_v) = (0, 1), 2) Dec_vec = <0>, then the decomposition terminates also because Dec_vec is null. So we can limit K to K < D. 
control_pos_neg(D-K, 0, 1) :- d(D), K = 0..D-1.	

%cont_path(K, Cont_path) : Cont_path is a path of lenght K. Recall that we reduce the search with control variables wich are 0 and 1 (representation of 0 tilda of the paper).
cont_path(0, nil).
cont_path(K, c(V_c, Cont_pathp)) :- d(D), K = 1..D,
			V_c = 0..1,  
			cont_path(K-1, Cont_pathp).


%%%%%%%%%%%%% Closure constraints obligation %%%%%%%%%%%%%%%%%%%%				

							
% If a network obtained via Cont_path is "embedded", then the closure constraints (which depend on Cont_path) of this network are mandatory, i.e. no_closure(K, Cont_path) must be false.			
:- decomp(D-K, Cont_path, c(1, Dec_vec)),
	d(D), K =0..D,
	dec_cont1(D-K, Cont_path, c(1, Dec_vec)), 
	cont_path(K, Cont_path), 
	no_closure(K, Cont_path).				
				
										


 
 
 

