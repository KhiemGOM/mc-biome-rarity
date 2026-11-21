import numpy as np, rarity as ry
from math import sqrt
from scipy import stats
NS=3000; RMAX=100000.0
names={int(a):b for a,b in (l.strip().split(",",1) for l in open("out/names.csv"))}
inv={v:k for k,v in names.items()}
D=ry.load_first("out/L/s.csv",NS,4)
edges=[4000,8000,16000,32000,64000,100000]
rng=np.random.default_rng(3)
def bin_stats(d):
    out=[]
    for a,b in zip(edges[:-1],edges[1:]):
        at=d>=a
        ev=(at&(d<b)).sum(1).astype(float); ex=np.where(at,np.minimum(d,b)-a,0).sum(1)
        out.append((ev,ex))
    return out
show=["plains","forest","desert","jungle","snowy_plains","ice_spikes","mangrove_swamp","cherry_grove","stony_peaks","windswept_gravelly_hills","pale_garden","mushroom_fields"]
print("hazard per bin, in units of 1e-5 per block; 95% CI from cluster bootstrap; last col = test that all bins share one rate")
print(f"{'biome':24s} " + " ".join(f"{a//1000}-{b//1000}k".rjust(15) for a,b in zip(edges[:-1],edges[1:])) + "   p(flat)")
idx=rng.integers(0,NS,(1000,NS))
for n in show:
    d=D[inv[n]]; bs=bin_stats(d)
    cells=[]; ev_tot=[]; ex_tot=[]
    for ev,ex in bs:
        lam=ev.sum()/ex.sum() if ex.sum()>0 else np.nan
        boot=ev[idx].sum(1)/np.maximum(ex[idx].sum(1),1e-9)
        lo,hi=np.quantile(boot,[0.025,0.975])
        cells.append(f"{lam*1e5:5.2f}[{lo*1e5:4.2f},{hi*1e5:4.2f}]"); ev_tot.append(ev.sum()); ex_tot.append(ex.sum())
    ev_tot=np.array(ev_tot); ex_tot=np.array(ex_tot)
    lam0=ev_tot.sum()/ex_tot.sum(); expct=lam0*ex_tot
    # likelihood-ratio test of constant hazard (Poisson), 4 df  (ignores seed clustering, so slightly optimistic)
    ok=expct>0
    G=2*np.sum(np.where(ev_tot[ok]>0,ev_tot[ok]*np.log(ev_tot[ok]/expct[ok]),0)-(ev_tot[ok]-expct[ok]))
    p=1-stats.chi2.cdf(G,ok.sum()-1)
    print(f"{n:24s} "+" ".join(c.rjust(15) for c in cells)+f"   {p:6.3f}")
