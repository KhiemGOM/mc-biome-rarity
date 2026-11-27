# Rarest biome video: outline (v5, 2026-11-23)

Not a script. Section order, beats, key visuals, rough timing. Target length about 11 minutes. The full script is VIDEO_SCRIPT.md.

All numbers are **final**, on **Minecraft Java 26.3 worldgen** (xpple/cubiomes fork), certified walk from spawn, caves included. Sight radius 0 on 215,000 seeds, 8 and 32 chunks on 10,000 seeds each. Every range holds together except with a 1 in 500,000 chance. Sources in `/mnt/project-files/results/`: `mc263_r0_order.md` / `mc263_r0_report.md`, `mc263_r128_512_order.md` / `mc263_r128_512_report.md`, spawn effect `mc263_r0_spawnratio.md`. Rankings come from the order files (paired comparisons). All 1.21.4 numbers are superseded.

### What changed since v1
- Headline is now the **full expected walk from spawn**, nothing cut off (no 4,000 block window).
- **Cave biomes included** (whole column, y -64 to 319).
- **One random ray per seed** (proven better than 4).
- Numbers are **estimate ± bound, wrong with chance at most 1 in 500,000** (no more "95%"). Where bounds overlap the biomes are called **tied**.
- Sight radii locked: **0** (headline), **8 chunks** (what a person would spot), **32 chunks** (pro hunter or cheat client).
- **Spawn bias was measured, and it is tiny** for every rare biome. This changes section 1, see the note there.
- v3: final r = 0 numbers (53,750 seeds, the #5 tie split), the owner's reading of the ranking recorded in section 4c.
- v4: the 8 and 32 chunk rankings get their own section (4b), and section 1 uses the normalized spawn effect.
- v5: everything rerun on 26.3 (the old runs were 1.21.4 worldgen, before the pale garden got bigger). New top 7, pale garden falls from #2 to #6. Section 3 now has two mistakes. Guarantee is 1 in 500,000. The owner 4c reading mapped to 26.3, the old 21 to 46 tie point dropped. Cold open now teases camman for four videos with four different answers.

## What the old video got wrong (so we avoid it)

Looked at `scenes.py` / `make_video.py` (16 silent slides).

- **Results buried.** The ranking was slide 8 of 16. Viewers want the answer, so tease it at 0:00 and pay it off by the midpoint.
- **Too much meta.** Five slides on method (proof, convergence, seeds vs rays, tests, caveats). That is the part nobody watches.
- **Maths notation on screen.** `S(r)`, `h(r)`, hazard curves. Fine for THEORY.md, kills a video. Say it in words.
- **Text walls, no voice.** Slides were 2 to 4 sentences of text each. Voice carries the words, the screen carries one picture.
- **Wrong pale garden number** (about 225k to 265k on screen; on 26.3 it is 62k). Every number in the new one comes from one source file.
- **Keep:** the "one real seed, four rays" map animation (scene 3) is genuinely good. Reuse it as the core Monte Carlo visual.

## Structure at a glance

| # | Section | Time | Job |
|---|---|---|---|
| 0 | Cold open | 0:00 to 0:30 | Hook + promise |
| 1 | What does "rare" even mean | 0:30 to 2:30 | Justify the metric (clumping, then the spawn test) |
| 2 | Monte Carlo: just make a lot of worlds | 2:30 to 4:00 | Method, intuitively |
| 3 | How do I know it is right? (wrong twice) | 4:00 to 5:15 | Earns the word "mathematically" |
| 4 | The countdown | 5:15 to 7:15 | Results |
| 4b | "Now open your eyes": 8 and 32 chunks | 7:15 to 8:40 | How the ranking changes when you can see |
| 4c | Reading the ranking | 8:40 to 10:30 | Surprising vs expected (the owner writes) |
| 5 | Outro | 10:30 to 11:10 | Takeaway + limits |

Final script note: draft it with the human voice skill so it sounds like the owner, not like AI.

## 0. Cold open (0:00 to 0:30)

- Beat: open on camman18, the go-to "rarest biome" creator. Short clip or thumbnail wall of his rarest biome videos (keep clips brief for fair use, and credit him on screen). Frame it as building on his work, not dunking on it: "camman18 has ranked the rarest biomes for years. I wanted to put an actual number on it."
  - Checked (shorts 12UgiwOo28k, ZnfLg6UiDYw, HVfXIyuudTY plus the 1.17 one). His #1 is never mushroom fields, which is the tension for the countdown. His distance method is unknown, so do not describe it on camera.
- Beat: "Ask the rest of the internet and you get five different answers." Then camman four answers in a row: modified jungle edge (1.17, mushroom not top five), pale garden by area, windswept gravelly hills after the pale garden buff, eroded badlands by distance. Sarcastic beat (the owner request): four videos, four different answers, none agree with each other, said with love. Then "Everyone has a number. Nobody has a proof."
- Beat: "So I generated a huge number of real Minecraft worlds and walked through every one of them." Seed counter spinning up.
- Beat (hook): "I worked out the rarest biome in Minecraft. Mathematically." Title and thumbnail: "I found the RAREST biome in Minecraft... MATHEMATICALLY". The 43% story stays in section 3, not the headline.
- Visual: fast cuts, real 26.3 footage of each candidate biome. Title card last, not first.

## 1. What does "rare" even mean (0:30 to 2:30)

The argument: rarity should mean **what it costs a player to find it, starting from where they actually start**.

> **How spawn shows up in the data (26.3).** Two different numbers tell two different stories, and the video uses both:
> - **In the walk length, spawn barely shows.** Mushroom fields from spawn vs from a random point: +786 blocks, range -6,749 to +8,326. The estimate points the way the owner expects (a tiny bonus, about 0.5% of the walk), but it is not proven. A spawn effect only lasts the first couple of thousand blocks, which is little on a 150,000 block trip.
> - **In the normalized spawn effect, it is huge.** "How much more likely is spawn to be in this biome than a random spot", area divided out (`mc263_r0_spawnratio.md`). Plains 1.77x, forest 1.72x, desert and other land biomes about 1.7 to 1.9x at the spawn point. Oceans and rivers: never, 0 in 215,000 spawns (river covers 6.1% of the world). Beaches flip: about 0.01x at the exact spawn point, 1.38x within 128 blocks. **Mushroom fields are pushed away**: never at spawn, about 0.14x (range 0.03 to 0.37) within 512 blocks. Every effect is gone by about 2,000 blocks.

- **Candidate A: the wiki / community label.** It is an opinion, often from old versions, and nobody says what "rare" was measured by. 10 seconds, move on.
- **Candidate B: % of the world's area.** Sounds objective. Show the old two-panel demo: same area share, one biome as 36 small patches vs one big blob. The blob is far harder to stumble on. Area ignores how a biome is **clumped**. This is still the main argument for walking distance.
  - Optional punch if the data backs it: a side by side "rank by area" vs "rank by walking" where the order flips. (To check: compute an area share ranking from the same seeds before claiming a flip.)
- **Candidate C: mean free path** (the average walk from a random point in the world). Fixes clumping, so it is better than area. Mention that this was my own first metric.
- **The spawn question.** C assumes you could start anywhere, but the game picks your spawn, and it is not random. So the biomes around spawn are not a fair sample of the world.
  - Visual: heat map of where spawns land vs a uniform scatter of random points. Then a bar chart of the normalized spawn effect: land biomes up at 1.7 to 1.9x, oceans and rivers at zero, beaches flipping between the spawn point and 128 blocks out.
  - Mushroom beat: set up only ("some biomes get pushed away from spawn, hold that thought"). **No spoiler**: the payoff comes at the #1 reveal in section 4. There: never at spawn, about 0.14x within 512 blocks; a likely tiny bonus to the walk, but not why it is #1.
  - Why the metric still wins: walking from your real spawn is what a player actually does, and it is the only one of these metrics that can **measure** the spawn effect at all. Area and mean free path assume it away; this one tested it and can tell you exactly how big it is.
- **Candidate D, the one I use: how far you walk from your real spawn until you find it.** Clumping is handled because you are actually walking, and spawn is handled because the walk starts where the game puts you. Nothing cut off. One number per biome, in blocks.
  - Visual: spawn dot, ray, distance counter starting at 0.
- **Quick note:** we walk in a straight line, because a wandering walk keeps re-checking ground it already saw. One quick overlay of a squiggly path vs a ray.
- **Make the unit human:** the #1 at about 150,000 blocks is about **7.4 hours of non-stop sprinting** (5.612 blocks/s), shown only at the reveal. It comes back in the outro.

## 2. Monte Carlo: just make a lot of worlds (2:30 to 4:00)

- Beat: "There is no formula for Minecraft terrain. But there is a seed." The trick: if you cannot calculate it, simulate it many times and average.
- 15 second analogy: throwing darts at a square to estimate pi. More darts, steadier answer. Keep it to one visual.
- Core visual (reuse old scene 3, but with **one** ray per seed in a random direction, since that is what the run does now): one real seed's map, spawn dot, the ray shooting out, each biome lighting up the first time the ray touches it with its distance.
- Then zoom out: hundreds of maps tiling the screen, one ray each, a running estimate for each biome wobbling then settling. "Every ray finds every biome at once, so one pass gives the whole ranking." Seed count to quote: 215,000.
- Optional 10 second aside: "why not 4 rays per world? Rays from the same spawn see the same terrain, so a fresh world teaches you more than another ray." Only if it fits.
- Tool credit on screen: Cubiomes, xpple fork (runs the real 26.3 generator, no game needed). Mention it is the same generator the game uses, so these are real worlds, not approximations.
- Do NOT show: survival curves, hazard plots, caps. If needed, one sentence: "rays that go a really long way without finding it count too."

## 3. How do I know it is right? (4:00 to 5:15)

The convergence proof as a story, not maths. Hook line: "mathematically is a big word, so let me earn it. I got it wrong twice."

- **Mistake 1, the 16 block grid.** "To go fast, my first version only checked the biome every 16 blocks." Dot grid over terrain. Results looked great, tiny error bars. Reveal: a pale garden patch sitting between the dots, the grid steps over it. Pale garden came out 43% too far.
- The lesson: **more seeds would never fix this.** Dartboard, tight cluster nowhere near the bullseye. "Precise is not the same as correct."
- **Mistake 2, the wrong game version.** camman's pale garden short made me check: the generator was 1.21.4, the update before pale gardens got bigger. Everything thrown away and rerun on 26.3. Visual: the old ranking with pale garden at #2, a red "1.21.4" stamp, it shatters. Line: "Maths can prove the code matches the model. It cannot tell you that you picked the wrong version of the game."
- The fix: checks every spot, current version, every number with a range proven to hold all at once except with a 1 in 500,000 chance. "The proof is on GitHub" with the THEORY.md link.
- Tie in: "when two ranges overlap, I will not pretend I know which is rarer. I will call it a tie."
- Length: about 75 seconds.

## 4. The countdown (5:15 to 7:15)

Count down from 5 to 1. Each entry about 20 seconds: footage, walk in blocks, sprint hours (5.612 blocks/s), one fact about why. Sight radius 0 (you have to step on it), 215,000 seeds.

| Rank | Biome | Walk from spawn | Sprint time |
|---|---|---|---|
| 5 | Eroded badlands | 70,084 ± 1,452 | about 3.5 h |
| 4 | Ice spikes | 74,603 ± 1,486 | about 3.7 h |
| 3 | Stony peaks | 83,873 ± 1,743 | about 4.2 h |
| 2 | Windswept gravelly hills | 94,893 ± 1,964 | about 4.7 h |
| 1 | Mushroom fields | 149,522 ± 3,280 | about 7.4 h |

- Ranks 1 to 7 are each proven apart from every other biome (pale garden #6 at 62,471, mangrove swamp #7 at 58,464). The first tie is 8 to 10 (wooded badlands, jagged peaks, frozen peaks, about 53k to 54k). Line: "the top 7 are not opinions, they are proven in that order."
- Beat at #5: eroded badlands was camman's answer by distance, and here it is only fifth.
- Beat at #2: windswept gravelly hills covers the least area of any biome (0.065% of the world), and most people could not say what it looks like.
- Beat before #1: pale garden fell from #2 on 1.21.4 to #6 on 26.3 (callback to mistake 2).
- Beat at #1: more than 1.5x further than anything else. Big once you find them, but very few, far out in the ocean. Spawn payoff from section 1: never at spawn, about 0.14x as likely within 512 blocks. A likely tiny bonus, not why it is #1.
- Transition into 4b: "but you do not walk around with your eyes closed."
- End card: ranked bar chart, top 10 or so, each bar with its ± range as a thin band, tied groups bracketed.

**Full r = 0 order (for the end card and 4c):** 1 mushroom fields 149,522; 2 windswept gravelly hills 94,893; 3 stony peaks 83,873; 4 ice spikes 74,603; 5 eroded badlands 70,084; 6 pale garden 62,471; 7 mangrove swamp 58,464; 8 to 10 wooded badlands, jagged peaks, frozen peaks; 11 windswept forest 48,008; 12 to 13 badlands, windswept savanna; 14 to 15 deep frozen ocean, cherry grove; 16 to 18 windswept hills 34,001, dappled forest 33,807 (savanna plateau 16 to 19); 18 to 19 snowy slopes; 20 warm ocean; 21 swamp; 22 to 26 snowy beach, bamboo jungle, old growth spruce taiga, old growth pine taiga, desert; 27 to 28 flower forest, sunflower plains; 29 to 30 grove, frozen ocean; 31 to 33 snowy taiga, snowy plains, deep lukewarm ocean; 34 to 35 frozen river, deep cold ocean; 36 to 37 sparse jungle, dark forest; 38 to 39 meadow, jungle; 40 deep ocean; 41 to 42 savanna, lukewarm ocean; 43 cold ocean; 44 taiga; 45 old growth birch forest; 46 to 47 birch forest, stony shore; 48 ocean 4,251; 49 sulfur caves 3,991; 50 deep dark 2,981; 51 beach 2,563; 52 dripstone caves 1,966; 53 lush caves 1,728; 54 plains 1,587; 55 forest 1,164; 56 river 763.

## 4b. "Now open your eyes": 8 and 32 chunks (7:15 to 8:40)

A biome counts as found once it is within sight: **8 chunks (128 blocks)**, what a normal player would spot, and **32 chunks (512 blocks)**, a pro hunter with max render distance, or a cheat client. Same certified method, 10,000 seeds each.

- Opening visual: the same ray, now with a glowing band, 8 chunks wide, then 32.
- Core idea once: seeing helps **small patches** most. Tiny patch: hard to step on, easy to spot from 500 blocks. A big patch was never hard to hit.

**Top of the table across the three radii (26.3)**

| Biome | Step on it (0) | 8 chunks | 32 chunks |
|---|---|---|---|
| Mushroom fields | #1, 149,522 | #1, 73,730 | #1, 31,630 |
| Windswept gravelly hills | #2, 94,893 | 2 to 5, 42,378 | 3 to 7, 19,530 |
| Stony peaks | #3, 83,873 | 5 to 7, 35,618 | 7 to 10, 16,800 |
| Ice spikes | #4, 74,603 | 2 to 6, 40,322 | 3 to 7, 20,363 |
| Eroded badlands | #5, 70,084 | 2 to 5, 42,295 | **#2**, 23,970 |
| Pale garden | #6, 62,471 | 8 to 11, 26,573 | 12 to 16, 10,637 |
| Mangrove swamp | #7, 58,464 | 2 to 7, 38,084 | 3 to 7, 20,083 |
| Wooded badlands | 8 to 10, 54,092 | 4 to 7, 36,752 | 3 to 6, 21,729 |
| Badlands | 12 to 13, 39,814 | 8 to 10, 28,584 | 4 to 8, 18,169 |

**Beats**
- **Mushroom fields never move.** #1 alone and proven at every radius: about 7.4 h of sprinting at 0, 3.6 h at 8 chunks, 1.6 h at 32 chunks. "You cannot see something that is not there."
- **8 chunks: the podium collapses.** Ranks 2 to 7 can't be separated: windswept gravelly hills, eroded badlands, ice spikes, mangrove, wooded badlands, stony peaks. "Once you can actually see, nobody wins second place."
- **Pale garden keeps falling:** #6, then 8 to 11, then 12 to 16. Tiny patches, easy to spot.
- **32 chunks: eroded badlands takes a proven #2** (about 1 h 10 min), up from #5. Big but **sparse** patches (the owner's reading). The badlands family climbs with it: wooded badlands 3 to 6, badlands 4 to 8.
- **camman link:** eroded badlands near the top looks like his distance ranking. The further you see, the closer you get to "how near is the nearest patch". Mushroom still stays ahead, proven.
- **The common end:** at 8 chunks river is still #56 alone (283 blocks). At 32 chunks the bottom blurs: dripstone, lush caves and plains tie, and forest and river tie (river 164 blocks).
- **Which one is "the" answer?** It depends on how far you can see. Only #1 survives every version.
- **Optional nerd beat, patch size and count (26.3, recomputed):** from the certified walks at 0, 128 and 512 (`patchsize.py`, `out/patchsize263/patchsize.md`, all 56 biomes). Hit rate model: walks meet patches at rate density x (width + 2 x sight), so width = 2r / (walk at 0 / walk at r - 1). Ranges inherit the certified 1 in 500,000 guarantee; the hit-rate model itself is an assumption.

| Biome | Patch width, blocks (sight 0 to 128 / 0 to 512) | Patches per 10,000 x 10,000 blocks (0 to 128 / 0 to 512) |
|---|---|---|
| Mushroom fields | 208 to 306 / 245 to 311 | 2.2 to 3.1 / 2.2 to 2.7 |
| Windswept gravelly hills | 177 to 248 / 237 to 300 | 4.3 to 5.8 / 3.6 to 4.4 |
| Stony peaks | 162 to 224 / 228 to 291 | 5.4 to 7.2 / 4.2 to 5.1 |
| Ice spikes | 251 to 374 / 341 to 439 | 3.7 to 5.2 / 3.1 to 3.9 |
| Eroded badlands | 314 to 506 / 462 to 622 | 2.9 to 4.5 / 2.3 to 3.0 |
| Pale garden | 161 to 228 / 186 to 240 | 7.2 to 9.7 / 6.8 to 8.4 |
| Mangrove swamp | 377 to 647 / 468 to 622 | 2.7 to 4.5 / 2.8 to 3.6 |
| Wooded badlands | 415 to 773 / 591 to 816 | 2.4 to 4.4 / 2.3 to 3.1 |
| Cherry grove | 156 to 222 / 185 to 240 | 13.0 to 17.7 / 12.0 to 15.0 |
| Plains | 210 to 408 / 235 to 384 | 158.8 to 291.7 / 168.7 to 261.1 |
| River | 103 to 259 / 200 to 519 | 522.1 to 1225.5 / 260.8 to 632.3 |

  - **Headline:** the top biomes are not wide, they are few. Mushroom fields: about 250 to 310 blocks across, only about 2.2 to 2.7 patches per 10,000 x 10,000 blocks, among the fewest of any biome (its range overlaps eroded badlands, wooded badlands, warm ocean and desert). Windswept gravelly hills and stony peaks are about as wide as pale garden but 1.5 to 2x fewer patches. Plains has about 60 to 100x as many patches as mushroom.
  - **Honest caveat (say it, or drop the beat):** widths grow when you use the 512 sight (51 of 56 biomes), so patches come in clusters and "width" is an effective number. 55 of 56 ranges still agree between the two sight radii; stony peaks does not. Rivers and caves are not convex patches, so treat them as hit-rate numbers only.
  - Pale garden is small (about 160 to 240 blocks) with a moderate count, which fits it dropping fast once you can see (section 4b).
- End card: three bar charts (0, 8, 32 chunks) with lines connecting each biome across them.

## 4c. Reading the ranking (8:40 to 10:30, the owner's section)

the owner's own reading, every point kept, mapped to the 26.3 ranking. Written out in his voice in VIDEO_SCRIPT.md section 4c. Where the data contradicts or adds to a point it is marked **[data]**.

**Expected**
- **#1 mushroom fields:** surprises nobody. Rare by surface area, and also biased by the spawn factor, biased away. **[data]** Never at spawn, about 0.14x within 512 blocks. Walk length effect +786 blocks (about 0.5%): a likely tiny bonus, not proven, and not why it is #1.
- **#2 to #5 (windswept gravelly hills, stony peaks, ice spikes, eroded badlands):** make sense, all very rare, niche, small biomes.
- **#11 to #19:** ordering is not that surprising.
- **The middle (about 20 to 47):** nothing surprising in there.
- **#48 onwards is the common category.** Ocean being common is definitely correct.
- **Plains and forest** being the most common makes sense. **[data]** Not quite: river is #56, forest #55, plains #54.

**Surprises**
- **#7 mangrove swamp.** Feels not that rare, "I stumble on it all the time". Maybe because it is big and rare. Or the latest SMP spawned near one. It is the more unique biome, so perception bias, compared with everything else that is just "plains". **[data]** "Big" is not checked with our data.
- **Windswept hills this low (16 to 18).** Nobody remembers what a windswept hills is, everyone notices a cherry grove, so people vote it rare because it is niche, not rare. **[data]** Backed: cherry grove (14 to 15) is rarer.
- **Old growth spruce and pine taiga (23 to 26) and sparse jungle (36 to 37) in the middle.** Niche, not rare.
- **Deep dark this common (#50, 2,981 blocks).** Insane, but it makes sense: it is a cave biome, and maybe rarity needs a definition that accounts for caves. It is under basically every tall mountain. The ancient city is what is rare, not the deep dark, a mental association. "Now that I think more about it, I do see deep dark everywhere." Same for other caves: less variety underground, so caves benefited more from the 3D biome update. **[data]** Under-mountain and 3D update points not checked. Sulfur caves (new) #49, dripstone #52, lush caves #53. Depends on the rule that a cave biome counts anywhere in the column, reachable or not.
- **River as the most common (#56, 763 blocks).** A bit surprising, since by area it is smaller than plains or forest. **[data]** Backed: 6.1% vs 10.2% and 12.2%. First guess: not affected by spawn bias, so no tails. **[data]** Contradicted: river is 0x at spawn. His second reason fits: the perfect line catcher.

- **Swept versions (owner):** pale garden dropping at 32 chunks makes sense, it is the clumpy small patch case, so at 32 chunks it gets close to its area ranking instead of its clumpiness. Eroded badlands is the opposite: huge inside badlands regions but sparse. So the radii give a rough guess at biome density. **[data]** Pale garden at 32 chunks (12 to 16) lands well below its area rank (0.147% of the world), so "gets to its area ranking" does not fit on 26.3. Eroded badlands rising to a proven #2 does fit "big but sparse".

**Callbacks to place**
- camman: by area we agree (windswept gravelly hills smallest, about 0.07%). By distance clumping matters. We differ at the top: mushroom fields #1.
- "Niche, not rare" works as the section's catchphrase.
- Where a reason is a guess (mangrove SMP bias, perception), say "my guess is" on camera.

## 5. Outro (10:30 to 11:10)

- Takeaway: "The rarest biome in Minecraft 26.3 is mushroom fields: almost seven and a half hours of sprinting from spawn, and still #1 no matter how far you can see." (Proven: #1 alone at 0, 8 and 32 chunks.)
- Honest limits, 2 lines max: Java 26.3 worldgen; a straight line from spawn over land or water, so distance not time; "found" means the biome is there, not that you looked at it. Caves count at any depth, reachable or not.
- Call to action: code and maths are open source. "I already found two mistakes myself, so go check."

## My take on the convergence proof

You are right that the proof itself would kill retention. But cutting the topic entirely is a mistake, because "how do you know your numbers are right" is the first comment on any stats video, and you have an unusually good answer. The 43% bias is the hook: it is a real mistake you made, it has a visual (a patch slipping between grid dots), and it teaches the one idea a general audience can actually take away, that more data does not fix a biased method. So: no proof, no notation, one 60 to 75 second story, and point to THEORY.md for anyone who wants the maths. (Update: the owner chose "mathematically" as the headline instead, so the 43% now opens section 3 as the reason that word has to be earned.)

## Open items before recording

- camman's distance method is still unknown ([CHECK] lines in the script).
- Patch size and count table: DONE on 26.3 (see section 4b nerd beat). Decide on camera whether to use it.
- Area vs walk flip: compute an area share ranking from the same seeds if section 1 wants that punch.
- Footage list: one clip per top 5 biome, plus pale garden, mangrove, windswept hills vs cherry grove, deep dark and an ancient city, a river crossing, spawn, and the dot grid shot.
