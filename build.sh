#!/usr/bin/env bash
# Build Cubiomes (pinned) and all simulators. Usage: ./build.sh [path-to-cubiomes]
set -euo pipefail
CUBI="${1:-$HOME/cubiomes}"
PIN=e61f90580cbdd883214a8054670dacae655e59c0
if [ ! -d "$CUBI" ]; then git clone https://github.com/Cubitect/cubiomes.git "$CUBI"; fi
git -C "$CUBI" checkout "$PIN"
make -C "$CUBI" release            # produces libcubiomes.a
# libcubiomes.so is used only by tests/test_raysim.py (ctypes oracle)
if [ ! -f "$CUBI/libcubiomes.so" ]; then
  (cd "$CUBI" && gcc -shared -fPIC -O3 -fwrapv -o libcubiomes.so biomenoise.c biomes.c finders.c generator.c layers.c noise.c quadbase.c -lm)
fi
for p in raysim colsim discsim discexact mapdump; do
  gcc -O3 -fwrapv -I"$CUBI" -o "$p" "$p.c" "$CUBI/libcubiomes.a" -lm -pthread
done
echo "built. Cubiomes at $CUBI (tests expect it at /home/claude/cubiomes; symlink or edit CUBI in tests/test_raysim.py)"
