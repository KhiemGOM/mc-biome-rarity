#!/usr/bin/env bash
# Build Cubiomes (pinned) and all simulators. Usage: ./build.sh [path-to-cubiomes]
# Cubiomes location: first argument, else $CUBIOMES, else ~/cubiomes.
set -euo pipefail
CUBI="${1:-${CUBIOMES:-$HOME/cubiomes}}"
PIN=e61f90580cbdd883214a8054670dacae655e59c0
if [ ! -d "$CUBI" ]; then git clone https://github.com/Cubitect/cubiomes.git "$CUBI"; fi
git -C "$CUBI" checkout "$PIN"
make -C "$CUBI" release            # produces libcubiomes.a
# libcubiomes.so is used only by tests/test_raysim.py (ctypes oracle)
# Rebuilt every time so a stale .so from an older build.sh (missing util.c) is replaced.
(cd "$CUBI" && gcc -shared -fPIC -O3 -fwrapv -o libcubiomes.so biomenoise.c biomes.c finders.c generator.c layers.c noise.c quadbase.c util.c -lm)
for p in raysim colsim discsim discexact mapdump; do
  gcc -O3 -fwrapv -I"$CUBI" -o "$p" "$p.c" "$CUBI/libcubiomes.a" -lm -pthread
done
echo "built. Cubiomes at $CUBI"
if [ "$CUBI" != "$HOME/cubiomes" ]; then
  echo "run tests with: CUBIOMES=$CUBI python3 -m pytest -q   (or: make test CUBIOMES=$CUBI)"
fi
