# I Found the Rarest Biome in Minecraft, Mathematically (script v4)

Working title / thumbnail text: "I found the RAREST biome in Minecraft... MATHEMATICALLY"

v4 (2026-11-27): rewritten for fun. Less maths talk, less hedging, more jokes, same facts. Every number is unchanged from v3
(Minecraft Java 26.3, 215,000 worlds at sight radius 0, 10,000 each at 8 and 32 chunks; sources in `out/certwalk263_r0/` and
`out/certwalk263_r128_512/`). Khiem's own reactions in 4c are all still there, point by point, just punchier.
Sprint times use 5.612 blocks per second.

Voice over is plain text. `[VISUAL: ...]` is what is on screen. `[GAG: ...]` is a quick visual joke, built in Resolve
(text pop, zoom, freeze frame). `[CHECK: ...]` is something to confirm before recording. `[beat]` means a short pause.

---

## 0. Cold open

[VISUAL: thumbnail wall of camman18's rarest biome videos, credited on screen]

If you've ever googled "rarest biome in Minecraft", you've watched camman18. And if you've watched camman18, you've watched him change his answer. A lot.

[VISUAL: the April 2021 short, then the 1.17 video, each with its title big on screen]

First, in 2021: "The Rarest Biome in Minecraft." Modified jungle edge. Then, a couple of months later: "the rarest biome in Minecraft 1.17." Still modified jungle edge, and mushroom fields weren't even in his top five. Consistent. Respect.

[VISUAL: pale garden short, title on screen]

Then in 2026: "The REAL Rarest Biome in Minecraft." Oh. So the first two were fake? Now it's the pale garden.

[VISUAL: windswept gravelly hills short, title on screen]

Then the pale garden got bigger in an update, so: "the REAL, real rarest biome." Windswept gravelly hills.

[VISUAL: eroded badlands short, title on screen]

Then he measured it a different way: "the REAL, real, real rarest biome." Eroded badlands.

Five videos. Four answers. Three reals. Camman, I love you, but the next one is going to be "the REAL, real, real, real rarest biome", and at some point that stops being a title and starts being a cry for help.

[GAG: the five titles stack up one by one, each "real" popping in bigger: "The Rarest Biome", "the rarest biome 1.17", "The REAL Rarest Biome", "the REAL, real rarest biome", "the REAL, real, real rarest biome". A sixth slot types itself out: "the REAL, real, real, real rarest biome...?"]

[VISUAL: quick cuts of forum posts and wiki pages, each naming a different biome]

And the rest of the internet? Worse. Everyone has an answer. Nobody has a proof.

[VISUAL: seed counter spinning up past 200,000, fast biome cuts]

So I generated two hundred and fifteen thousand Minecraft worlds, walked through every single one of them, and found the rarest biome. Not "I think". Not "probably". Proven.

[beat]

And yes, it's going to be a different answer again. Sorry camman.

[VISUAL: title card]

---

## 1. What does "rare" even mean?

First problem: nobody agrees on what "rare" means. So let's try a few.

Option one: ask the wiki, or the community. That's vibes. Half of it is from versions older than some of you watching.

[GAG: "SOURCE: trust me bro" stamp over a wiki page]

Option two: measure how much of the world each biome covers. That's camman's area video. Sounds objective. Watch this.

[VISUAL: two panels. Left: 36 small teal patches. Right: one big orange blob. Same total area.]

These two biomes cover exactly the same amount of land. But if you're wandering around, you'll trip over the left one constantly, and you can walk right past the big blob without ever seeing it. Area doesn't care how a biome is spread out, and the spread is most of what decides whether you find it. Camman actually says this himself in his distance video, which is why his answers keep changing.

Option three, and honestly my first idea: drop yourself at a random spot and count how far you walk until you find the biome. That fixes the spread problem.

But there's a catch. You never start at a random spot. The game picks where you spawn.

[VISUAL: heat map of where spawns land vs an even scatter of random points]

And the game is picky. Like, really picky.

[VISUAL: bar chart of the spawn effect. Land biomes up at 1.7 to 1.9x, oceans, rivers and beaches at zero.]

You're almost twice as likely to spawn in plains, forest or desert as you'd expect. Ocean or river? Never. Not once in two hundred and fifteen thousand worlds. The game would rather die than spawn you in water.

Beaches are weird. You basically never spawn right on one, but there's very often one nearby, because the game loves putting you on land right next to the coast.

And some biomes get pushed away from spawn entirely. Remember that. It comes back.

[VISUAL: spawn effect curves sliding back to 1 by 2,000 blocks]

The good news: all of this wears off after about two thousand blocks. The rare biomes are way further out than that. So spawn picks your starting line, then gets out of the way.

So here's my definition, and it's close to camman's distance idea. Start where the game actually puts you. Pick a direction. Walk. Count the blocks until you find the biome. No cutoff, no shortcuts.

[CHECK: camman's short says "average distance from spawn" but never says how he measured it (checked the captions, 2026-11-27). So the next line describes only how I walk, not his method. Keep it that way unless he confirms.]

The difference: I walk blind, like a real player exploring, with no map telling me where the nearest patch is. And every number comes with a proof, because that's the whole point of this video.

[VISUAL: spawn dot, one straight ray, distance counter ticking up from 0]

And the walk is a straight line. If you wander around in circles, you're measuring how bad you are at walking, not how rare the biome is.

[GAG: a tiny squiggly path doing loops next to the straight ray]

---

## 2. Monte Carlo: just make a lot of worlds

There's no formula for Minecraft terrain. But there is a seed, and every seed is a whole world.

[VISUAL: darts thrown at a square with a circle inside, estimate of pi settling]

So I used the oldest trick in the book. If you can't calculate something, simulate it a ridiculous number of times and take the average. It's called Monte Carlo, after the casino, which is fitting, because you're basically gambling until the answer stops moving. One dart tells you nothing. Thousands of darts, and suddenly you know pi.

[VISUAL: one real seed's map. Spawn dot. One ray shoots out in a random direction. Each biome lights up the first time the ray touches it, with its distance.]

Here's one real world. Start at spawn, pick a random direction, walk. Every time I hit a new biome, I write down how far I've gone. So one walk gives me a distance for every biome at once.

[VISUAL: zoom out to hundreds of maps tiled, one ray each, running averages wobbling then flattening]

Then a new world. And another. Two hundred and fifteen thousand times.

[GAG: counter in the corner "worlds walked: 215,000", "blocks walked: a lot"]

The worlds come from Cubiomes, a tool that runs the real Minecraft world generator without the game, here the version for 26.3. So these are real worlds, block for block, the same ones you'd get in game.

---

## 3. How do I know it's right?

Okay. "Mathematically" is a big word in a title. So let me earn it, by telling you about the two times I got it completely wrong.

[VISUAL: dot grid laid over terrain, one dot every 16 blocks]

Mistake number one. To make the code fast, I only checked the biome every 16 blocks. The results looked amazing. Tiny error bars. More worlds, even tinier error bars. I was very proud of myself.

[VISUAL: zoom into a small pale garden patch sitting between the dots. The grid steps right over it.]

Then I checked it against a version that looks at every single block. Turns out small patches fit right between my dots, so I kept stepping over them. Pale garden came out 43 percent further away than it really is.

[GAG: "43%" slams onto the screen, then a small "oops" underneath]

[VISUAL: dartboard. Tight cluster of darts, nowhere near the bullseye.]

And here's the scary part. More worlds would never have fixed it. If your arm is bent, throwing a million more darts just makes you very confidently wrong. Precise is not the same as correct.

Mistake number two was even dumber. Halfway through making this video, camman's pale garden short made me check which version of the game my generator was running.

[beat]

It was 1.21.4. The update right before pale gardens got bigger. So everything I had was for the wrong game. I threw it all away and ran it again on 26.3.

[VISUAL: old ranking with pale garden at #2, a big red "1.21.4" stamp, then it shatters]

Lesson learned: maths can prove your code is right. It can't tell you you're running the wrong version of Minecraft. That one's on you.

So now it checks every single block, on the current version, and every number in this video comes with a range that's proven to contain the real answer. The chance that any of them is wrong is one in five hundred thousand. For scale, a naturally pink sheep is about one in six hundred. You are going to see a lot of pink sheep before I'm wrong.

[CHECK: pink sheep natural spawn chance is 0.164 percent on the Minecraft Wiki (about 1 in 610). Confirm on the current wiki page before recording.]

[VISUAL: GitHub link, THEORY.md]

The full proof is on GitHub, if you're into that sort of thing. And when two biomes are too close to call, I won't pretend. I'll call it a tie.

---

## 4. The countdown

Okay. The rarest biomes in Minecraft 26.3. Measured as how far you walk from spawn until you actually step on the biome.

[VISUAL: footage of each biome, distance and sprint time on screen]

Number five. Eroded badlands. Seventy thousand blocks. That's three and a half hours of sprinting in a straight line. That's longer than Titanic. This was camman's latest answer, and it's not even top three.

Number four. Ice spikes. About seventy-five thousand blocks. Three hours forty of holding W.

Number three. Stony peaks. Eighty-four thousand blocks, over four hours. It's a grey mountain. That's it. That's the biome. Four hours.

[GAG: freeze frame on the most boring grey rock, caption "four hours for this"]

Number two. Windswept gravelly hills. Ninety-five thousand blocks, almost five hours. It's the smallest biome in the game by area, and I promise you've never once said its name out loud.

[VISUAL: pale garden sliding from #2 down to #6]

And if you're wondering where pale garden went: on the old version it was number two. Then the update made it bigger, and it fell all the way to six. Fell off, honestly.

And number one.

[beat]

[VISUAL: mushroom island reveal]

Mushroom fields. A hundred and fifty thousand blocks. That's seven and a half hours of sprinting in a straight line from spawn. That's a full school day of holding W. It's more than one and a half times further than anything else on this list.

They're huge once you find one. There are just barely any of them, and they hide way out in the middle of the ocean.

And remember the biome spawn pushes away? It's this one. You never spawn on mushroom fields. Within 512 blocks of spawn they're about a third as likely as anywhere else, at best. It doesn't change the ranking though, because that push fades after two thousand blocks, and you've still got a hundred and forty-eight thousand to go.

[VISUAL: full ranking bar chart, each bar with its range as a thin band]

And this order is proven. One through seven, locked in: pale garden sixth, mangrove swamp seventh. The first tie doesn't show up until number eight.

But here's the thing. You don't walk around with your eyes closed.

---

## 4b. Now open your eyes

[VISUAL: the same ray, now with a glowing band around it, 8 chunks wide, then 32]

In real life you find a biome the moment you see it. So I ran it all again, where a biome counts once it's within 8 chunks of you, which is about what a normal player notices. And then 32 chunks, which is a hardcore biome hunter on max render distance.

[beat]

Or a cheat client. No judgement.

[GAG: "no judgement" in small text, eyes emoji style icon]

Seeing further helps small patches the most. A tiny patch is hard to step on but easy to spot from 500 blocks away. A big blob was never hard to hit in the first place.

[VISUAL: three bar charts side by side, 0, 8 and 32 chunks, lines connecting each biome across them]

Mushroom fields does not care. Number one at every distance, alone, proven. Over three and a half hours of sprinting at 8 chunks, an hour and a half at 32. You can't see something that isn't there.

Everything below it, though, falls apart. At 8 chunks, windswept gravelly hills, eroded badlands, ice spikes, mangrove, wooded badlands and stony peaks all land somewhere between two and seven, and they're too close to call. Six-way tie for second. Everybody gets a participation trophy.

Pale garden just keeps falling. Sixth if you have to step on it, eight to eleven at 8 chunks, and twelve to sixteen at 32. Its patches are tiny, so they're hard to step on but really easy to spot.

At 32 chunks, eroded badlands climbs to a proven second. About an hour and ten minutes. It's the reverse of pale garden: big patches, but so few and so far apart that seeing further helps everything else more. And it drags the whole badlands family up with it. Wooded badlands goes to three to six, plain badlands to four to eight.

[VISUAL: on screen table, 26.3]
[mushroom fields: #1, 149,522 | #1, 73,730 | #1, 31,630]
[eroded badlands: #5, 70,084 | 2 to 5, 42,295 | #2, 23,970]
[windswept gravelly hills: #2, 94,893 | 2 to 5, 42,378 | 3 to 7, 19,530]
[pale garden: #6, 62,471 | 8 to 11, 26,573 | 12 to 16, 10,637]

And look at that: eroded badlands near the top. That's starting to look like camman's distance ranking. The further you can see, the closer you get to his answer. But even at 32 chunks, mushroom fields stays ahead, and that gap is proven.

So which ranking is "the" answer? Depends how far you can see. But the one thing every version agrees on is number one.

---

## 4c. Reading the ranking

[NOTE: Khiem's own reactions, every point kept from v3, wording made punchier. [data] lines are facts to say or show alongside his take.]

So, does this ranking actually make sense? Let's go through it.

Mushroom fields at number one doesn't surprise anyone. It's rare by area, sure. But it's also biased by spawn, and it's biased away. You basically never spawn next to one.

Not once in two hundred and fifteen thousand worlds. That push probably makes the walk a tiny bit longer, my best guess is about 786 blocks, so half a percent. Too small to prove, and it's not why mushroom wins anyway. It wins because there's barely any of it, and what there is lives in the middle of the ocean.

Two to five make total sense. Those are all very rare, very niche, very small biomes.

Seven, though. Mangrove swamp. That one surprised me. I feel like I stumble into mangroves all the time. But maybe that's because they're big and rare, so when you do find one, it's a LOT of mangrove. Or maybe my last SMP just spawned next to one and I'm biased. It's also just a really unique biome. You remember every mangrove you've ever been in. Everything else is just "plains" to me.

Eleven to nineteen, nothing too surprising. Except windswept hills, sixteen to eighteen. That's low. But again, that's a memory thing. Literally nobody remembers what a windswept hills looks like. But everyone notices a cherry grove. So when people vote windswept hills as rarer, they're voting for "niche", not "rare".

[data: cherry grove is 14 to 15, so it's actually rarer than windswept hills (16 to 18). Dappled forest, the new 26.3 biome, is tied with windswept hills.]

The middle, nothing crazy. What did surprise me is that both old growth taigas and sparse jungle are way down here. Old growth spruce and pine taiga at around twenty-three to twenty-six, sparse jungle at thirty-six to thirty-seven. Niche, not rare. Same story.

From about forty-eight onward, it's the common stuff. Ocean being common? Yeah. Correct. Thank you.

[VISUAL: on screen note: "cave biomes count once you pass over them at any depth, reachable or not"]

Deep dark being this common is insane though. Number fifty. About three thousand blocks. Three thousand! But I guess it makes sense. It's a cave biome, it's under basically every tall mountain. Which honestly means maybe we need a different definition of rare for caves. Because the ancient city is what's rare. Not the deep dark. My brain just glued the two together. And now that I think about it, I do see deep dark everywhere. Same with the other caves. There's way less variety underground, so caves got a massive boost from the 3D biome update.

[data: sulfur caves, new in 26.3, is number 49, about four thousand blocks. Dripstone 52, lush caves 53.]

Plains and forest being the most common makes sense.

Except. They're not the most common.

[beat]

River is. About seven hundred and sixty blocks on average. And that's weird, because by area, river is smaller than plains or forest. My first guess was spawn, that rivers just don't get pushed around by spawn. Nope. You literally never spawn in a river. It's the shape. Rivers are long thin lines cutting through everything, so any straight walk crosses one almost immediately. River is the ultimate line catcher.

[data: river is 0x at the spawn point in 26.3, so spawn does affect it, just the other way. The shape is what wins.]

[VISUAL: callback to the camman18 clips]

So, camman. By area, we agree. Windswept gravelly hills covers the least of the world in my numbers too, about 0.07 percent. And on distance, you were right that how a biome is spread out changes everything. Where we split is the top. With a blind walk and a proof, mushroom fields is number one, and it's not close.

[CHECK: his distance short has mushroom fields second, just behind eroded badlands. Optional extra line: "In your distance video, mushroom fields was literally second. So close, camman." His method is still unknown, so do not describe it.]

The REAL, real, real, real rarest biome. You're welcome.

---

## 5. Outro

So. The rarest biome in Minecraft 26.3 is mushroom fields. Seven and a half hours of sprinting from spawn if you have to step on it, and still number one no matter how far you can see.

A few honest limits, quickly. This is Java 26.3. The walk is a straight line from spawn, over land and water, so it's distance, not time. Nobody is actually sprinting across the ocean for seven hours. And "found" means the biome is there, not that you actually looked at it.

[VISUAL: GitHub repo link]

All the code is open source, and so is the maths. If you think I got something wrong, go check. I've already found two of my own mistakes, so honestly, it's a fair request.

[beat]

See you in the next one. Hopefully closer to spawn.
