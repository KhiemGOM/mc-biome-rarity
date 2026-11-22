# Certified ranking from paired differences

Every biome pair is compared on the same seeds and rays (THEORY.md 9.1). A rank range says where the biome can be: rank 3 to 5 means exactly 2 biomes are certified rarer and the others in between are not separated from it. Except with chance at most 2e-06 (1 in 500,000) every statement below and every range of report.md hold at once.

Plan `c838d3c2e97b6c69`.


## Sight radius 0 (22500 seeds)

| rank | biome | E[D] from spawn | not separated from |
|---|---|---|---|
| 1 | mushroom_fields | 150,486 | none |
| 2 | pale_garden | 113,571 | none |
| 3 | windswept_gravelly_hills | 94,917 | none |
| 4 | stony_peaks | 84,015 | none |
| 5 to 6 | ice_spikes | 75,331 | eroded_badlands |
| 5 to 6 | eroded_badlands | 70,427 | ice_spikes |
| 7 | mangrove_swamp | 58,851 | none |
| 8 to 10 | frozen_peaks | 53,941 | wooded_badlands, jagged_peaks |
| 8 to 10 | wooded_badlands | 53,816 | jagged_peaks, frozen_peaks |
| 8 to 10 | jagged_peaks | 53,718 | wooded_badlands, frozen_peaks |
| 11 | windswept_forest | 48,126 | none |
| 12 to 13 | badlands | 39,872 | windswept_savanna |
| 12 to 14 | windswept_savanna | 39,399 | badlands, deep_frozen_ocean |
| 13 to 16 | deep_frozen_ocean | 36,505 | windswept_hills, windswept_savanna, cherry_grove |
| 14 to 17 | cherry_grove | 35,572 | windswept_hills, savanna_plateau, deep_frozen_ocean |
| 14 to 19 | windswept_hills | 33,807 | savanna_plateau, warm_ocean, deep_frozen_ocean, snowy_slopes, cherry_grove |
| 15 to 19 | savanna_plateau | 33,409 | windswept_hills, warm_ocean, snowy_slopes, cherry_grove |
| 16 to 19 | snowy_slopes | 32,657 | windswept_hills, savanna_plateau, warm_ocean |
| 16 to 20 | warm_ocean | 31,510 | windswept_hills, swamp, savanna_plateau, snowy_slopes |
| 19 to 20 | swamp | 29,228 | warm_ocean |
| 21 to 24 | snowy_beach | 26,143 | desert, old_growth_spruce_taiga, bamboo_jungle |
| 21 to 25 | bamboo_jungle | 25,478 | desert, snowy_beach, old_growth_pine_taiga, old_growth_spruce_taiga |
| 21 to 25 | old_growth_spruce_taiga | 24,560 | desert, snowy_beach, old_growth_pine_taiga, bamboo_jungle |
| 21 to 26 | desert | 24,107 | snowy_beach, old_growth_pine_taiga, flower_forest, old_growth_spruce_taiga, bamboo_jungle |
| 22 to 26 | old_growth_pine_taiga | 23,883 | desert, flower_forest, old_growth_spruce_taiga, bamboo_jungle |
| 24 to 27 | flower_forest | 22,555 | desert, old_growth_pine_taiga, sunflower_plains |
| 26 to 27 | sunflower_plains | 21,973 | flower_forest |
| 28 to 29 | grove | 19,865 | frozen_ocean |
| 28 to 29 | frozen_ocean | 19,668 | grove |
| 30 to 32 | snowy_taiga | 16,492 | snowy_plains, deep_lukewarm_ocean |
| 30 to 33 | snowy_plains | 16,406 | frozen_river, snowy_taiga, deep_lukewarm_ocean |
| 30 to 33 | deep_lukewarm_ocean | 16,249 | frozen_river, snowy_plains, snowy_taiga |
| 31 to 34 | frozen_river | 15,706 | snowy_plains, deep_lukewarm_ocean, deep_cold_ocean |
| 33 to 34 | deep_cold_ocean | 15,017 | frozen_river |
| 35 to 36 | sparse_jungle | 11,385 | dark_forest |
| 35 to 37 | dark_forest | 11,239 | sparse_jungle, meadow |
| 36 to 39 | meadow | 10,453 | jungle, deep_ocean, dark_forest |
| 37 to 39 | jungle | 10,311 | deep_ocean, meadow |
| 37 to 39 | deep_ocean | 9,796 | jungle, meadow |
| 40 to 41 | savanna | 7,963 | lukewarm_ocean |
| 40 to 41 | lukewarm_ocean | 7,848 | savanna |
| 42 to 44 | cold_ocean | 7,174 | taiga, old_growth_birch_forest |
| 42 to 44 | taiga | 6,916 | cold_ocean, old_growth_birch_forest |
| 42 to 46 | old_growth_birch_forest | 6,630 | taiga, stony_shore, birch_forest, cold_ocean |
| 44 to 46 | birch_forest | 6,360 | stony_shore, old_growth_birch_forest |
| 44 to 46 | stony_shore | 6,302 | birch_forest, old_growth_birch_forest |
| 47 | ocean | 4,259 | none |
| 48 | deep_dark | 2,970 | none |
| 49 | beach | 2,552 | none |
| 50 | dripstone_caves | 1,936 | none |
| 51 | lush_caves | 1,738 | none |
| 52 | plains | 1,566 | none |
| 53 | forest | 1,153 | none |
| 54 | river | 749 | none |
