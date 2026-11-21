import csv, json, numpy as np, rarity as ry
R=20000.0; STEP=16
names={int(a):b for a,b in (l.strip().split(",",1) for l in open("out/names.csv"))}
parts=[(f"out/main{i}_first.csv",f"out/main{i}_far.csv") for i in (1,2)]
Ds=[ry.load_first(p[0],10000,4) for p in parts]
biomes=sorted(set().union(*[d.keys() for d in Ds]))
D={b:np.vstack([d.get(b,np.full((10000,4),np.inf)) for d in Ds]) for b in biomes}
far=[ry.load_far(p[1]) for p in parts]
rng=np.random.default_rng(0)
res=[]
for b in biomes:
    d=D[b]; flat=d.ravel()
    hit=float(np.isfinite(flat).mean())
    rm=ry.restricted_mean(d,R); lo,hi=ry.bootstrap_restricted_mean(d,R,n_boot=2000,rng=rng)
    med=ry.median(flat,R)
    mlo,mhi=(ry.bootstrap_median(d,R,n_boot=300,rng=rng) if np.isfinite(med) or hit>0.3 else (np.inf,np.inf))
    sin=sum(f.get(b,(0,0,0))[0] for f in far); ent=sum(f.get(b,(0,0,0))[1] for f in far)
    tot=sum(next(iter(f.values()))[2] for f in far)
    ell=ry.far_mean_free_path(sin,ent,tot,STEP)
    res.append(dict(biome=b,name=names.get(b,str(b)),hit=hit,rmean=rm,rmean_lo=lo,rmean_hi=hi,
        median=None if not np.isfinite(med) else med,
        med_lo=None if not np.isfinite(mlo) else mlo,med_hi=None if not np.isfinite(mhi) else mhi,
        p=sin/tot,ell=None if not np.isfinite(ell) else ell,far_entries=ent))
res.sort(key=lambda r:-r["rmean"])
json.dump(res,open("out/results.json","w"),indent=1)
print(f"{'biome':26s} hit%   median  restr.mean [95% CI]        p%     ell")
for r in res[:40]:
    m="  >R " if r["median"] is None else f"{r['median']:6.0f}"
    e="  n/a" if r["ell"] is None else f"{r['ell']:6.0f}"
    print(f"{r['name']:26s} {r['hit']*100:5.1f} {m} {r['rmean']:7.0f} [{r['rmean_lo']:6.0f},{r['rmean_hi']:6.0f}] {r['p']*100:6.2f} {e}")
