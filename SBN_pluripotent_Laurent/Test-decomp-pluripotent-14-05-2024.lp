%%%%%%%%%%%%%%%
% 1-03
% d(1).
% d(2).
d(3).
% d(4).

%%%%%%%%%%%
% :- not dec_cont1(2,nil,c(0,c(0,c(1,nil)))).
% :- not dec_cont1(2,nil,c(0,c(0,c(4,nil)))).% insatisf.
 
% :- not dec_cont1(3,nil,c(0,c(2,c(0, c(0,nil))))).

 :- not dec_cont1(3,nil,c(0,c(1,c(2, c(0,nil))))).
 
% :- not dec_cont1(3,nil,c(0,c(0,c(4, c(0,nil))))).
% :- not dec_cont1(3,nil,c(0,c(1,c(1, c(0,nil))))).
% :- not dec_cont1(3,nil,c(0,c(0,c(2, c(1,nil))))).

% :- not dec_cont1(4,nil,c(0,c(2,c(0, c(0, c(0,nil)))))).

% 1 cube + 2 surfaces
% :- not dec_cont1(4,nil,c(0,c(1,c(2, c(0, c(0,nil)))))).
% :- not funct(4, 65280). % 4eme fonction fixée 
% :- not funct(3, 61682). % 3eme fonction fixée 

%%%%%%%%%%%%%%%%%%%%
% 1 cube, 2 surfaces 
% :- not dec_cont1(4,nil,c(0,c(1,c(2, c(0, c(0,nil)))))).

% 1 cube, 1 surface, 2 segments 
% :- not dec_cont1(4,nil,c(0,c(1,c(1, c(2, c(0,nil)))))).

% 1 cube, 4 segments insatisfiable
% :- not dec_cont1(4,nil,c(0,c(1,c(0, c(4, c(0,nil)))))).

% 3 surfaces et 2 segments
% :- not dec_cont1(4,nil,c(0,c(0,c(3, c(2, c(0,nil)))))).

% 2 surfaces et 4 segments. (22-11-2024) Insatisfiable 71 s.
% :- not dec_cont1(4,nil,c(0,c(0,c(2, c(4, c(0,nil)))))).
  
% 4 surfaces OK (18-05-2026) Insatisfiable 72 s. 
% :- not dec_cont1(4,nil,c(0,c(0,c(4, c(0, c(0,nil)))))).
 
 %%%%%%%%%%%%%%%
% 1 surfaces et 6 segments. (29-11-2024) 
% :- not dec_cont1(4,nil,c(0,c(0,c(1, c(6, c(0,nil)))))).


% :- not dec_cont1(2,nil,c(0,c(2,c(0,nil)))). 
% :- not dec_cont1(1,nil,c(0,c(2,nil))).
% :- not dec_cont1(2,nil,c(0,c(1,c(2,nil)))). %Insatisf.
% :- not dec_cont1(D, nil, c(0, c(0, c(2, nil)))), d(D).                                                                                                               
% :- not up_dec(D, c(0, c(0, c(2, nil)))), d(D). Marche
% :- not up_dec(D, c(0, c(0, c(2, nil))), 2), d(D). Marche


%*
 voir_sum_gt_first102(Dec_vecp, Dec_vecpp):- 
				sum_gt_first(1, c(0,c(2,nil)), Dec_vecp, Dec_vecpp),
				up_dec(1, Dec_vecp, W_p), up_dec(1, Dec_vecpp, W_pp),
				W_p >= W_pp.
				
 voir_sum_gt_first00(Dec_vecp, Dec_vecpp):- 
				sum_gt_first(0, c(0,nil), Dec_vecp, Dec_vecpp),
				up_dec(0, Dec_vecp, W_p), up_dec(0, Dec_vecpp, W_pp),
				W_p >= W_pp.
 voir_weight_cp(N1, N, V, Cont_path) :- 
		&sum{weight_cp(N1, N, Cont_path)} = V, 
		edge_cont(N1, N, Cont_path), V = -(D-K)..D-K,
		cont_path(K, Cont_path), d(D), 
		 dec_emb(Cont_path).
 *%
 
% #show voir_sum_gt_first00/2.				
% #show sum_gt_first/4.
% #show voir_sum_gt_first102/2.
% #show unique_sum/5. 
% #show decomp/3.
% #show dec_cont1/3.
% #show dec_emb/2.
 #show funct/2.
% #show funct1/2.
% #show funct_cp/3.

% #show tous_function.
% #show dec_emb/1.
% #show up_dec/3.
% #show edge_cont/3.
% #show.

% #show dif_faces/2.

 
%
 &show{weight/2}.

%  &show.
% &show{bf_node/1}.
% &show{bf_node/2}.
% &show{bf_node1/2}.
 
% &show{bit/2}.
% #show entry_cont/3.
% &sum{bf_node(1)}=14.
% &sum{bf_node(2)}=12.

% &show{weight_cp/3}.
% #show voir_weight_cp/4.
% &show{pos_weight_sum_cp/3}.
% &show {weight_sum_cp/3}.


% :- not dec_emb(Cont_path), 
%	cont_path(K, Cont_path), K = 0..D, d(D),
%	edge(N1, N), &sum{weight_cp(N1, N, Cont_path)} >= 0. 

% #show look_two/5.



%test contraintes SBF sur tous les réseaux.

















%*
%%%%%%%%%%%% A RETENIR le 16-05-2024
% decomposition de <nil, c(0, c(0, c(2, nil))))> en
% d'une part <00, c(1, nil)> et <01, c(1, nil)> avec Answer 1
% d'autre part <00, c(1, nil)> et 

%%% Affaire --project bizarre !
trilling@timc-misi-17:~/Datas/dossiers_timc/Nicolas-Glade/Remi-Segretain/Pour-Rémi-29-10-2019/essai-02-05-2022/Programme-Pluripotent-12-06-2023$ clingcon SBF-constraints-21-05-2025.lp Fonctions-bool-Cont-cloture-11-12-2023.lp Test-decomp-pluripotent-14-05-2024.lp decomp-pluripotent-14-05-2023.lp --project  -n  0
clingcon version 5.2.1
Reading from SBF-constraints-21-05-2025.lp ...
Solving...
Answer: 1

Assignment:
bf_node(1)=12 bf_node(2)=12
SATISFIABLE



%%%%%%%%%%%

Models       : 1
Calls        : 1
Time         : 0.034s (Solving: 0.00s 1st Model: 0.00s Unsat: 0.00s)
CPU Time     : 0.033s


dec_cont1(0,c(0,c(1,nil)),c(1,nil))

dec_cont1(0,c(1,c(0,nil)),c(0,nil)) 
dec_cont1(0,c(1,c(1,nil)),c(0,nil))

dec_cont1(1,c(0,nil),c(0,c(1,nil))) 
dec_cont1(1,c(1,nil),c(0,c(1,nil))) 

dec_cont1(2,nil,c(0,c(0,c(2,nil))))


Answer: 2

dec_cont1(0,c(0,c(0,nil)),c(1,nil)) 
dec_cont1(0,c(1,c(0,nil)),c(1,nil))
 
dec_cont1(1,c(0,nil),c(0,c(2,nil))) 
dec_cont1(1,c(1,nil),c(0,c(0,nil)))
 
dec_cont1(2,nil,c(0,c(0,c(2,nil))))

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
*%

%* le 13-05 a tester maintenant avec copie pour decomp !
trilling@timc-misi-17:~/Datas/dossiers_timc/Nicolas-Glade/Remi-Segretain/Pour-Ré
mi-29-10-2019/essai-02-05-2022/Programme-Pluripotent-12-06-2023$ clingcon decomp-pluripotent-12-06-2023.lp Test-decomp-pluripotent-1-03-2024.lp Fonctions-bool-Cont-cloture-11-12-2023.lp -n 3
clingcon version 5.2.1
Reading from decomp-pluripotent-12-06-2023.lp ...
Solving...
Answer: 1
dec_cont1(0,c(0,c(0,nil)),c(1,nil)) dec_cont1(0,c(0,c(1,nil)),c(1,nil)) dec_cont1(0,c(1,c(0,nil)),c(0,nil)) dec_cont1(0,c(1,c(1,nil)),c(0,nil)) dec_cont1(1,c(0,nil),c(0,c(1,nil))) dec_cont1(1,c(1,nil),c(0,c(1,nil))) dec_cont1(2,nil,c(0,c(0,c(2,nil))))
Assignment:
bf_node(1)=10 bf_node(2)=14 bit(1,0)=0 bit(1,1)=1 bit(1,2)=0 bit(1,3)=1 bit(2,0)=0 bit(2,1)=1 bit(2,2)=1 bit(2,3)=1
Answer: 2
dec_cont1(0,c(0,c(0,nil)),c(1,nil)) dec_cont1(0,c(0,c(1,nil)),c(1,nil)) dec_cont1(0,c(1,c(0,nil)),c(0,nil)) dec_cont1(0,c(1,c(1,nil)),c(0,nil)) dec_cont1(1,c(0,nil),c(0,c(1,nil))) dec_cont1(1,c(1,nil),c(0,c(1,nil))) dec_cont1(2,nil,c(0,c(0,c(2,nil))))
Assignment:
bf_node(1)=10 bf_node(2)=12 bit(1,0)=0 bit(1,1)=1 bit(1,2)=0 bit(1,3)=1 bit(2,0)=0 bit(2,1)=0 bit(2,2)=1 bit(2,3)=1
Answer: 3
dec_cont1(0,c(0,c(0,nil)),c(1,nil)) dec_cont1(0,c(0,c(1,nil)),c(1,nil)) dec_cont1(0,c(1,c(0,nil)),c(0,nil)) dec_cont1(0,c(1,c(1,nil)),c(0,nil)) dec_cont1(1,c(0,nil),c(0,c(1,nil))) dec_cont1(1,c(1,nil),c(0,c(1,nil))) dec_cont1(2,nil,c(0,c(0,c(2,nil))))
Assignment:
bf_node(1)=8 bf_node(2)=12 bit(1,0)=0 bit(1,1)=0 bit(1,2)=0 bit(1,3)=1 bit(2,0)=0 bit(2,1)=0 bit(2,2)=1 bit(2,3)=1
SATISFIABLE

Models       : 3+

*%


% le 16-05 resultat obtenu avec version decomps-pluripotent-14-05-2023.lp. Au total il y a 32 solution  pour le vecteur de décomposition c(0,c(0,c(2,nil))).
%*
trilling@timc-misi-17:~/Datas/dossiers_timc/Nicolas-Glade/Remi-Segretain/Pour-Ré
mi-29-10-2019/essai-02-05-2022/Programme-Pluripotent-12-06-2023$ clingcon decomp-pluripotent-14-05-2023.lp Test-decomp-pluripotent-14-05-2024.lp Fonctions-bool-Cont-cloture-11-12-2023.lp -n  3
clingcon version 5.2.1
Reading from decomp-pluripotent-14-05-2023.lp ...
Solving...
Answer: 1
dec_cont1(0,c(0,c(0,nil)),c(1,nil)) dec_cont1(0,c(0,c(1,nil)),c(1,nil)) dec_cont1(0,c(1,c(0,nil)),c(0,nil)) dec_cont1(0,c(1,c(1,nil)),c(0,nil)) dec_cont1(1,c(0,nil),c(0,c(1,nil))) dec_cont1(1,c(1,nil),c(0,c(1,nil))) dec_cont1(2,nil,c(0,c(0,c(2,nil)))) unique_sum(0,c(0,nil),c(1,nil),c(1,nil),c(0,nil)) unique_sum(0,c(1,nil),c(1,nil),c(1,nil),c(0,nil)) unique_sum(1,nil,c(0,c(2,nil)),c(0,c(1,nil)),c(0,c(1,nil)))
Assignment:
bf_node(1)=10 bf_node(2)=14 bf_decomp(1,0)=0 bf_decomp(1,1)=2 bf_decomp(1,2)=2 bf_decomp(1,3)=10 bf_decomp(2,0)=0 bf_decomp(2,1)=2 bf_decomp(2,2)=6 bf_decomp(2,3)=14 bit(1,0)=0 bit(1,1)=1 bit(1,2)=0 bit(1,3)=1 bit(2,0)=0 bit(2,1)=1 bit(2,2)=1 bit(2,3)=1
Answer: 2
dec_cont1(0,c(0,c(0,nil)),c(1,nil)) dec_cont1(0,c(0,c(1,nil)),c(1,nil)) dec_cont1(0,c(1,c(0,nil)),c(0,nil)) dec_cont1(0,c(1,c(1,nil)),c(0,nil)) dec_cont1(1,c(0,nil),c(0,c(1,nil))) dec_cont1(1,c(1,nil),c(0,c(1,nil))) dec_cont1(2,nil,c(0,c(0,c(2,nil)))) unique_sum(0,c(0,nil),c(1,nil),c(1,nil),c(0,nil)) unique_sum(0,c(1,nil),c(1,nil),c(1,nil),c(0,nil)) unique_sum(1,nil,c(0,c(2,nil)),c(0,c(1,nil)),c(0,c(1,nil)))
Assignment:
bf_node(1)=8 bf_node(2)=14 bf_decomp(1,0)=0 bf_decomp(1,1)=0 bf_decomp(1,2)=0 bf_decomp(1,3)=8 bf_decomp(2,0)=0 bf_decomp(2,1)=2 bf_decomp(2,2)=6 bf_decomp(2,3)=14 bit(1,0)=0 bit(1,1)=0 bit(1,2)=0 bit(1,3)=1 bit(2,0)=0 bit(2,1)=1 bit(2,2)=1 bit(2,3)=1
Answer: 3
dec_cont1(0,c(0,c(0,nil)),c(1,nil)) dec_cont1(0,c(0,c(1,nil)),c(1,nil)) dec_cont1(0,c(1,c(0,nil)),c(0,nil)) dec_cont1(0,c(1,c(1,nil)),c(0,nil)) dec_cont1(1,c(0,nil),c(0,c(1,nil))) dec_cont1(1,c(1,nil),c(0,c(1,nil))) dec_cont1(2,nil,c(0,c(0,c(2,nil)))) unique_sum(0,c(0,nil),c(1,nil),c(1,nil),c(0,nil)) unique_sum(0,c(1,nil),c(1,nil),c(1,nil),c(0,nil)) unique_sum(1,nil,c(0,c(2,nil)),c(0,c(1,nil)),c(0,c(1,nil)))
Assignment:
bf_node(1)=0 bf_node(2)=14 bf_decomp(1,0)=0 bf_decomp(1,1)=0 bf_decomp(1,2)=0 bf_decomp(1,3)=0 bf_decomp(2,0)=0 bf_decomp(2,1)=2 bf_decomp(2,2)=6 bf_decomp(2,3)=14 bit(1,0)=0 bit(1,1)=0 bit(1,2)=0 bit(1,3)=0 bit(2,0)=0 bit(2,1)=1 bit(2,2)=1 bit(2,3)=1
SATISFIABLE

Models       : 3+
Calls        : 1
Time         : 0.027s (Solving: 0.00s 1st Model: 0.00s Unsat: 0.00s)
CPU Time     : 0.027s
trilling@timc-misi-17:~/
*%





