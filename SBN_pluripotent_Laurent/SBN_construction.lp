#const d = 2.
#const w_bound = d.

node(0..d-1).

state(0..2**d-1).

% &dom{(-d)..d} = w(N1,N2) :- node(N1),node(N2).

{w(N1,N2,V): V =(-w_bound)..w_bound} = 1 :- node(N1),node(N2).

#sum {2**N : activated(N,S) : node(N)} = S :- state(S).

% #show activated/2.

transition_function_bit(N,S) :- node(N), state(S), #sum {V:w(NI,N,V),node(NI),activated(NI,S)} > 0.
transition_function(N,X) :- node(N), X = #sum {2**S : state(S),transition_function_bit(N,S)}.


#show transition_function/2.
% #show w/3.