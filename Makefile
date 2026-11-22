# Cubiomes location: $CUBIOMES if set, else ~/cubiomes-xp. Override with: make CUBIOMES=/path
CUBIOMES ?= $(HOME)/cubiomes-xp
CUBI ?= $(CUBIOMES)
export CUBIOMES

raysim: raysim.c
	gcc -O3 -fwrapv -ffp-contract=off -fno-fast-math -I$(CUBI) -o raysim raysim.c $(CUBI)/libcubiomes.a -lm -pthread

test: raysim
	python3 -m pytest -q
