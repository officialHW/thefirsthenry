import sys, heapq, numpy as np
sys.path.insert(0, sys.argv[2]); import glbio
def weld(P, I, tol=1e-4):
    key = np.round(P/tol).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    return P[first], inv[I], inv, first
def graph(n, T, V):
    E = np.vstack([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]); E = E[E[:,0]!=E[:,1]]
    E = np.unique(np.sort(E,axis=1),axis=0); L = np.linalg.norm(V[E[:,0]]-V[E[:,1]],axis=1)
    adj = [[] for _ in range(n)]
    for (a,b),l in zip(E,L): adj[a].append((b,l)); adj[b].append((a,l))
    return adj, E, L
def dijkstra(adj, seeds, n):
    D = np.full(n, np.inf); h=[]
    for s in seeds: D[s]=0; h.append((0.0,int(s)))
    heapq.heapify(h)
    while h:
        d,u = heapq.heappop(h)
        if d>D[u]: continue
        for v,l in adj[u]:
            nd=d+l
            if nd<D[v]: D[v]=nd; heapq.heappush(h,(nd,v))
    return D
if __name__ == "__main__":
    j,b = glbio.load(sys.argv[1]); p=j["meshes"][0]["primitives"][0]
    P = glbio.acc(j,b,p["attributes"]["POSITION"]).astype(float); I = glbio.acc(j,b,p["indices"]).reshape(-1,3).astype(np.int64)
    V,T,inv,first = weld(P,I); n=len(V); print("welded", n)
    adj,E,L = graph(n,T,V)
    # components
    comp = np.full(n,-1); c=0
    for s in range(n):
        if comp[s]>=0: continue
        st=[s]; comp[s]=c
        while st:
            u=st.pop()
            for v,_ in adj[u]:
                if comp[v]<0: comp[v]=c; st.append(v)
        c+=1
    sizes = np.bincount(comp); print("components", c, sorted(sizes)[::-1][:8])
    for name, m in [("Lhand", (V[:,0]>0.3)&(V[:,1]<-0.74)&(V[:,1]>-0.84)), ("Rhand",(V[:,0]<-0.28)&(V[:,1]<-0.74)&(V[:,1]>-0.84)), ("Lfoot",(V[:,0]>0.05)&(V[:,1]<-0.9)), ("Rfoot",(V[:,0]<-0.03)&(V[:,1]<-0.9))]:
        seeds = np.where(m)[0]; D = dijkstra(adj, seeds, n); print(name, "seeds", len(seeds), "comp", np.unique(comp[seeds]))
        for d0 in np.arange(0,0.9,0.06):
            mm=(D>=d0)&(D<d0+0.06)
            if mm.sum(): 
                q=V[mm]; print(f"  d {d0:.2f} n={mm.sum():4d} x[{q[:,0].min():+.2f},{q[:,0].max():+.2f}] y[{q[:,1].min():+.2f},{q[:,1].max():+.2f}] z[{q[:,2].min():+.2f},{q[:,2].max():+.2f}]")
