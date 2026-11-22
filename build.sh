#!/usr/bin/env bash
# Build Cubiomes (pinned) and all simulators. Usage: ./build.sh [path-to-cubiomes]
# Cubiomes: the xpple/cubiomes fork, which has Java 26.3 biome generation (THEORY.md 0). Location: first argument,
# else $CUBIOMES, else ~/cubiomes-xp. The 1.21.4 results were made with Cubitect/cubiomes e61f905 and DX_VERSION=214.
set -euo pipefail
CUBI="${1:-${CUBIOMES:-$HOME/cubiomes-xp}}"
PIN=304940b
if [ ! -d "$CUBI" ]; then git clone https://github.com/xpple/cubiomes.git "$CUBI"; fi
git -C "$CUBI" fetch -q origin || true
git -C "$CUBI" checkout -q "$PIN"
cmake -S "$CUBI" -B "$CUBI/build" -DCMAKE_BUILD_TYPE=Release > /dev/null
cmake --build "$CUBI/build" -j"$(nproc)" --target cubiomes_static cubiomes > /dev/null
cp "$CUBI/build/libcubiomes_static.a" "$CUBI/libcubiomes.a"
cp "$CUBI/build/libcubiomes.so" "$CUBI/libcubiomes.so"   # used only by tests/test_raysim.py (ctypes oracle)
for p in raysim colsim discsim discexact mapdump; do
  gcc -O3 -fwrapv -I"$CUBI" -o "$p" "$p.c" "$CUBI/libcubiomes.a" -lm -pthread
done
echo "built. Cubiomes at $CUBI ($(git -C "$CUBI" rev-parse --short HEAD))"
if [ "$CUBI" != "$HOME/cubiomes-xp" ]; then
  echo "run tests with: CUBIOMES=$CUBI python3 -m pytest -q   (or: make test CUBIOMES=$CUBI)"
fi
