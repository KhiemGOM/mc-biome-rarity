import sys, time
from scenes import *
from PIL import Image
which=sys.argv[1:]
t0=time.time()
for nm,fn,secs in STILLS:
    if which and nm not in which: continue
    Image.fromarray(fn()).save(f"prev/{nm}.png"); print(nm, round(time.time()-t0,1))
if not which or "map" in which:
    s=MapScene(); Image.fromarray(s.frame(10.0)).save("prev/map_t10.png"); Image.fromarray(s.frame(15.0)).save("prev/map_t15.png"); print("map",round(time.time()-t0,1))
if not which or "surv" in which:
    s=SurvScene(); Image.fromarray(s.frame(6.0)).save("prev/surv_t6.png"); Image.fromarray(s.frame(16.0)).save("prev/surv_t16.png"); print("surv",round(time.time()-t0,1))
