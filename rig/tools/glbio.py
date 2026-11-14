import json, struct, numpy as np
CT = {5120:np.int8,5121:np.uint8,5122:np.int16,5123:np.uint16,5125:np.uint32,5126:np.float32}
NC = {"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT4":16}
def load(path):
    b = open(path,'rb').read()
    clen = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20+clen]); off = 20+clen
    blen = struct.unpack('<I', b[off:off+4])[0]; bin_ = b[off+8:off+8+blen]
    return j, bin_
def acc(j, bin_, i):
    a = j["accessors"][i]; bv = j["bufferViews"][a["bufferView"]]
    dt = CT[a["componentType"]]; n = NC[a["type"]]
    o = bv.get("byteOffset",0)+a.get("byteOffset",0)
    stride = bv.get("byteStride")
    if stride and stride != np.dtype(dt).itemsize*n:
        raw = np.frombuffer(bin_, np.uint8, count=stride*a["count"], offset=o).reshape(a["count"], stride)[:, :np.dtype(dt).itemsize*n]
        return np.frombuffer(raw.tobytes(), dt).reshape(a["count"], n)
    return np.frombuffer(bin_, dt, count=a["count"]*n, offset=o).reshape(a["count"], n)
