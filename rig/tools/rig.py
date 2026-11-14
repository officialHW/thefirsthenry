# Adds a skeleton and skin weights to the static Meshy model (no accounts, no cost).
# usage: python3 -I rig.py in.glb out.glb toolsdir
import sys, json, struct, numpy as np
sys.path.insert(0, sys.argv[3]); import glbio, geo
import scipy.sparse as sp, scipy.sparse.linalg as spl
j, b = glbio.load(sys.argv[1]); prim = j["meshes"][0]["primitives"][0]
P = glbio.acc(j,b,prim["attributes"]["POSITION"]).astype(float); I = glbio.acc(j,b,prim["indices"]).reshape(-1,3).astype(np.int64)
V, T, inv, first = geo.weld(P, I); n = len(V); adj, E, L = geo.graph(n, T, V)
x, y, z = V[:,0], V[:,1], V[:,2]
dL = geo.dijkstra(adj, np.where((x>0.3)&(y<-0.74)&(y>-0.84))[0], n)
dR = geo.dijkstra(adj, np.where((x<-0.28)&(y<-0.74)&(y>-0.84))[0], n)
fL = geo.dijkstra(adj, np.where((x>0.05)&(y<-0.9))[0], n)
fR = geo.dijkstra(adj, np.where((x<-0.03)&(y<-0.9))[0], n)
cen = lambda m: V[m].mean(axis=0)
band = lambda D, a, w=0.025: (D>a-w)&(D<a+w)
limb = (dL<0.42)|(dR<0.42)|(fL<0.30)|(fR<0.30)
core = ~limb & (z<0.17)
# ---- joints (model units: +Y up, +Z is his front, +X is his left) ----
J = {}
J["Hips"] = np.array([0, -0.60, cen(core&(y<-0.52))[2]])
for k,yy in [("Spine",-0.54),("Spine1",-0.49),("Spine2",-0.45),("Neck",-0.39),("Head",-0.30)]: J[k] = np.array([0, yy, J["Hips"][2]])
J["Jaw"] = np.array([0, -0.10, 0.10])
for S, D, F in [("Left", dL, fL), ("Right", dR, fR)]:
    sh = cen(band(D,0.34)); J[S+"Shoulder"] = np.array([sh[0]*0.45, -0.43, sh[2]])
    J[S+"Arm"] = np.array([sh[0], max(sh[1], -0.46), sh[2]]); J[S+"ForeArm"] = cen(band(D,0.185)); J[S+"Hand"] = cen(band(D,0.075))
    kn = cen(band(F,0.175)); an = cen(band(F,0.105))
    J[S+"UpLeg"] = np.array([kn[0], -0.63, kn[2]]); J[S+"Leg"] = kn; J[S+"Foot"] = an; J[S+"ToeBase"] = np.array([an[0], -0.92, an[2]+0.12])
parent = {"Hips":None,"Spine":"Hips","Spine1":"Spine","Spine2":"Spine1","Neck":"Spine2","Head":"Neck","Jaw":"Head"}
for S in ("Left","Right"):
    parent.update({S+"Shoulder":"Spine2",S+"Arm":S+"Shoulder",S+"ForeArm":S+"Arm",S+"Hand":S+"ForeArm",S+"UpLeg":"Hips",S+"Leg":S+"UpLeg",S+"Foot":S+"Leg",S+"ToeBase":S+"Foot"})
names = list(parent.keys()); idx = {k:i for i,k in enumerate(names)}
# ---- seeds: vertices that belong fully to one bone; everything in between is solved smoothly ----
seed = np.full(n, -1)
def put(name, m): seed[m & (seed<0)] = idx[name]
for S, D, F in [("Left", dL, fL), ("Right", dR, fR)]:
    put(S+"Hand", D<0.05); put(S+"ForeArm", (D>0.10)&(D<0.155)); put(S+"Arm", (D>0.215)&(D<0.30))
    put(S+"Foot", F<0.085); put(S+"Leg", (F>0.125)&(F<0.155)); put(S+"UpLeg", (F>0.195)&(F<0.235))
put("Jaw", ~limb & (y<-0.25) & (z>0.30) & (np.abs(x)<0.30))
put("Head", ~limb & ((y>-0.13) | ((z>0.24)&(y>-0.15))))
put("Head", ~limb & (y>-0.30) & (z<0.05))            # back and sides of the skull
put("Hips", core & (y<-0.57) & (y>-0.66) & (fL>0.33) & (fR>0.33))
put("Spine", core & (y>-0.53) & (y<-0.45) & (dL>0.47) & (dR>0.47))
for k in names: print(f"{k:14s} seeds={int((seed==idx[k]).sum()):4d}  at {np.round(J[k],3)}")
# ---- harmonic weights over the surface ----
w = 1.0/np.maximum(L, 1e-5)
A = sp.coo_matrix((np.r_[w,w], (np.r_[E[:,0],E[:,1]], np.r_[E[:,1],E[:,0]])), shape=(n,n)).tocsr()
Lap = sp.diags(np.asarray(A.sum(axis=1)).ravel()) - A
free = np.where(seed<0)[0]; fixed = np.where(seed>=0)[0]
solve = spl.factorized(Lap[free][:,free].tocsc())
W = np.zeros((n, len(names))); W[fixed, seed[fixed]] = 1
B = Lap[free][:,fixed]
for k in range(len(names)):
    if (seed==k).sum()==0: continue
    W[free, k] = solve(-(B @ W[fixed, k]))
W = np.clip(W, 0, 1); W = W**1.6                      # a little sharper at the joints
order = np.argsort(-W, axis=1)[:, :4]; top = np.take_along_axis(W, order, axis=1); top /= top.sum(axis=1, keepdims=True)
JN = order[inv].astype(np.uint8); WT = top[inv].astype(np.float32)
# ---- write the new GLB ----
pos = {}
def world(k): return J[k]
nodes = j["nodes"]; base = len(nodes)
for k in names:
    p = parent[k]; t = J[k] - (J[p] if p else 0)
    nodes.append({"name": "mixamorig" + k, "translation": [float(v) for v in t]})
for k in names:
    if parent[k]: nodes[base+idx[parent[k]]].setdefault("children", []).append(base+idx[k])
ibm = np.tile(np.eye(4, dtype=np.float32), (len(names),1,1))
for k in names: ibm[idx[k]][3,:3] = -J[k]            # column-major: translation sits in the last column
blob = bytearray(b)
def add(arr, ctype, typ, target=None):
    while len(blob) % 4: blob.append(0)
    off = len(blob); blob.extend(arr.tobytes())
    bv = {"buffer":0, "byteOffset":off, "byteLength":arr.nbytes}
    if target: bv["target"] = target
    j["bufferViews"].append(bv)
    j["accessors"].append({"bufferView":len(j["bufferViews"])-1, "componentType":ctype, "count":len(arr), "type":typ})
    return len(j["accessors"])-1
prim["attributes"]["JOINTS_0"] = add(JN, 5121, "VEC4", 34962)
prim["attributes"]["WEIGHTS_0"] = add(WT, 5126, "VEC4", 34962)
j["skins"] = [{"joints":[base+i for i in range(len(names))], "skeleton": base, "inverseBindMatrices": add(ibm.reshape(-1,16), 5126, "MAT4")}]
nodes[0]["skin"] = 0; nodes[0]["name"] = "Henry"
j["scenes"][j.get("scene",0)]["nodes"] = [0, base]
while len(blob) % 4: blob.append(0)
j["buffers"][0]["byteLength"] = len(blob)
js = json.dumps(j, separators=(",",":")).encode(); js += b" " * ((4 - len(js) % 4) % 4)
out = struct.pack("<4sII", b"glTF", 2, 12+8+len(js)+8+len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + bytes(blob)
open(sys.argv[2], "wb").write(out); print("wrote", sys.argv[2], len(out), "bytes;", len(names), "bones")
