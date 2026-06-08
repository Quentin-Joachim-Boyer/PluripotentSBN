#const n = 3.
#const d = 1.

node(1..n).
state(0..2**n-1).

activated(I,S) :- node(I), state(S), (S / 2**(I-1)) \ 2 = 1.

&dom{(-d)..d} = w(I) :- node(I).

tf_bit(S) :- state(S), &sum{w(I) : node(I), activated(I,S)} > 0.

#show tf_bit/1.
