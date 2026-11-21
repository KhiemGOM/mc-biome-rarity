import json, numpy as np, rarity as ry
R=20000.0; R0=4000.0; NS=800
names={int(a):b for a,b in (l.strip().split(",",1) for l in open("out/names.csv"))}
H=[1,2,4,8,16,32,64]
D={h:ry.load_first(f"out/h/s{h}.csv",NS,4) for h in H}
bios=sorted(set().union(*[d.keys() for d in D.values()]))
def tot(d):
    at=d>=R0
    return ((d<=R)&at).sum(1).astype(float), np.where(at,np.minimum(d,R)-R0,0).sum(1)
rng=np.random.default_rng(0); idx=rng.integers(0,NS,(2000,NS))
rows={}
for b in bios:
    nm=names.get(b,str(b))
    tt={h:tot(D[h].get(b,np.full((NS,4),np.inf))) for h in H}
    ref=tt[1]
    if ref[0].sum()<30: continue
    M1=ref[1].sum()/ref[0].sum()
    r={"M1":M1,"events":int(ref[0].sum()),"hit1":float(np.isfinite(D[1][b]).mean())}
    for h in H[1:]:
        e,x=tt[h]
        Mh=x.sum()/max(e.sum(),1)
        boot=(x[idx].sum(1)/np.maximum(e[idx].sum(1),1))/(ref[1][idx].sum(1)/ref[0][idx].sum(1))-1
        r[h]=(Mh/M1-1,np.quantile(boot,0.025),np.quantile(boot,0.975))
        # pathwise: fraction of rays whose first hit moved
        a=D[1][b]; c=D[h].get(b,np.full((NS,4),np.inf))
        r[f"moved{h}"]=float(np.mean(a!=c)); r[f"hitdrop{h}"]=float(np.isfinite(a).mean()-np.isfinite(c).mean())
    rows[nm]=r
json.dump(rows,open("out/stepbias.json","w"),indent=1,default=float)
show=["mushroom_fields","pale_garden","windswept_gravelly_hills","stony_peaks","ice_spikes","mangrove_swamp","cherry_grove","meadow","river","beach","stony_shore","frozen_river","plains","forest","desert","jungle","swamp","birch_forest"]
print("rel. change of mean walk vs h=1 (paired 95% CI); events at h=1")
print(f"{'biome':24s} ev    h=4              h=8              h=16             h=32             h=64")
for n in show:
    if n not in rows: print(n,"(too few events)"); continue
    r=rows[n]; s=f"{n:24s} {r['events']:5d}"
    for h in (4,8,16,32,64): s+=f" {r[h][0]*100:+6.1f}%[{r[h][1]*100:+5.1f},{r[h][2]*100:+5.1f}]"
    print(s)
allb=[(n,r) for n,r in rows.items() if r["events"]>=300]
for h in (16,32,64):
    worst=max(allb,key=lambda t:abs(t[1][h][0]))
    sig=[n for n,r in allb if r[h][1]>0 or r[h][2]<0]
    print(f"h={h}: biomes with events>=300: {len(allb)}; worst |bias| {abs(worst[1][h][0])*100:.1f}% ({worst[0]}); significantly nonzero: {len(sig)}; median |bias| {np.median([abs(r[h][0]) for n,r in allb])*100:.2f}%")
