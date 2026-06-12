% Ce programme à pour but de subdiviser l'espace des fonctions de transition à explorer
% pour que la parallélisation de JPP empêche le processus d'atteindre la limite memoire,
% et puisse potentiellement accélérer le processus.

% Fixe les fixed_bits premiers bits (S=0..fixed_bits-1) de la fonction de
% transition (SBF) du noeud fixed_node, via les constantes fixed_sbf_bit_S
% (une par etat S possible). Pour d <= 6, state(S) est borne a 0..63, donc
% seules les constantes fixed_sbf_bit_0..fixed_sbf_bit_63 sont utiles ; au-dela
% il suffirait d'en declarer plus.
#const fixed_node = 1.
#const fixed_bits = 0.

#const fixed_sbf_bit_0 = 0.
#const fixed_sbf_bit_1 = 0.
#const fixed_sbf_bit_2 = 0.
#const fixed_sbf_bit_3 = 0.
#const fixed_sbf_bit_4 = 0.
#const fixed_sbf_bit_5 = 0.
#const fixed_sbf_bit_6 = 0.
#const fixed_sbf_bit_7 = 0.
#const fixed_sbf_bit_8 = 0.
#const fixed_sbf_bit_9 = 0.
#const fixed_sbf_bit_10 = 0.
#const fixed_sbf_bit_11 = 0.
#const fixed_sbf_bit_12 = 0.
#const fixed_sbf_bit_13 = 0.
#const fixed_sbf_bit_14 = 0.
#const fixed_sbf_bit_15 = 0.
#const fixed_sbf_bit_16 = 0.
#const fixed_sbf_bit_17 = 0.
#const fixed_sbf_bit_18 = 0.
#const fixed_sbf_bit_19 = 0.
#const fixed_sbf_bit_20 = 0.
#const fixed_sbf_bit_21 = 0.
#const fixed_sbf_bit_22 = 0.
#const fixed_sbf_bit_23 = 0.
#const fixed_sbf_bit_24 = 0.
#const fixed_sbf_bit_25 = 0.
#const fixed_sbf_bit_26 = 0.
#const fixed_sbf_bit_27 = 0.
#const fixed_sbf_bit_28 = 0.
#const fixed_sbf_bit_29 = 0.
#const fixed_sbf_bit_30 = 0.
#const fixed_sbf_bit_31 = 0.
#const fixed_sbf_bit_32 = 0.
#const fixed_sbf_bit_33 = 0.
#const fixed_sbf_bit_34 = 0.
#const fixed_sbf_bit_35 = 0.
#const fixed_sbf_bit_36 = 0.
#const fixed_sbf_bit_37 = 0.
#const fixed_sbf_bit_38 = 0.
#const fixed_sbf_bit_39 = 0.
#const fixed_sbf_bit_40 = 0.
#const fixed_sbf_bit_41 = 0.
#const fixed_sbf_bit_42 = 0.
#const fixed_sbf_bit_43 = 0.
#const fixed_sbf_bit_44 = 0.
#const fixed_sbf_bit_45 = 0.
#const fixed_sbf_bit_46 = 0.
#const fixed_sbf_bit_47 = 0.
#const fixed_sbf_bit_48 = 0.
#const fixed_sbf_bit_49 = 0.
#const fixed_sbf_bit_50 = 0.
#const fixed_sbf_bit_51 = 0.
#const fixed_sbf_bit_52 = 0.
#const fixed_sbf_bit_53 = 0.
#const fixed_sbf_bit_54 = 0.
#const fixed_sbf_bit_55 = 0.
#const fixed_sbf_bit_56 = 0.
#const fixed_sbf_bit_57 = 0.
#const fixed_sbf_bit_58 = 0.
#const fixed_sbf_bit_59 = 0.
#const fixed_sbf_bit_60 = 0.
#const fixed_sbf_bit_61 = 0.
#const fixed_sbf_bit_62 = 0.
#const fixed_sbf_bit_63 = 0.

fixed_sbf_bit(0,fixed_sbf_bit_0).
fixed_sbf_bit(1,fixed_sbf_bit_1).
fixed_sbf_bit(2,fixed_sbf_bit_2).
fixed_sbf_bit(3,fixed_sbf_bit_3).
fixed_sbf_bit(4,fixed_sbf_bit_4).
fixed_sbf_bit(5,fixed_sbf_bit_5).
fixed_sbf_bit(6,fixed_sbf_bit_6).
fixed_sbf_bit(7,fixed_sbf_bit_7).
fixed_sbf_bit(8,fixed_sbf_bit_8).
fixed_sbf_bit(9,fixed_sbf_bit_9).
fixed_sbf_bit(10,fixed_sbf_bit_10).
fixed_sbf_bit(11,fixed_sbf_bit_11).
fixed_sbf_bit(12,fixed_sbf_bit_12).
fixed_sbf_bit(13,fixed_sbf_bit_13).
fixed_sbf_bit(14,fixed_sbf_bit_14).
fixed_sbf_bit(15,fixed_sbf_bit_15).
fixed_sbf_bit(16,fixed_sbf_bit_16).
fixed_sbf_bit(17,fixed_sbf_bit_17).
fixed_sbf_bit(18,fixed_sbf_bit_18).
fixed_sbf_bit(19,fixed_sbf_bit_19).
fixed_sbf_bit(20,fixed_sbf_bit_20).
fixed_sbf_bit(21,fixed_sbf_bit_21).
fixed_sbf_bit(22,fixed_sbf_bit_22).
fixed_sbf_bit(23,fixed_sbf_bit_23).
fixed_sbf_bit(24,fixed_sbf_bit_24).
fixed_sbf_bit(25,fixed_sbf_bit_25).
fixed_sbf_bit(26,fixed_sbf_bit_26).
fixed_sbf_bit(27,fixed_sbf_bit_27).
fixed_sbf_bit(28,fixed_sbf_bit_28).
fixed_sbf_bit(29,fixed_sbf_bit_29).
fixed_sbf_bit(30,fixed_sbf_bit_30).
fixed_sbf_bit(31,fixed_sbf_bit_31).
fixed_sbf_bit(32,fixed_sbf_bit_32).
fixed_sbf_bit(33,fixed_sbf_bit_33).
fixed_sbf_bit(34,fixed_sbf_bit_34).
fixed_sbf_bit(35,fixed_sbf_bit_35).
fixed_sbf_bit(36,fixed_sbf_bit_36).
fixed_sbf_bit(37,fixed_sbf_bit_37).
fixed_sbf_bit(38,fixed_sbf_bit_38).
fixed_sbf_bit(39,fixed_sbf_bit_39).
fixed_sbf_bit(40,fixed_sbf_bit_40).
fixed_sbf_bit(41,fixed_sbf_bit_41).
fixed_sbf_bit(42,fixed_sbf_bit_42).
fixed_sbf_bit(43,fixed_sbf_bit_43).
fixed_sbf_bit(44,fixed_sbf_bit_44).
fixed_sbf_bit(45,fixed_sbf_bit_45).
fixed_sbf_bit(46,fixed_sbf_bit_46).
fixed_sbf_bit(47,fixed_sbf_bit_47).
fixed_sbf_bit(48,fixed_sbf_bit_48).
fixed_sbf_bit(49,fixed_sbf_bit_49).
fixed_sbf_bit(50,fixed_sbf_bit_50).
fixed_sbf_bit(51,fixed_sbf_bit_51).
fixed_sbf_bit(52,fixed_sbf_bit_52).
fixed_sbf_bit(53,fixed_sbf_bit_53).
fixed_sbf_bit(54,fixed_sbf_bit_54).
fixed_sbf_bit(55,fixed_sbf_bit_55).
fixed_sbf_bit(56,fixed_sbf_bit_56).
fixed_sbf_bit(57,fixed_sbf_bit_57).
fixed_sbf_bit(58,fixed_sbf_bit_58).
fixed_sbf_bit(59,fixed_sbf_bit_59).
fixed_sbf_bit(60,fixed_sbf_bit_60).
fixed_sbf_bit(61,fixed_sbf_bit_61).
fixed_sbf_bit(62,fixed_sbf_bit_62).
fixed_sbf_bit(63,fixed_sbf_bit_63).

:- state(S), S < fixed_bits, fixed_sbf_bit(S,1), not transition_function_bit(fixed_node,S).
:- state(S), S < fixed_bits, fixed_sbf_bit(S,0), transition_function_bit(fixed_node,S).
