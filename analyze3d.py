import json, numpy as np, rarity as ry
R=20000.0; R0=4000.0; ZONE=2000.0
names={int(a):b for a,b in (l.strip().split(",",1) for l in open("out/names.csv"))}
old={r["name"]:r for r in json.load(open("out/lam.json"))}
oldres={r["name"]:r for r in json.load(open("out/results.json"))}
rng=np.random.default_rng(5)
def load(kind):
    Ds=[ry.load_first(f"out/c/{kind}{i}.csv",2000,4) for i in (1,2)]
    bs=set().union(*[d.keys() for d in Ds])
    return {b:np.vstack([d.get(b,np.full((2000,4),np.inf)) for d in Ds]) for b in bs}
def stat(d):
    at=d>=R0
    ev=((d<=R)&at).sum(1).astype(float); ex=np.where(at,np.minimum(d,R)-R0,0).sum(1)
    en=(d<ZONE).sum(1).astype(float); xn=np.minimum(d,ZONE).sum(1)
    N=d.shape[0]; idx=rng.integers(0,N,(1000,N))
    L=ev.sum()/ex.sum(); lf=ev[idx].sum(1)/np.maximum(ex[idx].sum(1),1e-9)
    M=1/L if L>0 else np.inf
    lo=1/np.quantile(lf,0.975) if np.quantile(lf,0.975)>0 else np.inf
    hi=1/np.quantile(lf,0.025) if np.quantile(lf,0.025)>0 else np.inf
    return dict(M=M,lo=lo,hi=hi,spawn=(en.sum()/xn.sum())/L if L>0 else np.nan,events=int(ev.sum()),hit=float(np.isfinite(d).mean()),
                at4000=float(np.isfinite(d).mean()))
res={}
for kind,label in (("s","surface (depth-0 layer)"),("c","column (any y)")):
    D=load(kind); res[kind]={names.get(b,str(b)):stat(d) for b,d in D.items()}
json.dump(res,open("out/res3d.json","w"),indent=1,default=float)
def row(n,r): return f"{n:26s} M={r['M']:9.0f} [{r['lo']:8.0f},{r['hi']:8.0f}] hit={r['hit']*100:5.1f}% events={r['events']}"
print("== CAVE BIOMES, column mode vs old y=63 ==")
for n in ("lush_caves","dripstone_caves","deep_dark"):
    r=res["c"][n]; o=oldres[n]
    print(row(n,r),f"| old y=63 hit={o['hit']*100:.1f}%")
print("\n== SURFACE mode (depth-0 layer), rarest 14, with old y=63 mean walk ==")
under={"deep_dark","lush_caves","dripstone_caves"}
rows=sorted([(n,r) for n,r in res["s"].items() if n not in under and r["events"]>=15],key=lambda t:-t[1]["M"])
for n,r in rows[:14]:
    o=old.get(n); print(row(n,r),f"| old M={o['M']:.0f}" if o else "| (not in old)")
print("\n== COLUMN mode rarest 10 ==")
rows=sorted([(n,r) for n,r in res["c"].items() if r["events"]>=15],key=lambda t:-t[1]["M"])
for n,r in rows[:10]: print(row(n,r))
print("\nnever seen in surface mode but in old y=63:",[n for n in old if n not in res["s"]][:10])
print("new in surface mode not in old:",[n for n in res["s"] if n not in old and n not in under][:10])
