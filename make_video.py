import os, subprocess, time
from scenes import *
V = D + "v/"
t0 = time.time()
still = {n: (f, s) for n, f, s in STILLS}
order = ["s00_title","s01_two","s02_def","MAP","s04_walk","s05_pipe","SURV","s07_haz","s08_rank","s09_twist",
         "s10a_proof","s10b_conv","s11_rays","s12_trust","s13_cav","s14_out"]
files = []
for n in order:
    out = V + n + ".mp4"
    files.append(out)
    if os.path.exists(out):
        continue
    if n in still:
        f, secs = still[n]
        enc_still(f(), secs, out)
    else:
        sc = MapScene() if n == "MAP" else SurvScene()
        w = AnimWriter(out, sc.secs)
        for i in range(int(sc.secs * FPS)):
            w.write(sc.frame(i / FPS))
        w.close()
    print(n, round(time.time() - t0), flush=True)
with open(V + "list.txt", "w") as f:
    for p in files:
        f.write(f"file '{p}'\n")
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",V+"list.txt","-c","copy",V+"silent.tmp.mp4"],check=True)
subprocess.run(["ffmpeg","-y","-loglevel","error","-i",V+"silent.tmp.mp4","-f","lavfi","-i","anullsrc=r=44100:cl=stereo",
                "-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-shortest","-movflags","+faststart",D+"minecraft_biome_rarity.tmp.mp4"],check=True)
os.rename(D+"minecraft_biome_rarity.tmp.mp4", D+"minecraft_biome_rarity.mp4")
print("done", round(time.time() - t0))
