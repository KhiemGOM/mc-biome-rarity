import json, numpy as np, rarity as ry
R=20000.0
names={int(a):b for a,b in (l.strip().split(",",1) for l in open("out/names.csv"))}
inv={v:k for k,v in names.items()}
Ds=[ry.load_first(f"out/main{i}_first.csv",10000,4) for i in (1,2)]
D={b:np.vstack([d.get(b,np.full((10000,4),np.inf)) for d in Ds]) for b in set().union(*[d.keys() for d in Ds])}
res=json.load(open("out/results.json"))
under={"deep_dark","lush_caves","dripstone_caves"}
surf=[r for r in res if r["name"] not in under]
out={"ranking":surf[:12],"n_seeds":20000,"rays":4,"R":R}
# survival curves
grid=np.arange(0,R+1,250.0)
curves={}
for n in ["plains","forest","desert","jungle","snowy_plains","ice_spikes","mushroom_fields"]:
    curves[n]=ry.survival(D[inv[n]].ravel(),grid).tolist()
out["grid"]=grid.tolist(); out["curves"]=curves
# hazard
edges=np.arange(0,R+1,2000.0)
haz={}
for n in ["plains","desert","snowy_plains","ice_spikes","mushroom_fields"]:
    mid,h=ry.hazard(D[inv[n]].ravel(),R,edges)
    haz[n]=[None if not np.isfinite(x) else float(x) for x in h]
out["haz_mid"]=mid.tolist(); out["hazard"]=haz
# far ratio
far=[ry.load_far(f"out/main{i}_far.csv") for i in (1,2)]
rat={}
rr={r["name"]:r for r in res}
for n in ["desert","snowy_plains","jungle","ice_spikes","mushroom_fields","plains"]:
    b=inv[n]; m,h=ry.hazard(D[b].ravel(),R,np.array([10000.,15000.,20000.]))
    rat[n]=dict(hazard=float(np.nanmean(h)),inv_ell=1/rr[n]["ell"],ratio=float(np.nanmean(h)*rr[n]["ell"]),ell=rr[n]["ell"])
out["far_ratio"]=rat
# variance components over biomes with 5%<hit<95% (surface only)
vs,vw=[],[]
for r in surf:
    if 0.05<r["hit"]<0.95:
        a,b_=ry.variance_components(np.minimum(D[r["biome"]],R)); vs.append(a); vw.append(b_)
vs,vw=np.array(vs),np.array(vw)
ks=[ry.k_star(4.3,4.6,w,s) for s,w in zip(vs,vw)]
out["varcomp"]=dict(med_sd_seed=float(np.median(vs**.5)),med_sd_ray=float(np.median(vw**.5)),
    ratio=float(np.median((vw/np.maximum(vs,1e-9))**.5)),kstar_median=float(np.median(ks)),n_biomes=len(vs))
# convergence (subset RMS error vs N) for two biomes
rng=np.random.default_rng(1)
conv={}
Ns=[50,100,200,500,1000,2000,5000]
for n in ["mushroom_fields","desert"]:
    m=np.minimum(D[inv[n]],R).mean(axis=1); full=m.mean()
    rms=[]
    for N in Ns:
        est=[m[rng.choice(m.size,N,replace=False)].mean() for _ in range(400)]
        rms.append(float(np.sqrt(np.mean((np.array(est)-full)**2))))
    sl=np.polyfit(np.log(Ns),np.log(rms),1)[0]
    conv[n]=dict(N=Ns,rms=rms,slope=float(sl),full=float(full),sd=float(m.std()))
out["conv"]=conv
out["hoeffding"]=dict(n_100=ry.hoeffding_n(R,100,0.05),n_25=ry.hoeffding_n(R,25,0.05))
json.dump(out,open("out/video_data.json","w"),indent=1)
print(json.dumps({k:out[k] for k in ["varcomp","far_ratio","hoeffding"]},indent=1))
for n,c in conv.items(): print(n,"slope",round(c["slope"],3),"rms",[round(x) for x in c["rms"]],"sd",round(c["sd"]))
print("hazard desert",[None if x is None else f"{x:.1e}" for x in haz["desert"]])
print("hazard mushroom",[None if x is None else f"{x:.1e}" for x in haz["mushroom_fields"]])
print("hazard plains",[None if x is None else f"{x:.1e}" for x in haz["plains"]])
print([ (r['name'],round(r['rmean']),round(r['hit']*100,1)) for r in out["ranking"]])
