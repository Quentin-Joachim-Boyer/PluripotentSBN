#const d = 3.
#const v0 = 0.
#const v1 = 0.
#const v2 = 0.
#const v3 = 0.
#const v4 = 0.
#const v5 = 0.

d(d).

:- not dec_cont1(d,nil,(v1,c(v0,nil))),d(1).
:- not dec_cont1(d,nil,c(v2,c(v1,c(v0,nil)))),d(2).
:- not dec_cont1(d,nil,c(v3,c(v2,c(v1,c(v0,nil))))),d(3).
:- not dec_cont1(d,nil,c(v4,c(v3,c(v2,c(v1,c(v0,nil)))))),d(4).
% :- not funct(4, 65280),d(4). % 4eme fonction fixée 
:- not dec_cont1(d,nil,c(v5,c(v4,c(v3,c(v2,c(v1,c(v0,nil))))))),d(5).

#show funct/2.
&show{weight/2}.

