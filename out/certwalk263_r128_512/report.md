# Walk from spawn to each biome

Every number is **estimate ± ε**. The true model value is inside every range at once, except with chance at most 1e-06 over the random seeds (1 in 1,000,000). Geometry error is 0 and rounding at most ±0.5 blocks (both certain, included in ε). The part past the cap rests on the constant hazard assumption and is shown as the tail share; the lower end of each range needs no assumption at all.

Plan `5e61f6a48bc983ed`, code `b31f22e50a`.

**Layers (assumption, THEORY.md 8.9):** a biome counts in a 4x4 column if it is at any of the 96 layers from y = -64 to 319, so a cave biome counts as found when you pass within the radius of its column, at any depth, reachable or not.


## Sight radius 128, cap 300,000 blocks, per biome cap 4x its pilot walk (all 56 biomes, rarest first, most common last)

| rank | biome | E[D] from spawn | ± ε | guaranteed at least | tail share | from a random start | spawn bias | seeds |
|---|---|---|---|---|---|---|---|---|
| 1 | mushroom_fields | 73,730 | 6,048 | 67,698 | 2.3% | not run | | 10000 |
| 2 (tied) | windswept_gravelly_hills | 42,378 | 3,375 | 39,154 | 1.9% | not run | | 10000 |
| 2 (tied) | eroded_badlands | 42,295 | 3,352 | 38,845 | 2.4% | not run | | 10000 |
| 2 (tied) | ice_spikes | 40,322 | 3,111 | 37,417 | 1.3% | not run | | 10000 |
| 2 (tied) | mangrove_swamp | 38,084 | 2,974 | 35,066 | 2.2% | not run | | 10000 |
| 2 (tied) | wooded_badlands | 36,752 | 3,010 | 33,753 | 2.3% | not run | | 10000 |
| 2 (tied) | stony_peaks | 35,618 | 2,767 | 32,936 | 1.6% | not run | | 10000 |
| 8 (tied) | badlands | 28,584 | 2,288 | 26,245 | 2.4% | not run | | 10000 |
| 8 (tied) | pale_garden | 26,573 | 2,273 | 24,368 | 2.1% | not run | | 10000 |
| 8 (tied) | deep_frozen_ocean | 25,609 | 2,226 | 23,526 | 1.8% | not run | | 10000 |
| 8 (tied) | warm_ocean | 24,465 | 2,224 | 22,267 | 2.6% | not run | | 10000 |
| 8 (tied) | windswept_forest | 21,851 | 1,952 | 20,032 | 1.8% | not run | | 10000 |
| 8 (tied) | frozen_peaks | 21,783 | 1,869 | 20,020 | 1.7% | not run | | 10000 |
| 8 (tied) | jagged_peaks | 21,514 | 1,897 | 19,696 | 2.0% | not run | | 10000 |
| 8 (tied) | desert | 19,922 | 1,843 | 18,133 | 2.4% | not run | | 10000 |
| 8 (tied) | swamp | 19,287 | 1,732 | 17,698 | 1.7% | not run | | 10000 |
| 8 (tied) | windswept_savanna | 17,787 | 1,598 | 16,303 | 1.9% | not run | | 10000 |
| 8 (tied) | snowy_beach | 17,193 | 1,520 | 15,772 | 1.7% | not run | | 10000 |
| 8 (tied) | dappled_forest | 17,151 | 1,540 | 15,719 | 1.8% | not run | | 10000 |
| 8 (tied) | savanna_plateau | 16,585 | 1,484 | 15,073 | 2.9% | not run | | 10000 |
| 8 (tied) | snowy_slopes | 16,163 | 1,448 | 14,789 | 2.0% | not run | | 10000 |
| 8 (tied) | windswept_hills | 15,860 | 1,399 | 14,557 | 1.7% | not run | | 10000 |
| 8 (tied) | frozen_ocean | 15,357 | 1,400 | 14,049 | 1.9% | not run | | 10000 |
| 8 (tied) | cherry_grove | 14,782 | 1,290 | 13,590 | 1.7% | not run | | 10000 |
| 8 (tied) | bamboo_jungle | 13,742 | 1,211 | 12,590 | 1.7% | not run | | 10000 |
| 8 (tied) | snowy_taiga | 13,204 | 1,242 | 12,046 | 2.0% | not run | | 10000 |
| 8 (tied) | old_growth_spruce_taiga | 13,119 | 1,203 | 12,032 | 1.7% | not run | | 10000 |
| 8 (tied) | snowy_plains | 13,043 | 1,215 | 11,873 | 2.2% | not run | | 10000 |
| 8 (tied) | old_growth_pine_taiga | 12,941 | 1,164 | 11,899 | 1.5% | not run | | 10000 |
| 8 (tied) | frozen_river | 12,513 | 1,184 | 11,368 | 2.3% | not run | | 10000 |
| 8 (tied) | flower_forest | 11,318 | 1,023 | 10,375 | 1.7% | not run | | 10000 |
| 8 (tied) | sunflower_plains | 11,258 | 1,058 | 10,251 | 2.4% | not run | | 10000 |
| 8 (tied) | deep_lukewarm_ocean | 11,144 | 994 | 10,128 | 2.8% | not run | | 10000 |
| 8 (tied) | grove | 10,741 | 995 | 9,780 | 2.4% | not run | | 10000 |
| 8 (tied) | deep_cold_ocean | 10,046 | 901 | 9,188 | 2.0% | not run | | 10000 |
| 36 (tied) | sparse_jungle | 6,838 | 655 | 6,198 | 2.5% | not run | | 10000 |
| 36 (tied) | dark_forest | 6,632 | 637 | 5,998 | 2.9% | not run | | 10000 |
| 36 (tied) | jungle | 6,624 | 653 | 5,967 | 3.1% | not run | | 10000 |
| 36 (tied) | deep_ocean | 6,459 | 596 | 5,895 | 2.3% | not run | | 10000 |
| 36 (tied) | savanna | 5,772 | 591 | 5,174 | 3.4% | not run | | 10000 |
| 36 (tied) | lukewarm_ocean | 5,727 | 571 | 5,158 | 3.0% | not run | | 10000 |
| 36 (tied) | cold_ocean | 5,057 | 518 | 4,578 | 2.3% | not run | | 10000 |
| 36 (tied) | meadow | 5,054 | 468 | 4,609 | 2.0% | not run | | 10000 |
| 36 (tied) | taiga | 4,805 | 507 | 4,319 | 2.9% | not run | | 10000 |
| 45 (tied) | old_growth_birch_forest | 3,468 | 339 | 3,134 | 2.7% | not run | | 10000 |
| 45 (tied) | stony_shore | 3,455 | 347 | 3,109 | 3.0% | not run | | 10000 |
| 45 (tied) | birch_forest | 3,404 | 339 | 3,073 | 2.8% | not run | | 10000 |
| 48 | ocean | 2,758 | 287 | 2,483 | 2.7% | not run | | 10000 |
| 49 (tied) | deep_dark | 1,893 | 222 | 1,661 | 4.5% | not run | | 10000 |
| 49 (tied) | sulfur_caves | 1,888 | 197 | 1,695 | 3.0% | not run | | 10000 |
| 51 (tied) | beach | 1,227 | 158 | 1,050 | 6.6% | not run | | 10000 |
| 51 (tied) | dripstone_caves | 1,191 | 156 | 1,020 | 6.3% | not run | | 10000 |
| 51 (tied) | lush_caves | 1,016 | 121 | 884 | 5.4% | not run | | 10000 |
| 51 (tied) | plains | 830 | 118 | 709 | 5.9% | not run | | 10000 |
| 55 | forest | 601 | 104 | 490 | 9.3% | not run | | 10000 |
| 56 | river | 283 | 90 | 203 | 17.7% | not run | | 10000 |

## Sight radius 512, cap 300,000 blocks, per biome cap 4x its pilot walk (all 56 biomes, rarest first, most common last)

| rank | biome | E[D] from spawn | ± ε | guaranteed at least | tail share | from a random start | spawn bias | seeds |
|---|---|---|---|---|---|---|---|---|
| 1 | mushroom_fields | 31,630 | 2,535 | 29,178 | 1.9% | not run | | 10000 |
| 2 (tied) | eroded_badlands | 23,970 | 1,996 | 21,854 | 3.0% | not run | | 10000 |
| 2 (tied) | wooded_badlands | 21,729 | 1,742 | 20,064 | 1.7% | not run | | 10000 |
| 2 (tied) | ice_spikes | 20,363 | 1,573 | 18,893 | 1.1% | not run | | 10000 |
| 2 (tied) | mangrove_swamp | 20,083 | 1,583 | 18,522 | 1.8% | not run | | 10000 |
| 2 (tied) | windswept_gravelly_hills | 19,530 | 1,530 | 18,030 | 1.7% | not run | | 10000 |
| 2 (tied) | badlands | 18,169 | 1,478 | 16,702 | 2.1% | not run | | 10000 |
| 2 (tied) | stony_peaks | 16,800 | 1,385 | 15,392 | 2.5% | not run | | 10000 |
| 2 (tied) | warm_ocean | 16,171 | 1,527 | 14,617 | 3.0% | not run | | 10000 |
| 2 (tied) | deep_frozen_ocean | 15,179 | 1,394 | 13,806 | 2.5% | not run | | 10000 |
| 2 (tied) | desert | 13,821 | 1,298 | 12,522 | 2.6% | not run | | 10000 |
| 12 (tied) | snowy_beach | 11,075 | 1,070 | 10,015 | 2.9% | not run | | 10000 |
| 12 (tied) | pale_garden | 10,637 | 989 | 9,662 | 2.6% | not run | | 10000 |
| 12 (tied) | frozen_ocean | 10,171 | 1,026 | 9,156 | 3.1% | not run | | 10000 |
| 12 (tied) | swamp | 9,859 | 906 | 9,012 | 1.9% | not run | | 10000 |
| 12 (tied) | windswept_forest | 9,754 | 911 | 8,904 | 2.1% | not run | | 10000 |
| 12 (tied) | frozen_peaks | 9,105 | 830 | 8,329 | 1.8% | not run | | 10000 |
| 12 (tied) | snowy_taiga | 9,032 | 903 | 8,145 | 2.8% | not run | | 10000 |
| 12 (tied) | snowy_plains | 8,934 | 911 | 8,029 | 3.1% | not run | | 10000 |
| 12 (tied) | jagged_peaks | 8,820 | 801 | 8,069 | 1.9% | not run | | 10000 |
| 12 (tied) | frozen_river | 8,575 | 860 | 7,737 | 2.7% | not run | | 10000 |
| 12 (tied) | savanna_plateau | 8,179 | 788 | 7,377 | 3.2% | not run | | 10000 |
| 12 (tied) | windswept_savanna | 8,150 | 725 | 7,474 | 1.5% | not run | | 10000 |
| 12 (tied) | dappled_forest | 7,650 | 717 | 6,991 | 1.8% | not run | | 10000 |
| 12 (tied) | windswept_hills | 7,366 | 674 | 6,740 | 1.8% | not run | | 10000 |
| 12 (tied) | snowy_slopes | 7,321 | 691 | 6,659 | 2.2% | not run | | 10000 |
| 12 (tied) | bamboo_jungle | 6,688 | 662 | 6,026 | 3.0% | not run | | 10000 |
| 12 (tied) | deep_lukewarm_ocean | 6,036 | 597 | 5,429 | 3.2% | not run | | 10000 |
| 12 (tied) | old_growth_spruce_taiga | 6,008 | 576 | 5,475 | 1.9% | not run | | 10000 |
| 12 (tied) | cherry_grove | 6,001 | 571 | 5,468 | 2.1% | not run | | 10000 |
| 12 (tied) | old_growth_pine_taiga | 5,862 | 559 | 5,342 | 1.9% | not run | | 10000 |
| 12 (tied) | deep_cold_ocean | 5,341 | 531 | 4,842 | 2.2% | not run | | 10000 |
| 12 (tied) | grove | 5,177 | 500 | 4,697 | 2.3% | not run | | 10000 |
| 12 (tied) | flower_forest | 4,753 | 470 | 4,286 | 3.1% | not run | | 10000 |
| 12 (tied) | sunflower_plains | 4,659 | 449 | 4,224 | 2.6% | not run | | 10000 |
| 12 (tied) | sparse_jungle | 3,889 | 446 | 3,418 | 4.6% | not run | | 10000 |
| 12 (tied) | jungle | 3,815 | 444 | 3,329 | 5.3% | not run | | 10000 |
| 12 (tied) | lukewarm_ocean | 3,582 | 411 | 3,155 | 4.4% | not run | | 10000 |
| 12 (tied) | savanna | 3,479 | 415 | 3,047 | 4.7% | not run | | 10000 |
| 12 (tied) | deep_ocean | 3,107 | 326 | 2,766 | 4.1% | not run | | 10000 |
| 12 (tied) | cold_ocean | 3,024 | 354 | 2,681 | 3.5% | not run | | 10000 |
| 12 (tied) | dark_forest | 2,850 | 299 | 2,570 | 2.5% | not run | | 10000 |
| 12 (tied) | taiga | 2,843 | 352 | 2,491 | 4.4% | not run | | 10000 |
| 12 (tied) | meadow | 2,330 | 278 | 2,024 | 5.9% | not run | | 10000 |
| 45 (tied) | old_growth_birch_forest | 1,606 | 187 | 1,418 | 4.1% | not run | | 10000 |
| 45 (tied) | stony_shore | 1,585 | 183 | 1,379 | 5.7% | not run | | 10000 |
| 45 (tied) | birch_forest | 1,576 | 183 | 1,392 | 3.9% | not run | | 10000 |
| 45 (tied) | ocean | 1,462 | 185 | 1,263 | 6.0% | not run | | 10000 |
| 49 (tied) | deep_dark | 868 | 124 | 737 | 6.7% | not run | | 10000 |
| 49 (tied) | sulfur_caves | 748 | 94 | 663 | 3.2% | not run | | 10000 |
| 51 (tied) | beach | 532 | 81 | 455 | 5.4% | not run | | 10000 |
| 51 (tied) | dripstone_caves | 419 | 80 | 336 | 11.7% | not run | | 10000 |
| 51 (tied) | lush_caves | 370 | 48 | 328 | 3.6% | not run | | 10000 |
| 51 (tied) | plains | 352 | 69 | 287 | 9.7% | not run | | 10000 |
| 51 (tied) | forest | 279 | 69 | 223 | 10.3% | not run | | 10000 |
| 51 (tied) | river | 164 | 85 | 114 | 22.7% | not run | | 10000 |
