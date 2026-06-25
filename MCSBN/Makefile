# Construit le generateur rapide en C.
#   make            -> compile ./bin/mcsbn (.exe sous Windows)
#   make test       -> lance la suite de validation Python (compare a la pipeline)
#   make clean      -> retire le binaire et les caches de table
#
# Linux/macOS : make depuis un shell standard (gcc requis).
# Windows     : depuis le shell "MSYS2 MinGW64"
#               (pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-zlib make python).
#               Le binaire est lie statiquement -> .exe autonome (pas de DLL a cote).

CC      ?= gcc
CFLAGS  ?= -O3 -march=native -fopenmp -Wall -Wno-unused-result
LDLIBS  := -lm -lz
PYTHON  ?= python3

# Windows : suffixe .exe + link statique de libgomp/libwinpthread/libz
# pour que ./bin/mcsbn.exe tourne aussi hors du shell MSYS2.
ifeq ($(OS),Windows_NT)
  EXE     := .exe
  LDFLAGS += -static
else
  EXE     :=
endif

BIN := bin/mcsbn$(EXE)
METABIN := bin/metagraph_layout$(EXE)

$(BIN): src/c/mcsbn.c | bin
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $< $(LDLIBS)

# Port C des passes Python de add_metagraph_layout.py (lecture CSV ->
# metagraphe -> DRGraph -> reecriture), pour les gros volumes.
$(METABIN): src/c/metagraph_layout.c | bin
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $< $(LDLIBS)

bin:
	mkdir -p bin

.PHONY: test clean drgraph metalayout
test: $(BIN)
	$(PYTHON) src/python/test_mcsbn.py

# Construit le port C de l'annotation metagraph_x/metagraph_y.
metalayout: $(METABIN)

# Construit le binaire DRGraph (Vis) servant a add_metagraph_layout.py.
# build.sh detecte gsl/boost dans l'env conda (cf. tools/DRGraph/build.sh).
drgraph:
	bash tools/DRGraph/build.sh

clean:
	rm -f bin/mcsbn bin/mcsbn.exe .cache/mcsbn_table_*.bin