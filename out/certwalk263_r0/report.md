# Walk from spawn to each biome

Every number is **estimate ± ε**. The true model value is inside every range at once, except with chance at most 1e-06 over the random seeds (1 in 1,000,000). Geometry error is 0 and rounding at most ±0.5 blocks (both certain, included in ε). The part past the cap rests on the constant hazard assumption and is shown as the tail share; the lower end of each range needs no assumption at all.

Plan `81079ca199874b69`, code `994583eaa1`.

**Layers (assumption, THEORY.md 8.9):** a biome counts in a 4x4 column if it is at any of the 96 layers from y = -64 to 319, so a cave biome counts as found when you pass within the radius of its column, at any depth, reachable or not.


## Sight radius 0, cap 560,000 blocks, per biome cap 4x its pilot walk (all 56 biomes, rarest first, most common last)

| rank | biome | E[D] from spawn | ± ε | guaranteed at least | tail share | from a random start | spawn bias | seeds |
|---|---|---|---|---|---|---|---|---|
| 1 | mushroom_fields | 149,522 | 3,280 | 142,267 | 3.3% | 148,475 ± 5,060 | 786 [-6,749, 8,326] | 215000 (53750 random start, bias on those) |
| 2 | windswept_gravelly_hills | 94,893 | 1,964 | 92,074 | 1.3% | 95,527 ± 3,011 | -648 [-5,128, 3,902] | 215000 (53750 random start, bias on those) |
| 3 | stony_peaks | 83,873 | 1,743 | 80,548 | 2.3% | 83,506 ± 2,683 | -360 [-4,415, 3,665] | 215000 (53750 random start, bias on those) |
| 4 | ice_spikes | 74,603 | 1,486 | 72,116 | 1.7% | 74,517 ± 2,351 | 307 [-3,178, 3,782] | 215000 (53750 random start, bias on those) |
| 5 | eroded_badlands | 70,084 | 1,452 | 67,652 | 1.8% | 70,715 ± 2,271 | -1,240 [-4,551, 2,061] | 215000 (53750 random start, bias on those) |
| 6 | pale_garden | 62,471 | 1,290 | 59,831 | 2.6% | 62,693 ± 2,026 | -213 [-3,310, 2,885] | 215000 (53750 random start, bias on those) |
| 7 | mangrove_swamp | 58,464 | 1,184 | 56,077 | 2.5% | 58,495 ± 1,861 | -88 [-2,898, 2,732] | 215000 (53750 random start, bias on those) |
| 8 (tied) | wooded_badlands | 54,092 | 1,226 | 51,635 | 2.8% | 54,188 ± 1,934 | 297 [-2,609, 3,190] | 215000 (53750 random start, bias on those) |
| 8 (tied) | jagged_peaks | 53,418 | 1,192 | 51,415 | 2.0% | 53,156 ± 1,849 | 182 [-2,579, 2,916] | 215000 (53750 random start, bias on those) |
| 8 (tied) | frozen_peaks | 53,370 | 1,073 | 51,630 | 1.6% | 53,306 ± 1,694 | -262 [-2,756, 2,176] | 215000 (53750 random start, bias on those) |
| 11 | windswept_forest | 48,008 | 1,066 | 46,528 | 1.2% | 47,987 ± 1,652 | 135 [-2,303, 2,566] | 215000 (53750 random start, bias on those) |
| 12 (tied) | badlands | 39,814 | 904 | 38,072 | 2.6% | 39,916 ± 1,425 | -125 [-2,251, 1,991] | 215000 (53750 random start, bias on those) |
| 12 (tied) | windswept_savanna | 39,775 | 897 | 38,378 | 1.7% | 40,185 ± 1,389 | -503 [-2,564, 1,569] | 215000 (53750 random start, bias on those) |
| 14 (tied) | deep_frozen_ocean | 36,392 | 801 | 35,270 | 1.3% | 36,016 ± 1,269 | 573 [-1,258, 2,399] | 215000 (53750 random start, bias on those) |
| 14 (tied) | cherry_grove | 35,329 | 804 | 34,083 | 1.7% | 35,536 ± 1,274 | -27 [-1,898, 1,831] | 215000 (53750 random start, bias on those) |
| 14 (tied) | windswept_hills | 34,001 | 770 | 32,762 | 1.8% | 33,827 ± 1,183 | 131 [-1,626, 1,883] | 215000 (53750 random start, bias on those) |
| 14 (tied) | dappled_forest | 33,807 | 758 | 32,538 | 2.0% | 33,838 ± 1,190 | 30 [-1,735, 1,812] | 215000 (53750 random start, bias on those) |
| 14 (tied) | savanna_plateau | 32,939 | 765 | 31,444 | 2.8% | 32,953 ± 1,157 | -122 [-1,860, 1,637] | 215000 (53750 random start, bias on those) |
| 14 (tied) | snowy_slopes | 32,453 | 723 | 31,278 | 1.8% | 32,561 ± 1,135 | 12 [-1,672, 1,713] | 215000 (53750 random start, bias on those) |
| 14 (tied) | warm_ocean | 31,319 | 702 | 30,017 | 2.4% | 31,226 ± 1,111 | 60 [-1,592, 1,720] | 215000 (53750 random start, bias on those) |
| 21 | swamp | 29,579 | 676 | 28,436 | 2.1% | 29,651 ± 1,044 | -64 [-1,598, 1,481] | 215000 (53750 random start, bias on those) |
| 22 (tied) | snowy_beach | 26,096 | 593 | 25,191 | 1.7% | 25,971 ± 915 | 286 [-1,061, 1,636] | 215000 (53750 random start, bias on those) |
| 22 (tied) | bamboo_jungle | 25,316 | 559 | 24,415 | 1.7% | 25,237 ± 864 | -32 [-1,327, 1,270] | 215000 (53750 random start, bias on those) |
| 22 (tied) | old_growth_spruce_taiga | 24,585 | 554 | 23,851 | 1.2% | 24,686 ± 857 | -264 [-1,497, 972] | 215000 (53750 random start, bias on those) |
| 22 (tied) | old_growth_pine_taiga | 24,052 | 540 | 23,305 | 1.3% | 24,257 ± 834 | -180 [-1,396, 1,044] | 215000 (53750 random start, bias on those) |
| 22 (tied) | desert | 23,952 | 550 | 22,937 | 2.4% | 24,287 ± 875 | -268 [-1,575, 1,033] | 215000 (53750 random start, bias on those) |
| 27 (tied) | flower_forest | 22,362 | 507 | 21,641 | 1.4% | 22,646 ± 801 | -148 [-1,314, 1,021] | 215000 (53750 random start, bias on those) |
| 27 (tied) | sunflower_plains | 22,075 | 501 | 21,290 | 1.8% | 22,284 ± 785 | -217 [-1,371, 923] | 215000 (53750 random start, bias on those) |
| 29 (tied) | grove | 19,738 | 445 | 18,997 | 2.0% | 19,761 ± 690 | -5 [-1,042, 1,032] | 215000 (53750 random start, bias on those) |
| 29 (tied) | frozen_ocean | 19,586 | 448 | 18,860 | 2.0% | 19,272 ± 706 | 333 [-697, 1,361] | 215000 (53750 random start, bias on those) |
| 31 (tied) | snowy_taiga | 16,450 | 382 | 15,799 | 2.1% | 16,581 ± 598 | -79 [-968, 814] | 215000 (53750 random start, bias on those) |
| 31 (tied) | snowy_plains | 16,151 | 371 | 15,550 | 1.9% | 16,328 ± 586 | -50 [-922, 830] | 215000 (53750 random start, bias on those) |
| 31 (tied) | deep_lukewarm_ocean | 16,135 | 356 | 15,449 | 2.5% | 15,808 ± 569 | 375 [-478, 1,226] | 215000 (53750 random start, bias on those) |
| 31 (tied) | frozen_river | 15,541 | 366 | 14,932 | 2.1% | 15,563 ± 569 | 61 [-777, 902] | 215000 (53750 random start, bias on those) |
| 31 (tied) | deep_cold_ocean | 15,071 | 325 | 14,520 | 1.9% | 14,791 ± 521 | 283 [-485, 1,054] | 215000 (53750 random start, bias on those) |
| 36 (tied) | sparse_jungle | 11,463 | 262 | 11,024 | 2.0% | 11,542 ± 407 | -75 [-685, 536] | 215000 (53750 random start, bias on those) |
| 36 (tied) | dark_forest | 11,203 | 260 | 10,689 | 2.8% | 11,326 ± 402 | -215 [-821, 392] | 215000 (53750 random start, bias on those) |
| 38 (tied) | meadow | 10,442 | 239 | 10,029 | 2.2% | 10,537 ± 377 | -64 [-620, 494] | 215000 (53750 random start, bias on those) |
| 38 (tied) | jungle | 10,329 | 240 | 9,872 | 2.6% | 10,415 ± 376 | -90 [-656, 477] | 215000 (53750 random start, bias on those) |
| 40 | deep_ocean | 9,798 | 217 | 9,405 | 2.3% | 9,425 ± 343 | 328 [-179, 830] | 215000 (53750 random start, bias on those) |
| 41 (tied) | savanna | 7,984 | 195 | 7,575 | 3.3% | 8,155 ± 305 | -202 [-658, 259] | 215000 (53750 random start, bias on those) |
| 41 (tied) | lukewarm_ocean | 7,883 | 187 | 7,524 | 2.8% | 7,670 ± 293 | 229 [-207, 668] | 215000 (53750 random start, bias on those) |
| 43 (tied) | cold_ocean | 7,145 | 161 | 6,903 | 1.6% | 6,962 ± 257 | 171 [-203, 544] | 215000 (53750 random start, bias on those) |
| 43 (tied) | taiga | 6,888 | 166 | 6,643 | 1.6% | 7,024 ± 259 | -194 [-572, 182] | 215000 (53750 random start, bias on those) |
| 43 (tied) | old_growth_birch_forest | 6,609 | 158 | 6,326 | 2.5% | 6,733 ± 246 | -146 [-509, 219] | 215000 (53750 random start, bias on those) |
| 46 (tied) | birch_forest | 6,286 | 148 | 6,045 | 2.0% | 6,359 ± 232 | -82 [-423, 262] | 215000 (53750 random start, bias on those) |
| 46 (tied) | stony_shore | 6,282 | 144 | 6,004 | 2.6% | 6,344 ± 226 | -48 [-390, 295] | 215000 (53750 random start, bias on those) |
| 48 | ocean | 4,251 | 99 | 4,099 | 1.8% | 4,040 ± 153 | 187 [-37, 413] | 215000 (53750 random start, bias on those) |
| 49 | sulfur_caves | 3,991 | 92 | 3,844 | 1.9% | 4,055 ± 146 | -83 [-296, 131] | 215000 (53750 random start, bias on those) |
| 50 | deep_dark | 2,981 | 79 | 2,816 | 3.6% | 3,129 ± 128 | -121 [-312, 70] | 215000 (53750 random start, bias on those) |
| 51 | beach | 2,563 | 64 | 2,462 | 2.0% | 2,595 ± 100 | -32 [-177, 114] | 215000 (53750 random start, bias on those) |
| 52 | dripstone_caves | 1,966 | 55 | 1,847 | 4.1% | 2,026 ± 89 | -46 [-179, 87] | 215000 (53750 random start, bias on those) |
| 53 | lush_caves | 1,728 | 47 | 1,636 | 3.4% | 1,731 ± 74 | -3 [-112, 106] | 215000 (53750 random start, bias on those) |
| 54 | plains | 1,587 | 47 | 1,466 | 5.5% | 1,733 ± 74 | -140 [-253, -26] | 215000 (53750 random start, bias on those) |
| 55 | forest | 1,164 | 37 | 1,079 | 5.1% | 1,304 ± 59 | -135 [-224, -46] | 215000 (53750 random start, bias on those) |
| 56 | river | 763 | 27 | 681 | 8.8% | 820 ± 42 | -54 [-120, 12] | 215000 (53750 random start, bias on those) |
