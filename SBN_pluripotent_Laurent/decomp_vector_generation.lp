#const d=3.

n(0..d).

&dom{0..2**d} = v(I) :- n(I).

:- not &sum{2**I*v(I):n(I)} = 2**d.

&show {v/1}.