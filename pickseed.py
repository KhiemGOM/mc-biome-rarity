import csv, json, numpy as np
names={int(a):b for a,b in (l.strip().split(",",1) for l in open("out/names.csv"))}
inv={v:k for k,v in names.items()}
want=["mushroom_fields","desert","ice_spikes","jungle","snowy_plains"]
byseed={}
for r in csv.DictReader(open("out/main1_first.csv")):
    b=int(r["biome"])
    if names.get(b) in want:
        byseed.setdefault(int(r["seed"]),[]).append((names[b],int(r["ray"]),float(r["angle"]),int(r["dist"])))
best=None
for s,v in byseed.items():
    m=[x for x in v if x[0]=="mushroom_fields" and 5000<=x[3]<=9000]
    others={x[0] for x in v if x[3]<=9000}
    if m and len(others)>=4:
        best=(s,v); break
print(best[0]); 
for x in sorted(best[1],key=lambda t:(t[1],t[3])): print(x)
json.dump(dict(seed=best[0]),open("out/mapseed.json","w"))
