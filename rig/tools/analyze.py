import sys, numpy as np
sys.path.insert(0, sys.argv[2]); import glbio
j, b = glbio.load(sys.argv[1]); p = j["meshes"][0]["primitives"][0]
P = glbio.acc(j,b,p["attributes"]["POSITION"]).astype(float); I = glbio.acc(j,b,p["indices"]).reshape(-1,3)
print("nodes", j["nodes"], "verts", len(P), "tris", len(I))
def clusters(v, gap=0.03):
    v = np.sort(v); out=[]; s=v[0]; prev=v[0]
    for x in v[1:]:
        if x-prev>gap: out.append((round(s,3),round(prev,3))); s=x
        prev=x
    out.append((round(s,3),round(prev,3))); return out
for y0 in np.arange(-0.95, 0.0, 0.05):
    m = (P[:,1]>=y0)&(P[:,1]<y0+0.05)
    if m.sum()==0: continue
    print(f"y {y0:+.2f}  n={m.sum():4d}  x:{clusters(P[m,0])}  z:[{P[m,2].min():+.2f},{P[m,2].max():+.2f}]")
