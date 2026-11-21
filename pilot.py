import numpy as np, rarity as ry
R=20000.0
D=ry.load_first("out/pilot_first.csv",300,8)
c0c1=4.3/4.6
rows=[]
for b,d in D.items():
    hit=np.isfinite(d).mean()
    x=np.minimum(d,R)
    vs,vw=ry.variance_components(x)
    rows.append((hit,b,vs,vw))
rows.sort(reverse=True)
print("biome hit%  sd_seed  sd_ray  K*")
for hit,b,vs,vw in rows:
    if 0.02<hit<0.99:
        print(f"{b:4d} {hit*100:5.1f} {vs**.5:8.0f} {vw**.5:8.0f}  {ry.k_star(c0c1,1,vw,vs):5.1f}")
