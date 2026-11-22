# Checking the Cubiomes fork against the real game (THEORY.md 0, Minecraft 26.3)

`GameCheck.java` runs the game's own code (26.3 server jar, unobfuscated) and prints, for random seeds:
- `S`: the climate spawn position (`Climate.Sampler.findSpawnPosition`), which `estimateSpawn` models;
- `N`: the climate target point at random quart cells (half anywhere within 1M blocks, half within 2,048 blocks of
  spawn, all 96 layers) and the biome the game's parameter list returns there;
- `T`: random target points over the whole climate box and the game's biome, which tests every part of the tree.

`gamecheck.c` recomputes each line with the fork at `MC_26_3` and counts mismatches: climate values (bit for bit),
biomes and spawns. Required result: every count 0.

Steps (Linux/WSL):
1. Get the 26.3 server jar from Mojang's version manifest and run `java -jar server.jar --help` once, which unpacks
   `versions/26.3/server-26.3.jar` and `libraries/`.
2. `CP="versions/26.3/server-26.3.jar:$(find libraries -name '*.jar' | tr '\n' ':')"`
   `javac -cp "$CP" GameCheck.java && java -cp "$CP:." GameCheck 200 5000 2000000 1 > game.txt`
3. `gcc -O2 -fwrapv -I$CUBI -o gamecheck gamecheck.c $CUBI/libcubiomes.a -lm -pthread && ./gamecheck < game.txt`

The game's `findValue` keeps a per thread "last result" hint; Cubiomes and our model use the hint free search
(THEORY.md Lemma 26a). The two can differ only at exact distance ties, so any `T`/`N` biome mismatch must be checked
for a tie before anything else.
