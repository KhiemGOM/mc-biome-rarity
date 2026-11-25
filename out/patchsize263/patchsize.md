# Patch width and patch density, 26.3 (from the certified walks)

Per biome: effective patch width w (mean projected width, blocks) and patch density rho (expected patches per 10,000 x 10,000 block square), as ranges that hold whenever the certified E[D] ranges hold (chance of failure at most 1 in 500,000, two runs).
- **Proven** (given the certified inputs): the interval arithmetic, no extra sampling error.
- **Assumed**: patches act like a sparse stationary field of convex patches with constant hazard (Steiner hit rate lambda_r = rho (w + 2r)).
- **Empirical check**: the radius pairs (0,128) and (0,512) should give the same w and rho. Where the ranges do not overlap, or the estimates drift, patches are not isolated (they come in clusters), and w, rho are only effective numbers for that range of sight.
- Area bound: a disc has the largest area for a given mean width, so for convex patches the area share is at most rho pi w^2 / 4. It is a loose upper bound, not an estimate.

| biome | w, sight 0 to 128 | w, sight 0 to 512 | patches per 10k x 10k (0 to 128) | patches per 10k x 10k (0 to 512) | check | area share <= (0 to 512) |
|---|---|---|---|---|---|---|
| jagged_peaks | 147 to 208 | 180 to 231 | 9.2 to 12.5 | 8.3 to 10.2 | agree | 0.427% |
| cherry_grove | 156 to 222 | 185 to 240 | 13.0 to 17.7 | 12.0 to 15.0 | agree | 0.678% |
| pale_garden | 161 to 228 | 186 to 240 | 7.2 to 9.7 | 6.8 to 8.4 | agree | 0.382% |
| frozen_peaks | 151 to 211 | 187 to 240 | 9.1 to 12.2 | 8.0 to 9.8 | agree | 0.444% |
| sulfur_caves | 187 to 293 | 203 to 281 | 87.4 to 130.9 | 91.0 to 120.9 | agree | 7.516% |
| stony_peaks | 162 to 224 | 228 to 291 | 5.4 to 7.2 | 4.2 to 5.1 | **drift** | 0.340% |
| windswept_forest | 179 to 263 | 230 to 301 | 8.1 to 11.4 | 7.1 to 8.9 | agree | 0.629% |
| windswept_savanna | 174 to 254 | 232 to 303 | 10.1 to 14.1 | 8.5 to 10.6 | agree | 0.760% |
| windswept_gravelly_hills | 177 to 248 | 237 to 300 | 4.3 to 5.8 | 3.6 to 4.4 | agree | 0.307% |
| beach | 184 to 316 | 223 to 331 | 126.2 to 207.3 | 120.4 to 170.5 | agree | 14.709% |
| sunflower_plains | 218 to 339 | 240 to 317 | 13.6 to 20.3 | 14.6 to 18.5 | agree | 1.456% |
| mushroom_fields | 208 to 306 | 245 to 311 | 2.2 to 3.1 | 2.2 to 2.7 | agree | 0.204% |
| flower_forest | 216 to 331 | 241 to 321 | 13.8 to 20.3 | 14.2 to 18.1 | agree | 1.464% |
| dripstone_caves | 284 to 605 | 224 to 360 | 86.3 to 174.1 | 145.1 to 220.4 | agree | 22.423% |
| lush_caves | 274 to 528 | 238 to 338 | 112.3 to 206.1 | 175.7 to 237.1 | agree | 21.227% |
| river | 103 to 259 | 200 to 519 | 522.1 to 1225.5 | 260.8 to 632.3 | agree | 133.518% |
| windswept_hills | 187 to 276 | 249 to 326 | 10.9 to 15.4 | 9.2 to 11.6 | agree | 0.966% |
| plains | 210 to 408 | 235 to 384 | 158.8 to 291.7 | 168.7 to 261.1 | agree | 30.262% |
| meadow | 198 to 301 | 251 to 351 | 32.5 to 47.3 | 27.9 to 37.3 | agree | 3.603% |
| snowy_slopes | 210 to 319 | 261 to 345 | 9.9 to 14.4 | 9.1 to 11.6 | agree | 1.083% |
| dappled_forest | 217 to 332 | 262 to 347 | 9.1 to 13.3 | 8.7 to 11.0 | agree | 1.040% |
| forest | 197 to 424 | 234 to 454 | 208.8 to 423.5 | 195.0 to 356.1 | agree | 57.595% |
| old_growth_birch_forest | 227 to 367 | 280 to 393 | 42.2 to 65.0 | 39.4 to 52.8 | agree | 6.406% |
| old_growth_pine_taiga | 243 to 382 | 288 to 384 | 11.1 to 16.7 | 11.1 to 14.1 | agree | 1.634% |
| old_growth_spruce_taiga | 239 to 376 | 289 to 385 | 11.1 to 16.7 | 10.8 to 13.8 | agree | 1.607% |
| savanna_plateau | 214 to 327 | 294 to 395 | 9.5 to 13.9 | 7.9 to 10.1 | agree | 1.234% |
| birch_forest | 241 to 398 | 291 to 410 | 40.8 to 64.4 | 39.7 to 53.3 | agree | 7.044% |
| stony_shore | 248 to 416 | 294 to 413 | 39.2 to 62.7 | 39.4 to 53.0 | agree | 7.114% |
| dark_forest | 291 to 505 | 301 to 413 | 18.1 to 30.0 | 22.1 to 29.0 | agree | 3.885% |
| grove | 247 to 396 | 316 to 426 | 13.1 to 20.1 | 12.2 to 15.7 | agree | 2.238% |
| bamboo_jungle | 247 to 390 | 318 to 432 | 10.4 to 15.7 | 9.3 to 12.2 | agree | 1.781% |
| ice_spikes | 251 to 374 | 341 to 439 | 3.7 to 5.2 | 3.1 to 3.9 | agree | 0.583% |
| deep_dark | 323 to 683 | 344 to 530 | 50.4 to 101.1 | 64.8 to 94.9 | agree | 20.974% |
| deep_ocean | 378 to 710 | 405 to 570 | 14.7 to 26.4 | 18.3 to 24.7 | agree | 6.303% |
| swamp | 368 to 678 | 440 to 606 | 5.1 to 9.0 | 5.7 to 7.5 | agree | 2.165% |
| sparse_jungle | 295 to 516 | 439 to 645 | 17.3 to 28.9 | 13.8 to 19.4 | agree | 6.359% |
| eroded_badlands | 314 to 506 | 462 to 622 | 2.9 to 4.5 | 2.3 to 3.0 | agree | 0.918% |
| mangrove_swamp | 377 to 647 | 468 to 622 | 2.7 to 4.5 | 2.8 to 3.6 | agree | 1.090% |
| ocean | 353 to 698 | 443 to 670 | 34.4 to 65.2 | 35.8 to 51.9 | agree | 18.315% |
| deep_cold_ocean | 389 to 735 | 477 to 677 | 9.2 to 16.7 | 10.0 to 13.6 | agree | 4.891% |
| jungle | 346 to 660 | 496 to 747 | 15.0 to 27.3 | 13.3 to 19.1 | agree | 8.365% |
| deep_lukewarm_ocean | 425 to 850 | 517 to 742 | 7.5 to 14.3 | 8.5 to 11.7 | agree | 5.070% |
| wooded_badlands | 415 to 773 | 591 to 816 | 2.4 to 4.4 | 2.3 to 3.1 | agree | 1.601% |
| taiga | 421 to 955 | 583 to 924 | 15.5 to 33.6 | 16.1 to 24.3 | agree | 16.310% |
| deep_frozen_ocean | 452 to 911 | 618 to 889 | 3.1 to 6.0 | 3.2 to 4.4 | agree | 2.703% |
| cold_ocean | 444 to 1,005 | 613 to 957 | 14.2 to 30.8 | 14.9 to 22.3 | agree | 16.055% |
| snowy_beach | 377 to 701 | 631 to 928 | 5.6 to 9.9 | 4.2 to 5.9 | agree | 4.013% |
| savanna | 466 to 1,132 | 637 to 1,020 | 11.3 to 26.2 | 12.6 to 19.2 | agree | 15.692% |
| lukewarm_ocean | 477 to 1,141 | 688 to 1,100 | 11.4 to 26.0 | 11.8 to 18.0 | agree | 17.113% |
| badlands | 483 to 977 | 726 to 1,042 | 2.6 to 5.1 | 2.5 to 3.4 | agree | 2.883% |
| warm_ocean | 613 to 1,723 | 888 to 1,399 | 1.9 to 5.1 | 2.3 to 3.5 | agree | 5.402% |
| frozen_ocean | 621 to 1,772 | 891 to 1,436 | 2.9 to 8.0 | 3.6 to 5.6 | agree | 9.073% |
| snowy_taiga | 668 to 2,248 | 990 to 1,653 | 2.8 to 8.9 | 3.8 to 6.0 | agree | 12.878% |
| frozen_river | 670 to 2,322 | 999 to 1,674 | 2.8 to 9.4 | 3.9 to 6.3 | agree | 13.846% |
| snowy_plains | 682 to 2,370 | 1,002 to 1,693 | 2.7 to 8.9 | 3.7 to 6.0 | agree | 13.602% |
| desert | 767 to 3,352 | 1,103 to 1,864 | 1.3 to 5.3 | 2.3 to 3.7 | agree | 10.095% |

Check: 55 of 56 biomes agree between the (0,128) and (0,512) pairs. Drift direction: w (0,512) minus w (0,128) estimate is positive for 51 of 56 biomes.
