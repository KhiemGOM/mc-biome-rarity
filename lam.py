import json, numpy as np, rarity as ry
R=20000.0; R0=4000.0; ZONE=2000.0
names={int(a):b for a,b in (l.strip().split(",",1) for l in open("out/names.csv"))}
Ds=[ry.load_first(f"out/main{i}_first.csv",10000,4) for i in (1,2)]
D={b:np.vstack([d.get(b,np.full((10000,4),np.inf)) for d in Ds]) for b in set().union(*[d.keys() for d in Ds])}
under={"deep_dark","lush_caves","dripstone_caves"}
rng=np.random.default_rng(7)
def lam_far(d):
    atrisk=d>=R0
    ev=((d<=R)&atrisk).astype(float); ex=np.where(atrisk,np.minimum(d,R)-R0,0.0)
    return ev.sum(axis=1),ex.sum(axis=1)
def lam_near(d):
    ev=(d<ZONE).astype(float); ex=np.minimum(d,ZONE)
    return ev.sum(axis=1),ex.sum(axis=1)
rows=[]
for b,d in D.items():
    nm=names.get(b,str(b))
    if nm in under: continue
    ef,xf=lam_far(d); en,xn=lam_near(d)
    if ef.sum()<30: continue
    N=d.shape[0]
    idx=rng.integers(0,N,(1000,N))
    lf=ef[idx].sum(1)/xf[idx].sum(1); ln=en[idx].sum(1)/np.maximum(xn[idx].sum(1),1e-9)
    L=ef.sum()/xf.sum(); Ln=en.sum()/xn.sum()
    M=1/L; Mlo,Mhi=1/np.quantile(lf,0.975),1/np.quantile(lf,0.025)
    sf=Ln/L; sflo,sfhi=np.quantile(ln/lf,[0.025,0.975])
    rows.append(dict(name=nm,biome=b,M=M,M_lo=float(Mlo),M_hi=float(Mhi),spawn=sf,spawn_lo=float(sflo),spawn_hi=float(sfhi),events=int(ef.sum())))
rows.sort(key=lambda r:-r["M"])
json.dump(rows,open("out/lam.json","w"),indent=1)
print(f"{'biome':26s} meanwalk[95%CI]            spawn factor [CI]")
for r in rows[:14]+[x for x in rows if x['name'] in('desert','snowy_plains','jungle','plains','forest','ocean')]:
    print(f"{r['name']:26s} {r['M']:8.0f} [{r['M_lo']:7.0f},{r['M_hi']:7.0f}]  {r['spawn']:5.2f} [{r['spawn_lo']:4.2f},{r['spawn_hi']:4.2f}]")
