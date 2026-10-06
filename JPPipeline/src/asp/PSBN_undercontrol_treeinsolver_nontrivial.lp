% PSBN_undercontrol_treeinsolver.lp sans le vecteur trivial <1,0,...,0>, qui contient
% toutes les dynamiques (1,87.10^10 en d = 4) et rendrait l'énumération interminable.
% La contrainte rend ce vecteur insatisfiable : JPP en reçoit 0 solution et passe aux
% autres, qui sont énumérés exactement comme par le programme d'origine.
% Usage (d = 4, toutes les solutions) :
%   java -cp <bin>:JPPipeline/lib/jpp.jar PSBN.Main 4 \
%        JPPipeline/src/asp/PSBN_undercontrol_treeinsolver_nontrivial.lp JPPipeline/src/asp 0 <sortie> 1

#include "PSBN_undercontrol_treeinsolver.lp".

:- d = 2, v2 = 1.
:- d = 3, v3 = 1.
:- d = 4, v4 = 1.
:- d = 5, v5 = 1.
:- d = 6, v6 = 1.
