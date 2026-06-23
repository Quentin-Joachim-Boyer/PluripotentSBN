# Construit le generateur rapide en C.
#   make            -> compile ./mcsbn
#   make test       -> lance la suite de validation Python (compare a la pipeline)
#   make clean      -> retire le binaire et les caches de table

CC      ?= gcc
CFLAGS  ?= -O3 -march=native -fopenmp -Wall -Wno-unused-result
LDLIBS  := -lm

mcsbn: mcsbn.c
	$(CC) $(CFLAGS) -o $@ $< $(LDLIBS)

.PHONY: test clean
test: mcsbn
	python3 test_mcsbn.py

clean:
	rm -f mcsbn .cache/mcsbn_table_*.bin
