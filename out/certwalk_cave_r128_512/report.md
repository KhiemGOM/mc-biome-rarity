# Walk from spawn to each biome

Every number is **estimate ± ε**. The true model value is inside every range at once, except with chance at most 1e-06 over the random seeds (1 in 1,000,000). Geometry error is 0 and rounding at most ±0.5 blocks (both certain, included in ε). The part past the cap rests on the constant hazard assumption and is shown as the tail share; the lower end of each range needs no assumption at all.

Plan `2e048abc0a486968`, code `9127566f19`.

**Layers (assumption, THEORY.md 8.9):** a biome counts in a 4x4 column if it is at any of the 96 layers from y = -64 to 319, so a cave biome counts as found when you pass within the radius of its column, at any depth, reachable or not.


## Sight radius 128, cap 270,000 blocks, per biome cap 4x its pilot walk (all 54 biomes, rarest first, most common last)

| rank | biome | E[D] from spawn | ± ε | guaranteed at least | tail share | from a random start | spawn bias | seeds |
|---|---|---|---|---|---|---|---|---|
| 1 | mushroom_fields | 72,527 | 6,614 | 66,105 | 2.9% | not run | | 9750 |
| 2 (tied) | pale_garden | 42,981 | 3,745 | 39,552 | 1.9% | not run | | 9750 |
| 2 (tied) | eroded_badlands | 42,754 | 3,713 | 39,278 | 2.1% | not run | | 9750 |
| 2 (tied) | windswept_gravelly_hills | 42,711 | 3,782 | 38,992 | 2.8% | not run | | 9750 |
| 2 (tied) | ice_spikes | 40,336 | 3,541 | 37,081 | 2.0% | not run | | 9750 |
| 2 (tied) | mangrove_swamp | 37,997 | 3,387 | 34,829 | 2.2% | not run | | 9750 |
| 2 (tied) | wooded_badlands | 36,750 | 3,219 | 33,742 | 2.1% | not run | | 9750 |
| 2 (tied) | stony_peaks | 36,151 | 3,015 | 33,396 | 1.6% | not run | | 9750 |
| 9 (tied) | badlands | 29,020 | 2,620 | 26,499 | 2.7% | not run | | 9750 |
| 9 (tied) | deep_frozen_ocean | 25,431 | 2,503 | 23,106 | 2.6% | not run | | 9750 |
| 9 (tied) | warm_ocean | 24,510 | 2,432 | 22,222 | 2.8% | not run | | 9750 |
| 9 (tied) | windswept_forest | 22,084 | 2,088 | 20,230 | 1.6% | not run | | 9750 |
| 9 (tied) | frozen_peaks | 21,605 | 2,044 | 19,779 | 1.7% | not run | | 9750 |
| 9 (tied) | jagged_peaks | 21,462 | 2,040 | 19,615 | 1.9% | not run | | 9750 |
| 9 (tied) | desert | 19,995 | 2,028 | 18,021 | 3.3% | not run | | 9750 |
| 9 (tied) | swamp | 19,242 | 1,861 | 17,540 | 2.1% | not run | | 9750 |
| 9 (tied) | windswept_savanna | 17,716 | 1,692 | 16,123 | 2.4% | not run | | 9750 |
| 9 (tied) | savanna_plateau | 16,897 | 1,555 | 15,480 | 1.7% | not run | | 9750 |
| 9 (tied) | snowy_beach | 16,859 | 1,728 | 15,273 | 2.5% | not run | | 9750 |
| 9 (tied) | snowy_slopes | 16,215 | 1,520 | 14,836 | 1.7% | not run | | 9750 |
| 9 (tied) | windswept_hills | 15,858 | 1,546 | 14,443 | 2.2% | not run | | 9750 |
| 9 (tied) | frozen_ocean | 15,063 | 1,604 | 13,562 | 3.1% | not run | | 9750 |
| 9 (tied) | cherry_grove | 14,849 | 1,389 | 13,620 | 1.5% | not run | | 9750 |
| 9 (tied) | bamboo_jungle | 13,963 | 1,329 | 12,741 | 2.0% | not run | | 9750 |
| 9 (tied) | old_growth_spruce_taiga | 12,979 | 1,265 | 11,844 | 2.0% | not run | | 9750 |
| 9 (tied) | old_growth_pine_taiga | 12,806 | 1,240 | 11,710 | 1.6% | not run | | 9750 |
| 9 (tied) | snowy_taiga | 12,762 | 1,410 | 11,443 | 3.3% | not run | | 9750 |
| 9 (tied) | snowy_plains | 12,596 | 1,386 | 11,306 | 3.2% | not run | | 9750 |
| 9 (tied) | frozen_river | 12,076 | 1,343 | 10,837 | 3.1% | not run | | 9750 |
| 9 (tied) | flower_forest | 11,540 | 1,085 | 10,556 | 1.7% | not run | | 9750 |
| 9 (tied) | sunflower_plains | 11,415 | 1,082 | 10,445 | 1.6% | not run | | 9750 |
| 9 (tied) | deep_lukewarm_ocean | 11,117 | 1,004 | 10,218 | 1.4% | not run | | 9750 |
| 9 (tied) | grove | 10,654 | 1,047 | 9,715 | 1.9% | not run | | 9750 |
| 9 (tied) | deep_cold_ocean | 10,152 | 965 | 9,248 | 2.3% | not run | | 9750 |
| 35 (tied) | sparse_jungle | 7,091 | 770 | 6,377 | 3.0% | not run | | 9750 |
| 35 (tied) | jungle | 6,735 | 715 | 6,071 | 2.7% | not run | | 9750 |
| 35 (tied) | deep_ocean | 6,518 | 637 | 5,944 | 2.0% | not run | | 9750 |
| 35 (tied) | dark_forest | 6,444 | 631 | 5,871 | 1.9% | not run | | 9750 |
| 35 (tied) | lukewarm_ocean | 5,883 | 634 | 5,296 | 2.7% | not run | | 9750 |
| 35 (tied) | savanna | 5,853 | 661 | 5,229 | 3.4% | not run | | 9750 |
| 35 (tied) | meadow | 5,091 | 504 | 4,627 | 2.0% | not run | | 9750 |
| 35 (tied) | cold_ocean | 5,060 | 561 | 4,541 | 2.9% | not run | | 9750 |
| 35 (tied) | taiga | 4,743 | 535 | 4,250 | 2.9% | not run | | 9750 |
| 44 (tied) | old_growth_birch_forest | 3,542 | 371 | 3,199 | 2.4% | not run | | 9750 |
| 44 (tied) | stony_shore | 3,511 | 379 | 3,162 | 2.5% | not run | | 9750 |
| 44 (tied) | birch_forest | 3,450 | 379 | 3,095 | 3.0% | not run | | 9750 |
| 44 (tied) | ocean | 2,827 | 321 | 2,531 | 2.9% | not run | | 9750 |
| 48 | deep_dark | 1,910 | 251 | 1,680 | 3.5% | not run | | 9750 |
| 49 (tied) | beach | 1,234 | 171 | 1,079 | 3.8% | not run | | 9750 |
| 49 (tied) | dripstone_caves | 1,162 | 176 | 985 | 6.5% | not run | | 9750 |
| 49 (tied) | lush_caves | 1,006 | 127 | 893 | 2.7% | not run | | 9750 |
| 49 (tied) | plains | 837 | 135 | 709 | 6.0% | not run | | 9750 |
| 53 | forest | 606 | 119 | 491 | 9.3% | not run | | 9750 |
| 54 | river | 289 | 105 | 207 | 17.3% | not run | | 9750 |

## Sight radius 512, cap 270,000 blocks, per biome cap 4x its pilot walk (all 54 biomes, rarest first, most common last)

| rank | biome | E[D] from spawn | ± ε | guaranteed at least | tail share | from a random start | spawn bias | seeds |
|---|---|---|---|---|---|---|---|---|
| 1 | mushroom_fields | 31,062 | 2,599 | 28,586 | 2.1% | not run | | 10250 |
| 2 (tied) | eroded_badlands | 24,471 | 2,133 | 22,421 | 2.4% | not run | | 10250 |
| 2 (tied) | wooded_badlands | 21,796 | 1,914 | 19,962 | 2.4% | not run | | 10250 |
| 2 (tied) | mangrove_swamp | 20,241 | 1,806 | 18,482 | 2.7% | not run | | 10250 |
| 2 (tied) | ice_spikes | 20,040 | 1,781 | 18,344 | 2.4% | not run | | 10250 |
| 2 (tied) | windswept_gravelly_hills | 19,451 | 1,704 | 17,792 | 2.5% | not run | | 10250 |
| 2 (tied) | badlands | 18,463 | 1,632 | 16,879 | 2.6% | not run | | 10250 |
| 2 (tied) | stony_peaks | 17,192 | 1,446 | 15,843 | 1.8% | not run | | 10250 |
| 2 (tied) | warm_ocean | 16,366 | 1,628 | 14,812 | 2.9% | not run | | 10250 |
| 2 (tied) | pale_garden | 16,309 | 1,343 | 15,104 | 1.2% | not run | | 10250 |
| 2 (tied) | deep_frozen_ocean | 14,891 | 1,526 | 13,431 | 3.2% | not run | | 10250 |
| 2 (tied) | desert | 14,070 | 1,437 | 12,681 | 3.2% | not run | | 10250 |
| 13 (tied) | snowy_beach | 10,712 | 1,131 | 9,628 | 3.3% | not run | | 10250 |
| 13 (tied) | frozen_ocean | 9,878 | 1,081 | 8,821 | 3.8% | not run | | 10250 |
| 13 (tied) | windswept_forest | 9,761 | 940 | 8,897 | 2.0% | not run | | 10250 |
| 13 (tied) | swamp | 9,717 | 959 | 8,830 | 2.4% | not run | | 10250 |
| 13 (tied) | jagged_peaks | 9,190 | 907 | 8,343 | 2.5% | not run | | 10250 |
| 13 (tied) | frozen_peaks | 9,108 | 874 | 8,309 | 1.9% | not run | | 10250 |
| 13 (tied) | snowy_taiga | 8,715 | 966 | 7,798 | 3.3% | not run | | 10250 |
| 13 (tied) | snowy_plains | 8,682 | 968 | 7,748 | 3.6% | not run | | 10250 |
| 13 (tied) | frozen_river | 8,385 | 941 | 7,477 | 3.6% | not run | | 10250 |
| 13 (tied) | savanna_plateau | 8,316 | 832 | 7,541 | 2.5% | not run | | 10250 |
| 13 (tied) | windswept_savanna | 8,120 | 806 | 7,362 | 2.6% | not run | | 10250 |
| 13 (tied) | snowy_slopes | 7,422 | 727 | 6,753 | 2.1% | not run | | 10250 |
| 13 (tied) | windswept_hills | 7,390 | 759 | 6,682 | 2.7% | not run | | 10250 |
| 13 (tied) | bamboo_jungle | 6,775 | 734 | 6,082 | 3.3% | not run | | 10250 |
| 13 (tied) | deep_lukewarm_ocean | 6,152 | 627 | 5,585 | 2.0% | not run | | 10250 |
| 13 (tied) | old_growth_spruce_taiga | 5,963 | 627 | 5,394 | 2.4% | not run | | 10250 |
| 13 (tied) | old_growth_pine_taiga | 5,920 | 616 | 5,355 | 2.5% | not run | | 10250 |
| 13 (tied) | cherry_grove | 5,900 | 569 | 5,379 | 1.9% | not run | | 10250 |
| 13 (tied) | deep_cold_ocean | 5,334 | 550 | 4,821 | 2.5% | not run | | 10250 |
| 13 (tied) | grove | 5,260 | 543 | 4,757 | 2.4% | not run | | 10250 |
| 13 (tied) | flower_forest | 4,786 | 494 | 4,316 | 2.9% | not run | | 10250 |
| 13 (tied) | sunflower_plains | 4,747 | 509 | 4,269 | 3.1% | not run | | 10250 |
| 13 (tied) | sparse_jungle | 3,948 | 487 | 3,472 | 4.5% | not run | | 10250 |
| 13 (tied) | jungle | 3,836 | 461 | 3,391 | 3.9% | not run | | 10250 |
| 13 (tied) | lukewarm_ocean | 3,650 | 451 | 3,222 | 3.9% | not run | | 10250 |
| 13 (tied) | savanna | 3,511 | 450 | 3,079 | 4.4% | not run | | 10250 |
| 13 (tied) | deep_ocean | 3,113 | 346 | 2,788 | 3.1% | not run | | 10250 |
| 13 (tied) | cold_ocean | 3,025 | 377 | 2,665 | 4.1% | not run | | 10250 |
| 13 (tied) | dark_forest | 2,889 | 319 | 2,590 | 3.0% | not run | | 10250 |
| 13 (tied) | taiga | 2,854 | 385 | 2,471 | 5.4% | not run | | 10250 |
| 13 (tied) | meadow | 2,332 | 294 | 2,033 | 5.3% | not run | | 10250 |
| 44 (tied) | old_growth_birch_forest | 1,613 | 203 | 1,421 | 4.0% | not run | | 10250 |
| 44 (tied) | birch_forest | 1,608 | 199 | 1,419 | 3.8% | not run | | 10250 |
| 44 (tied) | stony_shore | 1,595 | 204 | 1,404 | 4.1% | not run | | 10250 |
| 44 (tied) | ocean | 1,478 | 202 | 1,276 | 5.8% | not run | | 10250 |
| 48 | deep_dark | 891 | 145 | 745 | 7.7% | not run | | 10250 |
| 49 | beach | 556 | 99 | 468 | 6.7% | not run | | 10250 |
| 50 (tied) | dripstone_caves | 395 | 87 | 318 | 11.1% | not run | | 10250 |
| 50 (tied) | lush_caves | 359 | 48 | 319 | 3.1% | not run | | 10250 |
| 50 (tied) | plains | 359 | 83 | 289 | 10.4% | not run | | 10250 |
| 50 (tied) | forest | 274 | 76 | 220 | 10.0% | not run | | 10250 |
| 50 (tied) | river | 169 | 99 | 116 | 23.1% | not run | | 10250 |
