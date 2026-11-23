# Certified ranking from paired differences

Every biome pair is compared on the same seeds and rays (THEORY.md 9.1). A rank range says where the biome can be: rank 3 to 5 means exactly 2 biomes are certified rarer and the others in between are not separated from it. Except with chance at most 2e-06 (1 in 500,000) every statement below and every range of report.md hold at once.

Plan `81079ca199874b69`.


## Sight radius 0 (215000 seeds)

| rank | biome | E[D] from spawn | not separated from |
|---|---|---|---|
| 1 | mushroom_fields | 149,522 | none |
| 2 | windswept_gravelly_hills | 94,893 | none |
| 3 | stony_peaks | 83,873 | none |
| 4 | ice_spikes | 74,603 | none |
| 5 | eroded_badlands | 70,084 | none |
| 6 | pale_garden | 62,471 | none |
| 7 | mangrove_swamp | 58,464 | none |
| 8 to 10 | wooded_badlands | 54,092 | jagged_peaks, frozen_peaks |
| 8 to 10 | jagged_peaks | 53,418 | wooded_badlands, frozen_peaks |
| 8 to 10 | frozen_peaks | 53,370 | wooded_badlands, jagged_peaks |
| 11 | windswept_forest | 48,008 | none |
| 12 to 13 | badlands | 39,814 | windswept_savanna |
| 12 to 13 | windswept_savanna | 39,775 | badlands |
| 14 to 15 | deep_frozen_ocean | 36,392 | cherry_grove |
| 14 to 15 | cherry_grove | 35,329 | deep_frozen_ocean |
| 16 to 18 | windswept_hills | 34,001 | savanna_plateau, dappled_forest |
| 16 to 18 | dappled_forest | 33,807 | windswept_hills, savanna_plateau |
| 16 to 19 | savanna_plateau | 32,939 | windswept_hills, snowy_slopes, dappled_forest |
| 18 to 19 | snowy_slopes | 32,453 | savanna_plateau |
| 20 | warm_ocean | 31,319 | none |
| 21 | swamp | 29,579 | none |
| 22 to 23 | snowy_beach | 26,096 | bamboo_jungle |
| 22 to 24 | bamboo_jungle | 25,316 | snowy_beach, old_growth_spruce_taiga |
| 23 to 26 | old_growth_spruce_taiga | 24,585 | desert, old_growth_pine_taiga, bamboo_jungle |
| 24 to 26 | old_growth_pine_taiga | 24,052 | desert, old_growth_spruce_taiga |
| 24 to 26 | desert | 23,952 | old_growth_pine_taiga, old_growth_spruce_taiga |
| 27 to 28 | flower_forest | 22,362 | sunflower_plains |
| 27 to 28 | sunflower_plains | 22,075 | flower_forest |
| 29 to 30 | grove | 19,738 | frozen_ocean |
| 29 to 30 | frozen_ocean | 19,586 | grove |
| 31 to 33 | snowy_taiga | 16,450 | snowy_plains, deep_lukewarm_ocean |
| 31 to 33 | snowy_plains | 16,151 | snowy_taiga, deep_lukewarm_ocean |
| 31 to 33 | deep_lukewarm_ocean | 16,135 | snowy_plains, snowy_taiga |
| 34 to 35 | frozen_river | 15,541 | deep_cold_ocean |
| 34 to 35 | deep_cold_ocean | 15,071 | frozen_river |
| 36 to 37 | sparse_jungle | 11,463 | dark_forest |
| 36 to 37 | dark_forest | 11,203 | sparse_jungle |
| 38 to 39 | meadow | 10,442 | jungle |
| 38 to 39 | jungle | 10,329 | meadow |
| 40 | deep_ocean | 9,798 | none |
| 41 to 42 | savanna | 7,984 | lukewarm_ocean |
| 41 to 42 | lukewarm_ocean | 7,883 | savanna |
| 43 | cold_ocean | 7,145 | none |
| 44 | taiga | 6,888 | none |
| 45 | old_growth_birch_forest | 6,609 | none |
| 46 to 47 | birch_forest | 6,286 | stony_shore |
| 46 to 47 | stony_shore | 6,282 | birch_forest |
| 48 | ocean | 4,251 | none |
| 49 | sulfur_caves | 3,991 | none |
| 50 | deep_dark | 2,981 | none |
| 51 | beach | 2,563 | none |
| 52 | dripstone_caves | 1,966 | none |
| 53 | lush_caves | 1,728 | none |
| 54 | plains | 1,587 | none |
| 55 | forest | 1,164 | none |
| 56 | river | 763 | none |
