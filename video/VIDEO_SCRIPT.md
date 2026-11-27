# I Found the Rarest Biome in Minecraft, Mathematically (script draft v3)

Working title / thumbnail text: "I found the RAREST biome in Minecraft... MATHEMATICALLY"

Voice over is plain text. `[VISUAL: ...]` lines are what is on screen. `[CHECK: ...]` lines are things to confirm before recording.
About 1,600 words of voice over, so roughly 10 to 11 minutes at a normal talking pace.

**Numbers:** Minecraft Java 26.3 worldgen (xpple/cubiomes fork), certified walk from spawn, caves included, 215,000 seeds. Sources: `/mnt/project-files/results/mc263_r0_report.md`, `mc263_r0_order.md`, `mc263_r0_spawnratio.md`. All ranges hold together except with a 1 in 500,000 chance.
**All numbers final:** 26.3 worldgen, r = 0 on 215,000 worlds, 8 and 32 chunks on 10,000 worlds each.

---

## 0. Cold open (0:00 to 0:40)

[VISUAL: thumbnail wall of camman18's rarest biome videos, credited on screen]

If you have ever googled "rarest biome in Minecraft", you have probably watched camman18. He has been ranking these for years.

Years ago it was modified jungle edge, and mushroom fields did not even make his top five.

[VISUAL: clip from "The REAL Rarest Biome in Minecraft..." (youtube.com/shorts/12UgiwOo28k): pale garden first by area]

Then, by area, it was the pale garden.

[VISUAL: clip from "the REAL, real rarest biome in Minecraft..." (youtube.com/shorts/ZnfLg6UiDYw): windswept gravelly hills, after the pale garden buff]

Then pale garden got bigger in an update, so he ran his own simulation, and the answer became windswept gravelly hills.

[VISUAL: clip from "the REAL, real, real rarest biome in Minecraft..." (youtube.com/shorts/HVfXIyuudTY): eroded badlands by distance from spawn]

Then he measured distance from spawn instead, and it became eroded badlands.

Four videos, four different answers. Not one of them agrees with any of the others. I say that with love, camman, but at some point "the REAL, real, real rarest biome" stops being a title and starts being a cry for help.

And honestly, fair enough, because nobody agrees on what "rare" even means.

[VISUAL: quick cuts of forum posts and wiki pages, each naming a different biome]

The rest of the internet gives you five more answers. Everyone has a number. Nobody has a proof.

[VISUAL: seed counter spinning up past 200,000]

So I generated two hundred and fifteen thousand real Minecraft worlds, walked through every single one of them, and worked out the rarest biome in Minecraft. Mathematically. Not "I think". Proven.

[VISUAL: title card: "I found the RAREST biome in Minecraft... MATHEMATICALLY"]

---

## 1. What does "rare" even mean? (0:40 to 2:40)

Before ranking anything, we have to agree on what rare means. There are a few ways to measure it, and most of them are worse than they sound.

The easiest one is the wiki, or just what the community says. But that is an opinion. Half of it comes from old versions, and nobody tells you what "rare" was measured by.

Okay, so be objective. Take the percentage of the world each biome covers. That is camman's area video.

[VISUAL: two panels. Left: 36 small teal patches. Right: one big orange blob. Same total area.]

These two biomes cover exactly the same area. But if you are wandering around, you are going to bump into the one on the left way more often. The blob on the right is easy to miss completely. Area does not care how a biome is clumped, and clumping is most of what decides whether you find it. Camman makes this exact point in his distance video: lots of small patches can be easier to find than a few big ones. That is why his answers keep changing.

So the next idea, and honestly my own first idea, is the mean free path: drop yourself at a random point in the world and measure how far you walk until you find the biome. That fixes clumping.

But there is a catch. You never start at a random point. The game picks your spawn.

[VISUAL: heat map of where spawns land vs an even scatter of random points]

And the game is picky. I measured how much more likely your spawn point is to be in each biome than a random spot, with area divided out.

[VISUAL: bar chart of the spawn effect. Land biomes up at 1.7 to 1.9x, oceans, rivers and beaches at zero.]

Plains, forest and desert are around one and three quarter to two times more likely at spawn. Oceans and rivers never happen, not once in two hundred and fifteen thousand spawns. Beaches are weird: you basically never spawn right on one, but you are more likely than average to have one within 128 blocks of you, because spawn loves land right next to the coast.

And some biomes get pushed away from spawn entirely. Hold that thought, it comes back later.

[VISUAL: spawn effect curves sliding back to 1 by 2,000 blocks]

Here is the catch though. All of that is gone after about two thousand blocks. The rare biomes are much, much further away than that, so spawn shapes the start of your walk, then stops mattering.

So this is the metric I use, and yes, it is close to camman's distance idea: start where the game actually puts you, walk, and count the blocks until you find the biome. Nothing cut off. It handles clumping, because you are actually walking. And it handles spawn, because it starts at spawn. It is also the only one of these metrics that can measure the spawn effect at all, which is how I know it is that small.

[CHECK: his short does not say how "average distance from spawn" was measured. If it is the nearest patch in any direction (you know where to go), that is a different question from ours (you walk without a map). Do not describe his method on camera unless you can confirm it.]

The difference is two things. One, I walk blind, the way a player actually explores, instead of already knowing where the nearest patch is. And two, every number comes with a proof, which is the whole point of this video.

[VISUAL: spawn dot, one straight ray, distance counter ticking up from 0]

Quick note: the walk is a straight line. A wandering walk keeps re-checking ground it has already seen, which tells you more about how you wander than about the biome.

---

## 2. Monte Carlo: just make a lot of worlds (2:40 to 4:00)

There is no formula for Minecraft terrain. But there is a seed, and a seed is a whole world.

[VISUAL: darts thrown at a square with a circle inside, estimate of pi settling]

So I did the classic trick. If you cannot calculate something, simulate it a lot and average. It is the same idea as throwing darts at a square to estimate pi. One dart tells you nothing. Thousands of darts, and the answer settles.

[VISUAL: one real seed's map. Spawn dot. One ray shoots out in a random direction. Each biome lights up the first time the ray touches it, with its distance.]

Here is one real world. Start at spawn, pick a random direction, walk. Every time the ray touches a biome for the first time, write down the distance. One walk gives you a distance for every biome at once.

[VISUAL: zoom out to hundreds of maps tiled, one ray each, running averages wobbling then flattening]

Then do it again in a new world. And again. Two hundred and fifteen thousand times.

The worlds come from Cubiomes, which runs the real Minecraft world generator without the game, here the version for 26.3. So these are real worlds, not some approximation of them.

---

## 3. How do I know it is right? (4:00 to 5:15)

Now, "mathematically" is a big word, so let me earn it. Because I got it wrong twice.

[VISUAL: dot grid laid over terrain, one dot every 16 blocks]

The first time, my code was built to be fast, so it only checked the biome every 16 blocks. And the results looked great. Tiny error bars. More worlds, even tinier error bars.

[VISUAL: zoom into a small pale garden patch sitting between the dots. The grid steps right over it.]

Then I checked it against a version that looks at every single spot. Small patches fit between the dots, so the grid kept stepping right over them. Pale garden came out 43 percent further away than it really was.

[VISUAL: dartboard. Tight cluster of darts, nowhere near the bullseye.]

And here is the part that actually matters. More worlds would never have fixed that. Throw a million more darts with a bent arm and you just get a very confident wrong answer. Precise is not the same as correct.

The second time was the game itself. Halfway through making this video, camman's pale garden short made me check which version my generator was running. It was 1.21.4, the update right before pale gardens got bigger. So I threw everything away and reran it all on 26.3.

[VISUAL: old ranking with pale garden at #2, a big red "1.21.4" stamp, then it shatters]

Maths can prove the code matches the model. It cannot tell you that you picked the wrong version of the game. You have to check that yourself.

So now it checks every spot, on the current version, and every number in this video comes with a range that is mathematically proven to contain the true value, all at once, with at most a one in five hundred thousand chance of being wrong. The proof is on GitHub if you are into that.

[VISUAL: GitHub link, THEORY.md]

And when two ranges overlap, I am not going to pretend I know which biome is rarer. I will call it a tie.

---

## 4. The countdown (5:15 to 7:15)

Okay. Rarest biomes in Minecraft 26.3, measured as the average walk from spawn. For this first ranking you have to actually step on the biome.

[VISUAL: footage of each biome, distance and sprint time on screen]

Number five. Eroded badlands. Seventy thousand blocks. That is three and a half hours of sprinting in a straight line without stopping. This was camman's answer by distance, and it is not even close to first here.

Number four. Ice spikes. About seventy-five thousand blocks, about three and three quarter hours.

Number three. Stony peaks. Eighty-four thousand blocks, a bit over four hours.

Number two. Windswept gravelly hills. Ninety-five thousand blocks, almost five hours. It covers the least area of any biome in the game, and most people could not tell you what it looks like.

[VISUAL: pale garden sliding from #2 down to #6]

And if you are wondering where pale garden went: on the old version it was number two. After the update made it bigger, it drops to number six.

And number one.

[VISUAL: mushroom island reveal]

Mushroom fields. A hundred and fifty thousand blocks. That is almost seven and a half hours of sprinting, in a straight line, from spawn. More than one and a half times further than anything else. They are big once you find them, but there are so few of them, and they only show up far out in the ocean.

Remember the biome spawn pushes away? This is it. You never spawn on one, and within 512 blocks of spawn you are at most about a third as likely to find one as from a random spot. It just does not change the ranking, because that push is gone after two thousand blocks, and this walk is a hundred and fifty thousand.

[VISUAL: full ranking bar chart, each bar with its range as a thin band]

And these are not vibes. The top seven are each proven to be in that order: pale garden at six and mangrove swamp at seven. The first tie is at eight.

But you do not walk around with your eyes closed.

---

## 4b. Now open your eyes (7:15 to 8:40)

[VISUAL: the same ray, now with a glowing band around it, 8 chunks wide, then 32]

In real gameplay you find a biome the moment you see it. So I ran it again where a biome counts once it is within 8 chunks of you, which is roughly what a normal player would notice. And then 32 chunks, which is a hardcore biome hunter with max render distance. Or a cheat client. No judgement.

Seeing further helps small patches the most. A tiny patch is hard to step on but easy to spot from 500 blocks away. A big patch was never hard to hit in the first place.

[VISUAL: three bar charts side by side, 0, 8 and 32 chunks, lines connecting each biome across them]

Mushroom fields does not care. Number one at every distance, alone, and proven. About three and a half hours of sprinting at 8 chunks, an hour and a half at 32. You cannot see something that is not there.

At 8 chunks, everything below it collapses. Windswept gravelly hills, eroded badlands, ice spikes, mangrove, wooded badlands and stony peaks all land somewhere in two to seven, and the maths can't separate them. Once you can actually see, nobody wins second place.

Pale garden keeps falling. Sixth if you have to step on it, eight to eleven at 8 chunks, and twelve to sixteen at 32. Its patches are tiny, so they were hard to step on but really easy to spot.

At 32 chunks, eroded badlands climbs to a proven second. About an hour and ten minutes. It's the opposite of pale garden: its patches are big but sparse, few and far apart, so seeing further helps everything else more than it helps you find badlands. And the whole badlands family climbs with it. Wooded badlands goes to three to six, plain badlands to four to eight.

[VISUAL: on screen table, 26.3]
[mushroom fields: #1, 149,522 | #1, 73,730 | #1, 31,630]
[eroded badlands: #5, 70,084 | 2 to 5, 42,295 | #2, 23,970]
[windswept gravelly hills: #2, 94,893 | 2 to 5, 42,378 | 3 to 7, 19,530]
[pale garden: #6, 62,471 | 8 to 11, 26,573 | 12 to 16, 10,637]

And notice what that looks like: eroded badlands near the top. That is starting to look like camman's distance from spawn ranking. The further you can see, the closer you get to "how near is the nearest patch", which is his question. But even at 32 chunks, mushroom fields stays ahead, and that gap is proven.

So which ranking is "the" answer? Honestly, it depends on how far you can see. The only thing every version agrees on is number one.

[NOTE: 8 and 32 chunk runs are 10,000 worlds each, same 1 in 500,000 guarantee as the main run.]

---

## 4c. Reading the ranking (8:40 to 10:30)

[NOTE: Khiem's own reading, kept point by point from his notes, wording cleaned up only. Lines marked [data] are where the 26.3 numbers add to or correct a point. Rewrite freely.]

So does this ranking actually make sense?

Mushroom fields being the rarest doesn't surprise most people. It's rare by surface area, sure. But it's also biased by the spawn factor, and it's biased away. You basically never spawn next to one.

[data: you never spawn on one in 215,000 worlds, and within 512 blocks of spawn it's about 0.14x as likely as from a random spot. So the spawn push-away is likely a tiny bonus on top: our best estimate is about +786 blocks, roughly 0.5% of the walk. It's too small to prove (the range includes zero), and it's not why mushroom is #1. That comes from it being tiny and far out in the ocean.]

Two to five make sense. Those are all very rare, very niche biomes, and they're all very small.

Seven is quite surprising to me. Mangrove swamp. I feel like mangroves are not that rare, I stumble on them all the time. But maybe that's because they're big and rare, so when you do find one it's a lot of mangrove. Or maybe my latest SMP just spawned near one and I'm biased. It's also the more unique biome anyway. You remember every mangrove you see. So perception bias is probably one of the reasons too, compared to everything else, which is just "plains" to me.

Eleven to nineteen, the ordering is not that surprising. Windswept hills being this low is kind of surprising though. Sixteen to eighteen. But again, it's a bias thing. Literally nobody ever remembers what a windswept hills is. But people will 100% always notice a cherry grove. So the people who vote windswept hills as rarer are doing it purely because it's niche, not because it's rare.

[data: cherry grove is 14 to 15, rarer than windswept hills at 16 to 18. Dappled forest, the new 26.3 biome, is tied with windswept hills.]

Then the middle. Nothing in there is that surprising. What is surprising is that both old growth taigas and sparse jungle are down here. Old growth spruce and pine taiga at around twenty-three to twenty-six, sparse jungle at thirty-six to thirty-seven. But again, niche, not rare.

From about forty-eight onward it's very much the common category already. The ocean being common is definitely correct.

Deep dark being this common is insane though. Number fifty, about three thousand blocks. But I guess it makes sense. It's a cave biome, which honestly maybe means we need to define rarity in a way that accounts for that. Deep dark is under basically every tall mountain, so the fact that it's up here is not that surprising. The ancient city is what's rare, not the deep dark. It's a mental association thing. But now that I think more about it, I do see deep dark everywhere. Same with the other cave biomes. There's way less variety underground, so caves in general benefited a lot more from the 3D biome update.

[VISUAL: on screen note: "cave biomes count once you pass over them at any depth, reachable or not"]

[data: sulfur caves, new in 26.3, is number 49, about four thousand blocks. Dripstone 52, lush caves 53.]

Plains and forest being the most common makes sense.

Except they're not quite the most common. River is. About seven hundred and sixty blocks on average. That's a bit surprising, because by area river is smaller than plains or forest. My first guess was spawn, that river just isn't affected by spawn bias so it doesn't get the long tails. But that's not it, you actually never spawn in a river. It's the shape. Rivers are thin lines that cut through everything, so a straight walk crosses one almost immediately. River is the perfect line catcher.

[data: river is 0x at the spawn point in 26.3, so it is spawn affected, just in the other direction. The line catcher shape is what wins.]

[VISUAL: callback to the camman18 clips]

So, camman. By area, we agree. Windswept gravelly hills covers the least of the world in my numbers too, about 0.07 percent. And by distance, you were right that clumping changes everything. Where we differ is the top. With a blind walk and a proof, mushroom fields is number one, and it is not close.

[CHECK: if his distance method turns out to be nearest patch in any direction, add one line saying the two rankings answer slightly different questions, so neither is wrong.]

---

## 5. Outro (10:30 to 11:10)

So, the rarest biome in Minecraft 26.3 is mushroom fields. Almost seven and a half hours of sprinting from spawn if you have to step on it, and still number one no matter how far you can see.

A few honest limits. This is Java 26.3 world generation. The walk is a straight line from spawn, over land or water, so it is distance, not time. And "found" means the biome is there, not that you actually looked at it.

[VISUAL: GitHub repo link]

All the code is open source, and so is the maths. If you think I got something wrong, go check. I already found two mistakes myself, so it is a fair request.
