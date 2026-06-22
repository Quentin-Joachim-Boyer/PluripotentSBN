% %%%%%%%%%%%%%%%%%%%% SBF RÉALISABLE (representees par bits) %%%%%%%%%%%%%%%%%%%%%
% %
% % sbf_bit(D,V,S) : dans la SBF de seuil 0 a D variables de vecteur de poids V,
% % l'etat S est actif. V est un terme compose encodant les D poids.
% % Representation bit a bit : evite l'encodage entier du pattern complet,
% % qui deborderait la representation entiere de clingo pour D >= 5 (2**31 overflow).

% wval(W) :- wb(Wb), W=-Wb..Wb.

% wvec(1, w(W1))             :- d>=2, wval(W1).
% wvec(2, w(W1,W2))          :- d>=3, wval(W1), wval(W2).
% wvec(3, w(W1,W2,W3))       :- d>=4, wval(W1), wval(W2), wval(W3).
% wvec(4, w(W1,W2,W3,W4))    :- d>=5, wval(W1), wval(W2), wval(W3), wval(W4).
% wvec(5, w(W1,W2,W3,W4,W5)) :- d>=6, wval(W1), wval(W2), wval(W3), wval(W4), wval(W5).

% sbf_bit(1, w(W1), S) :- wvec(1,w(W1)), S=0..1,
%     W1*((S/1)\2) > 0.
% sbf_bit(2, w(W1,W2), S) :- wvec(2,w(W1,W2)), S=0..3,
%     W1*((S/1)\2)+W2*((S/2)\2) > 0.
% sbf_bit(3, w(W1,W2,W3), S) :- wvec(3,w(W1,W2,W3)), S=0..7,
%     W1*((S/1)\2)+W2*((S/2)\2)+W3*((S/4)\2) > 0.
% sbf_bit(4, w(W1,W2,W3,W4), S) :- wvec(4,w(W1,W2,W3,W4)), S=0..15,
%     W1*((S/1)\2)+W2*((S/2)\2)+W3*((S/4)\2)+W4*((S/8)\2) > 0.
% sbf_bit(5, w(W1,W2,W3,W4,W5), S) :- wvec(5,w(W1,W2,W3,W4,W5)), S=0..31,
%     W1*((S/1)\2)+W2*((S/2)\2)+W3*((S/4)\2)+W4*((S/8)\2)+W5*((S/16)\2) > 0.