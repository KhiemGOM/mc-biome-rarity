# Certified ranking from paired differences

Every biome pair is compared on the same seeds and rays (THEORY.md 9.1). A rank range says where the biome can be: rank 3 to 5 means exactly 2 biomes are certified rarer and the others in between are not separated from it. Except with chance at most 2e-06 (1 in 500,000) every statement below and every range of report.md hold at once.

Plan `c838d3c2e97b6c69`.


## Sight radius 0 (53750 seeds)

| rank | biome | E[D] from spawn | not separated from |
|---|---|---|---|
| 1 | mushroom_fields | 149,466 | none |
| 2 | pale_garden | 114,028 | none |
| 3 | windswept_gravelly_hills | 94,752 | none |
| 4 | stony_peaks | 83,782 | none |
| 5 | ice_spikes | 75,084 | none |
| 6 | eroded_badlands | 70,124 | none |
| 7 | mangrove_swamp | 58,577 | none |
| 8 to 10 | wooded_badlands | 53,978 | jagged_peaks, frozen_peaks |
| 8 to 10 | jagged_peaks | 53,782 | wooded_badlands, frozen_peaks |
| 8 to 10 | frozen_peaks | 53,507 | wooded_badlands, jagged_peaks |
| 11 | windswept_forest | 47,794 | none |
| 12 to 13 | badlands | 39,876 | windswept_savanna |
| 12 to 13 | windswept_savanna | 39,620 | badlands |
| 14 to 15 | deep_frozen_ocean | 36,610 | cherry_grove |
| 14 to 16 | cherry_grove | 35,467 | windswept_hills, deep_frozen_ocean |
| 15 to 18 | windswept_hills | 33,726 | savanna_plateau, snowy_slopes, cherry_grove |
| 16 to 19 | savanna_plateau | 33,010 | windswept_hills, warm_ocean, snowy_slopes |
| 16 to 19 | snowy_slopes | 32,345 | windswept_hills, savanna_plateau, warm_ocean |
| 17 to 19 | warm_ocean | 31,328 | savanna_plateau, snowy_slopes |
| 20 | swamp | 29,197 | none |
| 21 to 22 | snowy_beach | 25,925 | bamboo_jungle |
| 21 to 24 | bamboo_jungle | 25,378 | desert, snowy_beach, old_growth_spruce_taiga |
| 22 to 25 | old_growth_spruce_taiga | 24,570 | desert, old_growth_pine_taiga, bamboo_jungle |
| 22 to 25 | desert | 24,118 | old_growth_pine_taiga, old_growth_spruce_taiga, bamboo_jungle |
| 23 to 25 | old_growth_pine_taiga | 24,011 | desert, old_growth_spruce_taiga |
| 26 to 27 | flower_forest | 22,396 | sunflower_plains |
| 26 to 27 | sunflower_plains | 22,001 | flower_forest |
| 28 to 29 | grove | 19,768 | frozen_ocean |
| 28 to 29 | frozen_ocean | 19,642 | grove |
| 30 to 32 | snowy_taiga | 16,386 | snowy_plains, deep_lukewarm_ocean |
| 30 to 33 | deep_lukewarm_ocean | 16,213 | frozen_river, snowy_plains, snowy_taiga |
| 30 to 32 | snowy_plains | 16,203 | snowy_taiga, deep_lukewarm_ocean |
| 32 to 34 | frozen_river | 15,548 | deep_lukewarm_ocean, deep_cold_ocean |
| 33 to 34 | deep_cold_ocean | 15,103 | frozen_river |
| 35 to 36 | sparse_jungle | 11,454 | dark_forest |
| 35 to 36 | dark_forest | 11,251 | sparse_jungle |
| 37 to 38 | meadow | 10,492 | jungle |
| 37 to 39 | jungle | 10,333 | deep_ocean, meadow |
| 38 to 39 | deep_ocean | 9,846 | jungle |
| 40 to 41 | savanna | 7,966 | lukewarm_ocean |
| 40 to 41 | lukewarm_ocean | 7,869 | savanna |
| 42 to 43 | cold_ocean | 7,170 | taiga |
| 42 to 44 | taiga | 6,873 | cold_ocean, old_growth_birch_forest |
| 43 to 44 | old_growth_birch_forest | 6,641 | taiga |
| 45 to 46 | birch_forest | 6,305 | stony_shore |
| 45 to 46 | stony_shore | 6,261 | birch_forest |
| 47 | ocean | 4,241 | none |
| 48 | deep_dark | 2,973 | none |
| 49 | beach | 2,563 | none |
| 50 | dripstone_caves | 1,946 | none |
| 51 | lush_caves | 1,730 | none |
| 52 | plains | 1,582 | none |
| 53 | forest | 1,157 | none |
| 54 | river | 754 | none |
