# Certified ranking from paired differences

Every biome pair is compared on the same seeds and rays (THEORY.md 9.1). A rank range says where the biome can be: rank 3 to 5 means exactly 2 biomes are certified rarer and the others in between are not separated from it. Except with chance at most 2e-06 (1 in 500,000) every statement below and every range of report.md hold at once.

Plan `2e048abc0a486968`.


## Sight radius 128 (9750 seeds)

| rank | biome | E[D] from spawn | not separated from |
|---|---|---|---|
| 1 | mushroom_fields | 72,527 | none |
| 2 to 6 | pale_garden | 42,981 | windswept_gravelly_hills, ice_spikes, eroded_badlands, mangrove_swamp |
| 2 to 6 | eroded_badlands | 42,754 | windswept_gravelly_hills, ice_spikes, mangrove_swamp, pale_garden |
| 2 to 6 | windswept_gravelly_hills | 42,711 | ice_spikes, eroded_badlands, mangrove_swamp, pale_garden |
| 2 to 8 | ice_spikes | 40,336 | wooded_badlands, windswept_gravelly_hills, eroded_badlands, stony_peaks, mangrove_swamp, pale_garden |
| 2 to 8 | mangrove_swamp | 37,997 | wooded_badlands, windswept_gravelly_hills, ice_spikes, eroded_badlands, stony_peaks, pale_garden |
| 5 to 8 | wooded_badlands | 36,750 | ice_spikes, stony_peaks, mangrove_swamp |
| 5 to 8 | stony_peaks | 36,151 | wooded_badlands, ice_spikes, mangrove_swamp |
| 9 to 10 | badlands | 29,020 | deep_frozen_ocean |
| 9 to 11 | deep_frozen_ocean | 25,431 | badlands, warm_ocean |
| 10 to 14 | warm_ocean | 24,510 | windswept_forest, deep_frozen_ocean, jagged_peaks, frozen_peaks |
| 11 to 15 | windswept_forest | 22,084 | desert, warm_ocean, jagged_peaks, frozen_peaks |
| 11 to 16 | frozen_peaks | 21,605 | desert, swamp, windswept_forest, warm_ocean, jagged_peaks |
| 11 to 16 | jagged_peaks | 21,462 | desert, swamp, windswept_forest, warm_ocean, frozen_peaks |
| 12 to 17 | desert | 19,995 | swamp, windswept_forest, windswept_savanna, jagged_peaks, frozen_peaks |
| 13 to 18 | swamp | 19,242 | desert, snowy_beach, windswept_savanna, jagged_peaks, frozen_peaks |
| 15 to 21 | windswept_savanna | 17,716 | desert, windswept_hills, swamp, snowy_beach, savanna_plateau, snowy_slopes |
| 17 to 22 | savanna_plateau | 16,897 | windswept_hills, frozen_ocean, snowy_beach, windswept_savanna, snowy_slopes |
| 16 to 22 | snowy_beach | 16,859 | windswept_hills, swamp, savanna_plateau, windswept_savanna, snowy_slopes, cherry_grove |
| 17 to 23 | snowy_slopes | 16,215 | windswept_hills, frozen_ocean, snowy_beach, savanna_plateau, windswept_savanna, cherry_grove |
| 17 to 24 | windswept_hills | 15,858 | 7 biomes |
| 19 to 24 | frozen_ocean | 15,063 | windswept_hills, savanna_plateau, bamboo_jungle, snowy_slopes, cherry_grove |
| 19 to 24 | cherry_grove | 14,849 | windswept_hills, frozen_ocean, snowy_beach, bamboo_jungle, snowy_slopes |
| 21 to 29 | bamboo_jungle | 13,963 | 8 biomes |
| 24 to 30 | old_growth_spruce_taiga | 12,979 | frozen_river, snowy_plains, snowy_taiga, old_growth_pine_taiga, flower_forest, bamboo_jungle |
| 24 to 31 | old_growth_pine_taiga | 12,806 | 7 biomes |
| 24 to 32 | snowy_taiga | 12,762 | 8 biomes |
| 24 to 32 | snowy_plains | 12,596 | 8 biomes |
| 24 to 33 | frozen_river | 12,076 | 9 biomes |
| 25 to 33 | flower_forest | 11,540 | 8 biomes |
| 26 to 34 | sunflower_plains | 11,415 | 8 biomes |
| 27 to 34 | deep_lukewarm_ocean | 11,117 | 7 biomes |
| 29 to 34 | grove | 10,654 | frozen_river, deep_lukewarm_ocean, deep_cold_ocean, sunflower_plains, flower_forest |
| 31 to 34 | deep_cold_ocean | 10,152 | deep_lukewarm_ocean, sunflower_plains, grove |
| 35 to 38 | sparse_jungle | 7,091 | jungle, deep_ocean, dark_forest |
| 35 to 38 | jungle | 6,735 | sparse_jungle, deep_ocean, dark_forest |
| 35 to 40 | deep_ocean | 6,518 | jungle, sparse_jungle, dark_forest, savanna, lukewarm_ocean |
| 35 to 40 | dark_forest | 6,444 | jungle, sparse_jungle, deep_ocean, savanna, lukewarm_ocean |
| 37 to 42 | lukewarm_ocean | 5,883 | deep_ocean, dark_forest, savanna, cold_ocean, meadow |
| 37 to 42 | savanna | 5,853 | deep_ocean, dark_forest, lukewarm_ocean, cold_ocean, meadow |
| 39 to 43 | meadow | 5,091 | taiga, savanna, lukewarm_ocean, cold_ocean |
| 39 to 43 | cold_ocean | 5,060 | taiga, savanna, lukewarm_ocean, meadow |
| 41 to 43 | taiga | 4,743 | cold_ocean, meadow |
| 44 to 46 | old_growth_birch_forest | 3,542 | stony_shore, birch_forest |
| 44 to 46 | stony_shore | 3,511 | birch_forest, old_growth_birch_forest |
| 44 to 46 | birch_forest | 3,450 | stony_shore, old_growth_birch_forest |
| 47 | ocean | 2,827 | none |
| 48 | deep_dark | 1,910 | none |
| 49 to 50 | beach | 1,234 | dripstone_caves |
| 49 to 51 | dripstone_caves | 1,162 | beach, lush_caves |
| 50 to 52 | lush_caves | 1,006 | plains, dripstone_caves |
| 51 to 52 | plains | 837 | lush_caves |
| 53 | forest | 606 | none |
| 54 | river | 289 | none |

## Sight radius 512 (10250 seeds)

| rank | biome | E[D] from spawn | not separated from |
|---|---|---|---|
| 1 | mushroom_fields | 31,062 | none |
| 2 | eroded_badlands | 24,471 | none |
| 3 to 6 | wooded_badlands | 21,796 | windswept_gravelly_hills, ice_spikes, mangrove_swamp |
| 3 to 7 | mangrove_swamp | 20,241 | badlands, wooded_badlands, windswept_gravelly_hills, ice_spikes |
| 3 to 7 | ice_spikes | 20,040 | badlands, wooded_badlands, windswept_gravelly_hills, mangrove_swamp |
| 3 to 8 | windswept_gravelly_hills | 19,451 | badlands, wooded_badlands, ice_spikes, stony_peaks, mangrove_swamp |
| 4 to 9 | badlands | 18,463 | windswept_gravelly_hills, ice_spikes, stony_peaks, mangrove_swamp, pale_garden |
| 6 to 10 | stony_peaks | 17,192 | badlands, warm_ocean, windswept_gravelly_hills, pale_garden |
| 8 to 11 | warm_ocean | 16,366 | deep_frozen_ocean, stony_peaks, pale_garden |
| 7 to 11 | pale_garden | 16,309 | badlands, warm_ocean, deep_frozen_ocean, stony_peaks |
| 9 to 12 | deep_frozen_ocean | 14,891 | desert, warm_ocean, pale_garden |
| 11 to 12 | desert | 14,070 | deep_frozen_ocean |
| 13 to 16 | snowy_beach | 10,712 | swamp, frozen_ocean, windswept_forest |
| 13 to 18 | frozen_ocean | 9,878 | swamp, snowy_beach, windswept_forest, jagged_peaks, frozen_peaks |
| 13 to 20 | windswept_forest | 9,761 | 7 biomes |
| 13 to 20 | swamp | 9,717 | 7 biomes |
| 14 to 23 | jagged_peaks | 9,190 | 9 biomes |
| 14 to 23 | frozen_peaks | 9,108 | 9 biomes |
| 15 to 23 | snowy_taiga | 8,715 | 8 biomes |
| 15 to 23 | snowy_plains | 8,682 | 8 biomes |
| 17 to 25 | frozen_river | 8,385 | 8 biomes |
| 17 to 25 | savanna_plateau | 8,316 | 8 biomes |
| 17 to 25 | windswept_savanna | 8,120 | 8 biomes |
| 21 to 26 | snowy_slopes | 7,422 | windswept_hills, frozen_river, savanna_plateau, windswept_savanna, bamboo_jungle |
| 21 to 26 | windswept_hills | 7,390 | frozen_river, savanna_plateau, windswept_savanna, bamboo_jungle, snowy_slopes |
| 24 to 30 | bamboo_jungle | 6,775 | windswept_hills, old_growth_pine_taiga, deep_lukewarm_ocean, old_growth_spruce_taiga, snowy_slopes, cherry_grove |
| 26 to 31 | deep_lukewarm_ocean | 6,152 | old_growth_pine_taiga, deep_cold_ocean, old_growth_spruce_taiga, bamboo_jungle, cherry_grove |
| 26 to 32 | old_growth_spruce_taiga | 5,963 | old_growth_pine_taiga, deep_lukewarm_ocean, deep_cold_ocean, bamboo_jungle, grove, cherry_grove |
| 26 to 32 | old_growth_pine_taiga | 5,920 | deep_lukewarm_ocean, deep_cold_ocean, old_growth_spruce_taiga, bamboo_jungle, grove, cherry_grove |
| 26 to 32 | cherry_grove | 5,900 | old_growth_pine_taiga, deep_lukewarm_ocean, deep_cold_ocean, old_growth_spruce_taiga, bamboo_jungle, grove |
| 27 to 34 | deep_cold_ocean | 5,334 | 7 biomes |
| 28 to 34 | grove | 5,260 | old_growth_pine_taiga, deep_cold_ocean, sunflower_plains, flower_forest, old_growth_spruce_taiga, cherry_grove |
| 31 to 34 | flower_forest | 4,786 | deep_cold_ocean, sunflower_plains, grove |
| 31 to 34 | sunflower_plains | 4,747 | deep_cold_ocean, flower_forest, grove |
| 35 to 37 | sparse_jungle | 3,948 | jungle, lukewarm_ocean |
| 35 to 38 | jungle | 3,836 | sparse_jungle, savanna, lukewarm_ocean |
| 35 to 39 | lukewarm_ocean | 3,650 | jungle, sparse_jungle, savanna, cold_ocean |
| 36 to 40 | savanna | 3,511 | jungle, deep_ocean, lukewarm_ocean, cold_ocean |
| 38 to 42 | deep_ocean | 3,113 | taiga, dark_forest, savanna, cold_ocean |
| 37 to 42 | cold_ocean | 3,025 | taiga, deep_ocean, dark_forest, savanna, lukewarm_ocean |
| 39 to 42 | dark_forest | 2,889 | taiga, deep_ocean, cold_ocean |
| 39 to 42 | taiga | 2,854 | deep_ocean, dark_forest, cold_ocean |
| 43 | meadow | 2,332 | none |
| 44 to 47 | old_growth_birch_forest | 1,613 | ocean, stony_shore, birch_forest |
| 44 to 47 | birch_forest | 1,608 | ocean, stony_shore, old_growth_birch_forest |
| 44 to 47 | stony_shore | 1,595 | ocean, birch_forest, old_growth_birch_forest |
| 44 to 47 | ocean | 1,478 | stony_shore, birch_forest, old_growth_birch_forest |
| 48 | deep_dark | 891 | none |
| 49 | beach | 556 | none |
| 50 to 52 | dripstone_caves | 395 | plains, lush_caves |
| 50 to 53 | lush_caves | 359 | plains, forest, dripstone_caves |
| 50 to 52 | plains | 359 | dripstone_caves, lush_caves |
| 52 to 54 | forest | 274 | river, lush_caves |
| 53 to 54 | river | 169 | forest |
