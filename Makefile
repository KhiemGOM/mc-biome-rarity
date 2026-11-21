CUBI ?= /home/claude/cubiomes

raysim: raysim.c
	gcc -O3 -fwrapv -I$(CUBI) -o raysim raysim.c $(CUBI)/libcubiomes.a -lm -pthread

test: raysim
	python3 -m pytest -q
