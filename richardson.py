import numpy as np, rarity as ry
R=20000.0; R0=4000.0; NS=800
names={int(a):b for a,b in (l.strip().split(",",1) for l in open("out/names.csv"))}
H=[1,2,4,8,16,32]
D={h:ry.load_first(f"out/h/s{h}.csv",NS,4) for h in H}
bios=sorted(set().union(*[d.keys() for d in D.values()]))
def tot(d):
    at=d>=R0
    return ((d<=R)&at).sum(1).astype(float), np.where(at,np.minimum(d,R)-R0,0).sum(1)
rng=np.random.default_rng(1); idx=rng.integers(0,NS,(2000,NS))
def M(e,x,ix=None):
    return (x.sum()/e.sum()) if ix is None else (x[ix].sum(1)/np.maximum(e[ix].sum(1),1))
res={k:[] for k in ["raw4","raw8","raw16","rich(4,8)","rich(8,16)","rich(16,32)"]}
sig={k:0 for k in res}; n=0; worst={k:(0,"") for k in res}
for b in bios:
    nm=names.get(b,str(b))
    t={h:tot(D[h].get(b,np.full((NS,4),np.inf))) for h in H}
    if t[1][0].sum()<300: continue
    n+=1
    ref=M(*t[1]); refb=M(*t[1],idx)
    est={"raw4":(lambda m:m[4]),"raw8":(lambda m:m[8]),"raw16":(lambda m:m[16]),
         "rich(4,8)":(lambda m:2*m[4]-m[8]),"rich(8,16)":(lambda m:2*m[8]-m[16]),"rich(16,32)":(lambda m:2*m[16]-m[32])}
    m0={h:M(*t[h]) for h in H}; mb={h:M(*t[h],idx) for h in H}
    for k,f in est.items():
        rel=f(m0)/ref-1; relb=f(mb)/refb-1
        lo,hi=np.quantile(relb,[0.025,0.975])
        res[k].append(abs(rel)); sig[k]+= (lo>0 or hi<0)
        if abs(rel)>worst[k][0]: worst[k]=(abs(rel),nm)
print(f"{n} biomes with >=300 events at h=1. error of each estimator relative to the h=1 value")
print(f"{'estimator':14s} median|err|  max|err|  worst biome            #significant")
for k in res: print(f"{k:14s} {np.median(res[k])*100:8.2f}%  {max(res[k])*100:7.2f}%  {worst[k][1]:22s} {sig[k]}/{n}")
