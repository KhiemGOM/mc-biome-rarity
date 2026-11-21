import numpy as np, rarity as ry, math
R=20000.0; R0=4000.0
names={int(a):b for a,b in (l.strip().split(",",1) for l in open("out/names.csv"))}
inv={v:k for k,v in names.items()}
Ds=[ry.load_first(f"out/main{i}_first.csv",10000,4) for i in (1,2)]
rng=np.random.default_rng(2)
NS=20000; NR=NS*4
idx=rng.integers(0,NS,(1000,NS))
def tot(d):
    at=d>=R0
    return ((d<=R)&at).sum(1).astype(float), np.where(at,np.minimum(d,R)-R0,0).sum(1)
sel=["desert","jungle","ice_spikes","cherry_grove","stony_peaks","windswept_gravelly_hills","pale_garden","mushroom_fields"]
rows=[]
print(f"{'biome':26s} events  ev/ray   SE_boot  1.96/sqrt(E)  DEFF")
for n in sel:
    b=inv[n]; d=np.vstack([x[b] for x in Ds])
    e,x=tot(d); E=e.sum(); M=x.sum()/E
    boot=x[idx].sum(1)/np.maximum(e[idx].sum(1),1)
    se=boot.std()/M; pois=1/math.sqrt(E)
    deff=(se/pois)**2
    rows.append((n,E/NR,deff,M))
    print(f"{n:26s} {int(E):6d}  {E/NR:7.4f}  {se*100:6.2f}%   {1.96*pois*100:6.2f}%     {deff:4.2f}")
# Richardson variance inflation from the paired h-study
NS2=800
H={h:ry.load_first(f"out/h/s{h}.csv",NS2,4) for h in (8,16)}
idx2=rng.integers(0,NS2,(2000,NS2)); infl=[]
for n in sel:
    b=inv[n]
    t={h:tot(H[h].get(b,np.full((NS2,4),np.inf))) for h in (8,16)}
    if t[8][0].sum()<100: continue
    Mb=lambda h:t[h][1][idx2].sum(1)/np.maximum(t[h][0][idx2].sum(1),1)
    infl.append((n,(2*Mb(8)-Mb(16)).std()/Mb(8).std()))
print("SE inflation of rich(8,16) vs plain h=8:",[(n,round(v,2)) for n,v in infl])
INFL=max(v for n,v in infl)
# cost per ray, measured: setup 4.3 ms per seed (4 rays), 3.6 us per lookup
cost_ray=(R/8+R/16)*3.6e-6+4.3e-3/4
print(f"\nmeasured cost per ray with Richardson (h=8 and h=16): {cost_ray*1000:.1f} ms CPU; plain h=16: {(R/16*3.6e-6+4.3e-3/4)*1000:.1f} ms")
print(f"\nrays needed for 95 pct half-width eps on the mean walk (noise only, Richardson SE inflation x{INFL:.2f} included), wall time on 2 cores")
print(f"{'biome':26s} " + "".join(f"{'eps=%d%%'%int(e*100):>22s}" for e in (0.10,0.05,0.02,0.01)))
for n,er,deff,M in rows:
    s=f"{n:26s} "
    for eps in (0.10,0.05,0.02,0.01):
        E_need=deff*INFL**2*(1.96/eps)**2; nr=E_need/er
        s+=f"{nr/1e3:9.0f}k rays {nr*cost_ray/2/60:7.1f} min"
    print(s)
