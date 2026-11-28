# Voice-over read script

## Section 0

*(camman: "What's the rarest biome in Minecraft?")*

**V001**  If you've ever googled that, you've watched camman18. And if you've watched camman18, you've watched him change his answer. A lot.

**V002**  2021.

*(camman: "The rarest biome is actually the Modified Jungle Edge")*

**V003**  A couple of months later.

*(camman: "You might think it's the Mushroom Island, but it's not even close. It's not even in the top five rarest.")*

*(camman: "The rarest biome in Minecraft is the Modified Jungle's Edge")*

**V004**  Still modified jungle edge. Consistent. Respect.

**V005**  Then, 2026: "The REAL Rarest Biome in Minecraft."

*(camman: "And in first place, the pale garden?")*

**V006**  Oh. So the first two were fake?

*(camman: "The rarest biome in Minecraft isn't the Pale Garden. I did say this like, a month ago, oops,")*

**V007**  Oops.

*(camman: "meaning the rarest biome in Minecraft by surface area,")*

*(camman: "is the windswept gravelly hills.")*

**V008**  "The REAL, real rarest biome." Okay.

*(camman: "While the windswept Gravely Hills takes up the least amount of the Minecraft world, it's not exactly the rarest biome.")*

**V009**  Of course it's not.

*(camman: "And by this metric, the rarest biome")*

*(camman: "is the Eroded Badlands.")*

**V010**  Five videos. Four answers. Three reals. Camman, I love you, but the next one is going to be "the REAL, real, real, real rarest biome", and at some point that stops being a title and starts being a cry for help.

**V011**  And the rest of the internet? Worse. wikiHow: "the rarest biome is the windswept gravelly hills."

**V012**  mcseedmap: "The rarest biome in Minecraft today is the Pale Garden."

**V013**  rarest.org: modified jungle edge. A biome that got deleted from the game in 2021.

**V014**  And oldest.org says... sunflower plains? Sure. Why not.

**V015**  Everyone has an answer. Nobody has a proof.

**V016**  So where do I come in? What do I actually bring to the table? Because simulating Minecraft worlds isn't new. People do it all the time. What I did first was write down exactly what "rare" means, as actual maths. Then I threw two hundred and fifteen thousand worlds at that definition. And here's the part that matters: the simulation is mathematically guaranteed to close in on that exact number. Not roughly. As close as I want. Want it tighter? Run more worlds. So not "I think". Not "probably". Proven, within a margin I get to pick.  *(pause)*

**V017**  And yes, it's going to be a different answer again. Sorry camman.

## Section 1

**V018**  First problem: nobody agrees on what "rare" means. So let's try a few.

**V019**  Option one: ask the wiki, or the community. That's vibes. Half of it is from versions older than some of you watching.

**V020**  Option two: measure how much of the world each biome covers. That's camman's area video. Sounds objective. Watch this.

**V021**  These two biomes cover exactly the same amount of land. But if you're wandering around, you'll trip over the left one constantly, and you can walk right past the big blob without ever seeing it. Area doesn't care how a biome is spread out, and the spread is most of what decides whether you find it. Camman actually says this himself in his distance from spawn video, which is why his answers keep changing. There's one more thing area misses, but you'll see it better in option three.

**V022**  Option three, and honestly my first idea: drop yourself at a random spot and count how far you walk until you find the biome. That fixes the spread problem.

**V023**  But there's a catch. You never start at a random spot. The game picks where you spawn. And that's a problem.

**V024**  And the game is picky. Like, really picky.

**V025**  You're almost twice as likely to spawn in plains, forest or desert as you'd expect. Ocean or river? Never. Not once in two hundred and fifteen thousand worlds. The game would rather die than spawn you in water.

**V026**  Beaches are weird. You basically never spawn right on one, but there's very often one nearby, because the game loves putting you on land right next to the coast.

**V027**  And some biomes get pushed away from spawn entirely. Remember that. It comes back.

**V028**  The good news: all of this wears off after about two thousand blocks. The rare biomes are way further out than that. So spawn picks your starting line, then gets out of the way.

**V029**  So here's my definition, and it's close to camman's distance idea. Start where the game actually puts you. Pick a direction. Walk. Count the blocks until you find the biome. No cutoff, no shortcuts.

**V030**  The difference: I walk blind, like a real player exploring, with no map telling me where the nearest patch is. And every number comes with a proof, because that's the whole point of this video.

**V031**  And the walk is a straight line. If you wander around in circles, you're measuring how bad you are at walking, not how rare the biome is. So no Brownian motion, for all you ball knowers out there.

**V032**  But hold on. Who am I to define Minecraft biome rarity? Why this way and not some other way? Why a straight line? Real players don't walk in perfectly straight lines. And what even counts as "finding" a biome? It loaded in your render distance? You saw it with your own eyes? You literally have to touch it?

**V033**  Well, here's my two-part answer.

**V034**  Part one: why a straight line? Think about how a pro player hunts for a biome. They pick roughly one direction and just keep going until something new shows up. Because going straight is one of the best ways to see new ground. Way better than wandering around at random.

**V035**  But what about a grid walk, going back and forth like a lawnmower? Fair. You probably cover new blocks just as fast. But Minecraft biomes aren't random block by block, where every spot could be any of the fifty-six biomes. They come from a few smooth noise maps, so biomes stick together. Any spot is probably the same biome as the spots around it.

**V036**  So a grid walk is actually worse. Every strip runs right next to the last one, through the same biomes you just saw. New blocks, sure, but not really new ground. A straight line never comes back, so almost everything it sees is genuinely new. More actually new ground, more new biomes.

**V037**  It's also the least made-up choice. Sure, I could walk straight and turn at random every so often, which looks more like a real player. But then I have to pick how often you turn, and by how much, and every one of those numbers is me inventing stuff. The straight line has zero settings, just a random direction. And the drifting a real player does? That's human error. I don't want human error baked into a maths definition.

**V038**  Part two: what counts as "found"? Honestly? I don't know. So I did all three.

**V039**  The main one, and the one I think is fairest because it's the least arbitrary: you have to literally be standing in the biome. Is that realistic? Not really. But this is a way to measure rarity, not a player simulator. Whether it's realistic is up for debate... I guess.

**V040**  But I literally just argued "this is what real players do", so, as the very nuanced person I am, I also ran it where a biome counts once it's within 8 chunks of you, and within 32.

**V041**  Are those numbers arbitrary? As heck. Eight I pulled out of my ass. Thirty-two is at least the max render distance in Java, so a bit less made up. But if you're spotting biomes from thirty-two chunks away, you're less a vanilla player and more a 2b2t hack client bot. But I digress.

## Section 2

**V042**  There's no formula for Minecraft terrain. But there is a seed, and every seed is a whole world.

**V043**  So I used the oldest trick in the book. If you can't calculate something, simulate it a ridiculous number of times and take the average. It's called Monte Carlo, after the casino, which is fitting, because you're basically gambling until the answer stops moving. One dart tells you nothing. Thousands of darts, and suddenly you know pi.

**V044**  Here's one real world. Start at spawn, pick a random direction, walk. Every time I hit a new biome, I write down how far I've gone. So one walk gives me a distance for every biome at once.

**V045**  Then a new world. And another. Two hundred and fifteen thousand times.

**V046**  The worlds come from Cubiomes, a tool that runs the real Minecraft world generator without the game, here the version for 26.3. So these are real worlds, block for block, the same ones you'd get in game.

## Section 3

**V047**  Okay. "Mathematically" is a big word in a title. So let me earn it, by telling you about the two times I got it completely wrong.

**V048**  Mistake number one. To make the code fast, I only checked the biome every 16 blocks. The results looked amazing. Tiny error bars. More worlds, even tinier error bars. I was very proud of myself.

**V049**  Then I checked it against a version that looks at every single block. Turns out small patches fit right between my dots, so I kept stepping over them. Pale garden came out 43 percent further away than it really is.

**V050**  And here's the scary part. More worlds would never have fixed it. If your arm is bent, throwing a million more darts just makes you very confidently wrong. Precise is not the same as correct.

**V051**  So now, every time I change the code, the first thing I do is prove it still converges to the value I actually defined.

**V052**  Mistake number two was even dumber. Halfway through making this video, camman's pale garden short made me check which version of the game my generator was running.  *(pause)*

**V053**  It was 1.21.4. The update right before pale gardens got bigger. So everything I had was for the wrong game. I threw it all away and ran it again on 26.3.

**V054**  Lesson learned: maths can prove your code is right. It can't tell you you're running the wrong version of Minecraft. That one's on you.

**V055**  So now it checks every single block, on the current version, and every number in this video comes with a range that's proven to contain the real answer. The chance that any of them is wrong is one in five hundred thousand. For scale, a naturally pink sheep is about one in six hundred. You are going to see a lot of pink sheep before I'm wrong.

**V056**  The full proof is on GitHub, if you're into that sort of thing. And when two biomes are too close to call, I won't pretend. I'll call it a tie.

## Section 4

**V057**  Okay. The rarest biomes in Minecraft 26.3. Measured as how far you walk from spawn until you actually step on the biome.

**V058**  Number five. Eroded badlands. Seventy thousand blocks. That's three and a half hours of sprinting in a straight line. That's longer than Titanic. This was camman's latest answer, and it's not even top three.

**V059**  Number four. Ice spikes. About seventy-five thousand blocks. Three hours forty of holding W.

**V060**  Number three. Stony peaks. Eighty-four thousand blocks, over four hours. It's a grey mountain. That's it. That's the biome. Four hours.

**V061**  Number two. Windswept gravelly hills. Ninety-five thousand blocks, almost five hours. It's the smallest biome in the game by area, and I promise you've never once said its name out loud.

**V062**  And if you're wondering where pale garden went: on the old version it was number two. Then the update made it bigger, and it fell all the way to six. Bro fell off.

**V063**  And number one.  *(pause)*

**V064**  Mushroom fields. A hundred and fifty thousand blocks. That's seven and a half hours of sprinting in a straight line from spawn. A full school day of holding W. Even on an elytra spamming rockets, it's still about an hour and a quarter. It's more than one and a half times further than anything else on this list.

**V065**  They're huge once you find one. There are just barely any of them, and they hide way out in the middle of the ocean.

**V066**  And remember the biome spawn pushes away? It's this one. You almost never spawn on mushroom fields. A seed that does is a legendary seed-hunting find. Within 512 blocks of spawn they're about a third as likely as anywhere else, at best. It doesn't change the ranking though, because that push fades after two thousand blocks, and you've still got a hundred and forty-eight thousand to go.

**V067**  And this order is proven. One through seven, locked in: pale garden sixth, mangrove swamp seventh. The first tie doesn't show up until number eight.

**V068**  But here's the thing. You don't walk around with your eyes closed.

## Section 4b

**V069**  Remember the 8 and 32 chunk versions I promised? Same worlds, same walks, but now a biome counts the moment it's within 8 chunks of you. Then 32.

**V070**  Seeing further helps small patches the most. A tiny patch is hard to step on but easy to spot from 500 blocks away. A big blob was never hard to hit in the first place.

**V071**  Mushroom fields does not care. Number one at every distance, alone, proven. Over three and a half hours of sprinting at 8 chunks, an hour and a half at 32. You can't see something that isn't there.

**V072**  Everything below it, though, falls apart. At 8 chunks, windswept gravelly hills, eroded badlands, ice spikes, mangrove, wooded badlands and stony peaks all land somewhere between two and seven, and they're too close to call. Six-way tie for second. Everybody gets a participation trophy.

**V073**  Pale garden just keeps falling. Sixth if you have to step on it, eight to eleven at 8 chunks, and twelve to sixteen at 32. Its patches are tiny, so they're hard to step on but really easy to spot.

**V074**  At 32 chunks, eroded badlands climbs to a proven second. About an hour and ten minutes. It's the reverse of pale garden: big patches, but so few and so far apart that seeing further helps everything else more. And it drags the whole badlands family up with it. Wooded badlands goes to three to six, plain badlands to four to eight.

**V075**  And look at that: eroded badlands near the top. That's starting to look like camman's distance ranking. The further you can see, the closer you get to his answer. But even at 32 chunks, mushroom fields stays ahead, and that gap is proven.

**V076**  So which ranking is "the" answer? Depends how far you can see. But the one thing every version agrees on is number one.

## Section 4c

**V077**  So, does this ranking actually make sense? Let's go through it.

**V078**  Mushroom fields at number one doesn't surprise anyone. It's rare by area, sure. But it's also biased by spawn, and it's biased away. You basically never spawn next to one.

**V079**  Not once in two hundred and fifteen thousand worlds. That push probably makes the walk a tiny bit longer, my best guess is about 786 blocks, so half a percent. Too small to prove, and it's not why mushroom wins anyway. It wins because there's barely any of it, and what there is lives in the middle of the ocean.

**V080**  Two to five make total sense. Those are all very rare, very niche, very small biomes.

**V081**  Seven, though. Mangrove swamp. That one surprised me. I feel like I stumble into mangroves all the time. But maybe that's because they're big and rare, so when you do find one, it's a LOT of mangrove. Or maybe my last SMP just spawned next to one and I'm biased. It's also just a really unique biome. You remember every mangrove you've ever been in. Unlike half of this list, which is just "plains" to me.

**V082**  Eleven to nineteen, nothing too surprising. Except windswept hills, sixteen to eighteen. That's low. But again, that's a memory thing. Literally nobody remembers what a windswept hills looks like. But everyone notices a cherry grove. So when people vote windswept hills as rarer, they're voting for "niche", not "rare".

**V083**  The middle, nothing crazy. What did surprise me is that both old growth taigas and sparse jungle are way down here. Old growth spruce and pine taiga at around twenty-three to twenty-six, sparse jungle at thirty-six to thirty-seven. Niche, not rare. Same story.

**V084**  From about forty-eight onward, it's the common stuff. Ocean being common? Yeah. Correct. Thank you.

**V085**  Deep dark being this common is insane though. Number fifty. About three thousand blocks. Three thousand! But I guess it makes sense. It's a cave biome, it's under basically every tall mountain. Which honestly means maybe caves need their own definition of rare, one that counts whether you can actually get to them.

**V086**  Or maybe it's that the ancient city is what's rare. Not the deep dark. My brain just glued the two together. And now that I think about it, I do see deep dark everywhere. Same with the other caves. There's way less variety underground, so caves got a massive boost from the 3D biome system.

**V087**  Plains and forest being the most common makes sense.

**V088**  Except. They're not the most common.  *(pause)*

**V089**  River is. About seven hundred and sixty blocks on average. And that's weird, because by area, river is smaller than plains or forest. My first guess was spawn. Maybe the game just loves putting you near rivers? Nope, it's the opposite. You spawn right in plains and forest all the time, and you never spawn in a river. Spawn is literally helping the other two. And river STILL wins, seven sixty against over a thousand. So it's the shape. Rivers are long thin lines cutting through everything, so any straight walk crosses one almost immediately. River is the ultimate line catcher.

**V090**  So, camman. By area, we agree. Windswept gravelly hills covers the least of the world in my numbers too, about 0.07 percent. And on distance, you were right that how a biome is spread out changes everything. Where we split is the top. With a blind walk and a proof, mushroom fields is number one, and it's not close.

**V091**  The REAL, real, real, real rarest biome. You're welcome.

## Section 5

**V092**  So. The rarest biome in Minecraft 26.3 is mushroom fields. Seven and a half hours of sprinting from spawn if you have to step on it, and still number one no matter how far you can see.

**V093**  A few honest limits, quickly. This is Java 26.3. The walk is a straight line from spawn, over land and water, so it's distance, not time. Nobody is actually sprinting across the ocean for seven hours. And "found" means the biome is there, not that you actually looked at it.

**V094**  All the code is open source, and so is the maths. If you think I got something wrong, go check. I've already found two of my own mistakes, so honestly, it's a fair request.  *(pause)*

**V095**  See you in the next one. Hopefully closer to spawn.
