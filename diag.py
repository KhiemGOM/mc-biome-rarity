import numpy as np, rarity as ry, json
names={int(a):b for a,b in (l.strip().split(",",1) for l in open("out/names.csv"))}
A=ry.load_first("out/s16_first.csv",400,4); B=ry.load_first("out/s4_first.csv",400,4)
print("step diag (R=6000, 400 seeds x 4 rays): hit% at h=16 vs h=4")
out=[]
for b in sorted(B):
    ha=np.isfinite(A.get(b,np.full((1,1),np.inf))).mean() if b in A else 0.0
    hb=np.isfinite(B[b]).mean()
    if hb>0.02: out.append((hb-ha,names[b],ha,hb))
out.sort(reverse=True)
for d,n,ha,hb in out[:10]: print(f"  {n:22s} {ha*100:5.1f} -> {hb*100:5.1f}")
# hazard far-field vs 1/ell
R=20000.0
D=[ry.load_first(f"out/main{i}_first.csv",10000,4) for i in (1,2)]
res={r["name"]:r for r in json.load(open("out/results.json"))}
inv={v:k for k,v in names.items()}
print("far hazard (r in 10000..20000) vs 1/ell")
for n in ["desert","snowy_plains","jungle","ice_spikes","mushroom_fields","plains"]:
    b=inv[n]; d=np.vstack([x[b] for x in D if b in x]+([] if True else []))
    # note: hazard conditions on not hit yet before 10000; fine for rate comparison
    mid,h=ry.hazard(d.ravel(),R,np.array([10000.,15000.,20000.]))
    ell=res[n]["ell"]
    print(f"  {n:16s} hazard={np.nanmean(h):.2e}  1/ell={1/ell:.2e}  ratio={np.nanmean(h)*ell:.2f}")
