# Certified ranking from paired differences

Every biome pair is compared on the same seeds and rays (THEORY.md 9.1). A rank range says where the biome can be: rank 3 to 5 means exactly 2 biomes are certified rarer and the others in between are not separated from it. Except with chance at most 2e-06 (1 in 500,000) every statement below and every range of report.md hold at once.

Plan `5e61f6a48bc983ed`.


## Sight radius 128 (10000 seeds)

| rank | biome | E[D] from spawn | not separated from |
|---|---|---|---|
| 1 | mushroom_fields | 73,730 | none |
| 2 to 5 | windswept_gravelly_hills | 42,378 | ice_spikes, eroded_badlands, mangrove_swamp |
| 2 to 5 | eroded_badlands | 42,295 | windswept_gravelly_hills, ice_spikes, mangrove_swamp |
| 2 to 6 | ice_spikes | 40,322 | wooded_badlands, windswept_gravelly_hills, eroded_badlands, mangrove_swamp |
| 2 to 7 | mangrove_swamp | 38,084 | wooded_badlands, windswept_gravelly_hills, ice_spikes, eroded_badlands, stony_peaks |
| 4 to 7 | wooded_badlands | 36,752 | ice_spikes, stony_peaks, mangrove_swamp |
| 5 to 7 | stony_peaks | 35,618 | wooded_badlands, mangrove_swamp |
| 8 to 10 | badlands | 28,584 | deep_frozen_ocean, pale_garden |
| 8 to 11 | pale_garden | 26,573 | badlands, warm_ocean, deep_frozen_ocean |
| 8 to 11 | deep_frozen_ocean | 25,609 | badlands, warm_ocean, pale_garden |
| 9 to 13 | warm_ocean | 24,465 | windswept_forest, deep_frozen_ocean, frozen_peaks, pale_garden |
| 11 to 15 | windswept_forest | 21,851 | desert, warm_ocean, jagged_peaks, frozen_peaks |
| 11 to 16 | frozen_peaks | 21,783 | desert, swamp, windswept_forest, warm_ocean, jagged_peaks |
| 12 to 16 | jagged_peaks | 21,514 | desert, swamp, windswept_forest, frozen_peaks |
| 12 to 17 | desert | 19,922 | swamp, windswept_forest, windswept_savanna, jagged_peaks, frozen_peaks |
| 13 to 19 | swamp | 19,287 | desert, snowy_beach, windswept_savanna, jagged_peaks, frozen_peaks, dappled_forest |
| 15 to 21 | windswept_savanna | 17,787 | desert, swamp, snowy_beach, savanna_plateau, snowy_slopes, dappled_forest |
| 16 to 22 | snowy_beach | 17,193 | windswept_hills, swamp, savanna_plateau, windswept_savanna, snowy_slopes, dappled_forest |
| 16 to 23 | dappled_forest | 17,151 | 7 biomes |
| 17 to 24 | savanna_plateau | 16,585 | 7 biomes |
| 17 to 24 | snowy_slopes | 16,163 | 7 biomes |
| 18 to 24 | windswept_hills | 15,860 | frozen_ocean, snowy_beach, savanna_plateau, snowy_slopes, cherry_grove, dappled_forest |
| 19 to 25 | frozen_ocean | 15,357 | windswept_hills, savanna_plateau, bamboo_jungle, snowy_slopes, cherry_grove, dappled_forest |
| 20 to 28 | cherry_grove | 14,782 | 8 biomes |
| 23 to 30 | bamboo_jungle | 13,742 | 7 biomes |
| 24 to 30 | snowy_taiga | 13,204 | frozen_river, snowy_plains, old_growth_pine_taiga, old_growth_spruce_taiga, bamboo_jungle, cherry_grove |
| 24 to 30 | old_growth_spruce_taiga | 13,119 | frozen_river, snowy_plains, snowy_taiga, old_growth_pine_taiga, bamboo_jungle, cherry_grove |
| 24 to 30 | snowy_plains | 13,043 | frozen_river, snowy_taiga, old_growth_pine_taiga, old_growth_spruce_taiga, bamboo_jungle, cherry_grove |
| 25 to 30 | old_growth_pine_taiga | 12,941 | frozen_river, snowy_plains, snowy_taiga, old_growth_spruce_taiga, bamboo_jungle |
| 25 to 33 | frozen_river | 12,513 | 8 biomes |
| 30 to 35 | flower_forest | 11,318 | frozen_river, deep_lukewarm_ocean, deep_cold_ocean, sunflower_plains, grove |
| 30 to 35 | sunflower_plains | 11,258 | frozen_river, deep_lukewarm_ocean, deep_cold_ocean, flower_forest, grove |
| 30 to 35 | deep_lukewarm_ocean | 11,144 | frozen_river, deep_cold_ocean, sunflower_plains, flower_forest, grove |
| 31 to 35 | grove | 10,741 | deep_lukewarm_ocean, deep_cold_ocean, sunflower_plains, flower_forest |
| 31 to 35 | deep_cold_ocean | 10,046 | deep_lukewarm_ocean, sunflower_plains, flower_forest, grove |
| 36 to 39 | sparse_jungle | 6,838 | jungle, deep_ocean, dark_forest |
| 36 to 40 | dark_forest | 6,632 | jungle, sparse_jungle, deep_ocean, savanna |
| 36 to 39 | jungle | 6,624 | sparse_jungle, deep_ocean, dark_forest |
| 36 to 41 | deep_ocean | 6,459 | jungle, sparse_jungle, dark_forest, savanna, lukewarm_ocean |
| 38 to 43 | savanna | 5,772 | deep_ocean, dark_forest, lukewarm_ocean, cold_ocean, meadow |
| 39 to 43 | lukewarm_ocean | 5,727 | deep_ocean, savanna, cold_ocean, meadow |
| 40 to 44 | cold_ocean | 5,057 | taiga, savanna, lukewarm_ocean, meadow |
| 40 to 44 | meadow | 5,054 | taiga, savanna, lukewarm_ocean, cold_ocean |
| 42 to 44 | taiga | 4,805 | cold_ocean, meadow |
| 45 to 47 | old_growth_birch_forest | 3,468 | stony_shore, birch_forest |
| 45 to 47 | stony_shore | 3,455 | birch_forest, old_growth_birch_forest |
| 45 to 47 | birch_forest | 3,404 | stony_shore, old_growth_birch_forest |
| 48 | ocean | 2,758 | none |
| 49 to 50 | deep_dark | 1,893 | sulfur_caves |
| 49 to 50 | sulfur_caves | 1,888 | deep_dark |
| 51 to 52 | beach | 1,227 | dripstone_caves |
| 51 to 53 | dripstone_caves | 1,191 | beach, lush_caves |
| 52 to 53 | lush_caves | 1,016 | dripstone_caves |
| 54 | plains | 830 | none |
| 55 | forest | 601 | none |
| 56 | river | 283 | none |

## Sight radius 512 (10000 seeds)

| rank | biome | E[D] from spawn | not separated from |
|---|---|---|---|
| 1 | mushroom_fields | 31,630 | none |
| 2 | eroded_badlands | 23,970 | none |
| 3 to 6 | wooded_badlands | 21,729 | windswept_gravelly_hills, ice_spikes, mangrove_swamp |
| 3 to 7 | ice_spikes | 20,363 | badlands, wooded_badlands, windswept_gravelly_hills, mangrove_swamp |
| 3 to 7 | mangrove_swamp | 20,083 | badlands, wooded_badlands, windswept_gravelly_hills, ice_spikes |
| 3 to 7 | windswept_gravelly_hills | 19,530 | badlands, wooded_badlands, ice_spikes, mangrove_swamp |
| 4 to 8 | badlands | 18,169 | windswept_gravelly_hills, ice_spikes, stony_peaks, mangrove_swamp |
| 7 to 10 | stony_peaks | 16,800 | badlands, warm_ocean, deep_frozen_ocean |
| 8 to 10 | warm_ocean | 16,171 | deep_frozen_ocean, stony_peaks |
| 8 to 11 | deep_frozen_ocean | 15,179 | desert, warm_ocean, stony_peaks |
| 10 to 11 | desert | 13,821 | deep_frozen_ocean |
| 12 to 16 | snowy_beach | 11,075 | swamp, frozen_ocean, windswept_forest, pale_garden |
| 12 to 16 | pale_garden | 10,637 | swamp, frozen_ocean, snowy_beach, windswept_forest |
| 12 to 17 | frozen_ocean | 10,171 | swamp, snowy_beach, windswept_forest, frozen_peaks, pale_garden |
| 12 to 20 | swamp | 9,859 | 8 biomes |
| 12 to 21 | windswept_forest | 9,754 | 9 biomes |
| 14 to 23 | frozen_peaks | 9,105 | 9 biomes |
| 15 to 23 | snowy_taiga | 9,032 | 8 biomes |
| 15 to 23 | snowy_plains | 8,934 | 8 biomes |
| 15 to 23 | jagged_peaks | 8,820 | 8 biomes |
| 16 to 24 | frozen_river | 8,575 | 8 biomes |
| 17 to 26 | savanna_plateau | 8,179 | 9 biomes |
| 17 to 26 | windswept_savanna | 8,150 | 9 biomes |
| 21 to 27 | dappled_forest | 7,650 | windswept_hills, frozen_river, savanna_plateau, windswept_savanna, bamboo_jungle, snowy_slopes |
| 22 to 27 | windswept_hills | 7,366 | savanna_plateau, windswept_savanna, bamboo_jungle, snowy_slopes, dappled_forest |
| 22 to 27 | snowy_slopes | 7,321 | windswept_hills, savanna_plateau, windswept_savanna, bamboo_jungle, dappled_forest |
| 24 to 31 | bamboo_jungle | 6,688 | 7 biomes |
| 27 to 32 | deep_lukewarm_ocean | 6,036 | old_growth_pine_taiga, deep_cold_ocean, old_growth_spruce_taiga, bamboo_jungle, cherry_grove |
| 27 to 31 | old_growth_spruce_taiga | 6,008 | old_growth_pine_taiga, deep_lukewarm_ocean, bamboo_jungle, cherry_grove |
| 27 to 32 | cherry_grove | 6,001 | old_growth_pine_taiga, deep_lukewarm_ocean, deep_cold_ocean, old_growth_spruce_taiga, bamboo_jungle |
| 27 to 33 | old_growth_pine_taiga | 5,862 | deep_lukewarm_ocean, deep_cold_ocean, old_growth_spruce_taiga, bamboo_jungle, grove, cherry_grove |
| 29 to 34 | deep_cold_ocean | 5,341 | old_growth_pine_taiga, deep_lukewarm_ocean, flower_forest, grove, cherry_grove |
| 31 to 35 | grove | 5,177 | old_growth_pine_taiga, deep_cold_ocean, sunflower_plains, flower_forest |
| 32 to 35 | flower_forest | 4,753 | deep_cold_ocean, sunflower_plains, grove |
| 33 to 35 | sunflower_plains | 4,659 | flower_forest, grove |
| 36 to 39 | sparse_jungle | 3,889 | jungle, savanna, lukewarm_ocean |
| 36 to 39 | jungle | 3,815 | sparse_jungle, savanna, lukewarm_ocean |
| 36 to 41 | lukewarm_ocean | 3,582 | jungle, sparse_jungle, deep_ocean, savanna, cold_ocean |
| 36 to 41 | savanna | 3,479 | jungle, sparse_jungle, deep_ocean, lukewarm_ocean, cold_ocean |
| 38 to 43 | deep_ocean | 3,107 | taiga, dark_forest, savanna, lukewarm_ocean, cold_ocean |
| 38 to 43 | cold_ocean | 3,024 | taiga, deep_ocean, dark_forest, savanna, lukewarm_ocean |
| 40 to 43 | dark_forest | 2,850 | taiga, deep_ocean, cold_ocean |
| 40 to 43 | taiga | 2,843 | deep_ocean, dark_forest, cold_ocean |
| 44 | meadow | 2,330 | none |
| 45 to 48 | old_growth_birch_forest | 1,606 | ocean, stony_shore, birch_forest |
| 45 to 48 | stony_shore | 1,585 | ocean, birch_forest, old_growth_birch_forest |
| 45 to 48 | birch_forest | 1,576 | ocean, stony_shore, old_growth_birch_forest |
| 45 to 48 | ocean | 1,462 | stony_shore, birch_forest, old_growth_birch_forest |
| 49 to 50 | deep_dark | 868 | sulfur_caves |
| 49 to 50 | sulfur_caves | 748 | deep_dark |
| 51 to 52 | beach | 532 | dripstone_caves |
| 51 to 54 | dripstone_caves | 419 | plains, beach, lush_caves |
| 52 to 54 | lush_caves | 370 | plains, dripstone_caves |
| 52 to 55 | plains | 352 | forest, dripstone_caves, lush_caves |
| 54 to 56 | forest | 279 | plains, river |
| 55 to 56 | river | 164 | forest |
