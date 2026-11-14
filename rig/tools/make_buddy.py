"""Builds "Buddy": a simple cartoon stand-in body with the same 23-bone skeleton as Henry.

It lets the starter kit work before you have made your own 3D model. Every mood, wave,
walk and jaw movement in henry.js works on it, because the bone names are the same.
Plain Python only (no extra installs):

    python3 rig/tools/make_buddy.py rig/buddy.glb

Change the colours below to dress him differently, then run it again.
"""

import json
import math
import struct
import sys

SKIN = (0.93, 0.74, 0.58)
HAIR = (0.18, 0.12, 0.09)
SHIRT = (0.20, 0.45, 0.85)
PANTS = (0.22, 0.24, 0.30)
SHOES = (0.95, 0.95, 0.95)
EYE_WHITE = (0.98, 0.98, 0.98)
PUPIL = (0.08, 0.08, 0.10)
MOUTH = (0.45, 0.12, 0.14)

# Joint positions in model units: +Y up, +Z is his front, +X is his left. Soles sit at y=-0.95.
J = {
    "Hips": (0, -0.60, -0.05), "Spine": (0, -0.54, -0.05), "Spine1": (0, -0.49, -0.05),
    "Spine2": (0, -0.45, -0.05), "Neck": (0, -0.39, -0.05), "Head": (0, -0.30, -0.05),
    "Jaw": (0, -0.10, 0.10),
}
for side, sx in (("Left", 1), ("Right", -1)):
    J[side + "Shoulder"] = (0.13 * sx, -0.43, -0.05)
    J[side + "Arm"] = (0.27 * sx, -0.45, -0.05)
    J[side + "ForeArm"] = (0.30 * sx, -0.60, -0.05)
    J[side + "Hand"] = (0.34 * sx, -0.69, -0.05)
    J[side + "UpLeg"] = (0.10 * sx, -0.63, -0.05)
    J[side + "Leg"] = (0.10 * sx, -0.78, -0.05)
    J[side + "Foot"] = (0.11 * sx, -0.86, -0.04)
    J[side + "ToeBase"] = (0.11 * sx, -0.92, 0.10)
PARENT = {"Hips": None, "Spine": "Hips", "Spine1": "Spine", "Spine2": "Spine1", "Neck": "Spine2",
          "Head": "Neck", "Jaw": "Head"}
for s in ("Left", "Right"):
    PARENT.update({s + "Shoulder": "Spine2", s + "Arm": s + "Shoulder", s + "ForeArm": s + "Arm",
                   s + "Hand": s + "ForeArm", s + "UpLeg": "Hips", s + "Leg": s + "UpLeg",
                   s + "Foot": s + "Leg", s + "ToeBase": s + "Foot"})
NAMES = list(PARENT)
IDX = {k: i for i, k in enumerate(NAMES)}

pos, nrm, col, jnt, idx = [], [], [], [], []


def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def add(a, b): return tuple(x + y for x, y in zip(a, b))
def mul(a, k): return tuple(x * k for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def unit(a):
    d = math.sqrt(dot(a, a)) or 1.0
    return mul(a, 1 / d)


def ellipsoid(c, r, color, bone, seg=24, ring=16):
    """A squashed ball centred at c with radii r, moving with one bone."""
    start = len(pos)
    for i in range(ring + 1):
        th = math.pi * i / ring
        for k in range(seg + 1):
            ph = 2 * math.pi * k / seg
            u = (math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph))
            pos.append(add(c, (u[0] * r[0], u[1] * r[1], u[2] * r[2])))
            nrm.append(unit((u[0] / r[0], u[1] / r[1], u[2] / r[2])))
            col.append(color)
            jnt.append(IDX[bone])
    for i in range(ring):
        for k in range(seg):
            a = start + i * (seg + 1) + k
            b = a + seg + 1
            idx.extend((a, a + 1, b, a + 1, b + 1, b))


def capsule(p, q, rad, color, bone, seg=14):
    """A rounded tube from p to q: an arm or leg piece."""
    axis = sub(q, p)
    length = math.sqrt(dot(axis, axis))
    ax = unit(axis)
    ref = (1, 0, 0) if abs(ax[0]) < 0.9 else (0, 0, 1)
    e1 = unit(cross(ax, ref))
    e2 = cross(ax, e1)
    rings = []                     # (height along the axis, radius, normal tilt)
    half = 6
    for i in range(half + 1):      # bottom cap
        a = -math.pi / 2 + (math.pi / 2) * i / half
        rings.append((rad * math.sin(a), rad * math.cos(a), math.sin(a)))
    for i in range(half + 1):      # top cap
        a = (math.pi / 2) * i / half
        rings.append((length + rad * math.sin(a), rad * math.cos(a), math.sin(a)))
    start = len(pos)
    for h, rr, tilt in rings:
        for k in range(seg + 1):
            ph = 2 * math.pi * k / seg
            d = add(mul(e1, math.cos(ph)), mul(e2, math.sin(ph)))
            pos.append(add(add(p, mul(ax, h)), mul(d, rr)))
            nrm.append(unit(add(mul(d, math.sqrt(max(0.0, 1 - tilt * tilt))), mul(ax, tilt))))
            col.append(color)
            jnt.append(IDX[bone])
    for i in range(len(rings) - 1):
        for k in range(seg):
            a = start + i * (seg + 1) + k
            b = a + seg + 1
            idx.extend((a, a + 1, b, a + 1, b + 1, b))


def build():
    # head, hair, face
    ellipsoid((0, 0.26, -0.05), (0.52, 0.56, 0.48), SKIN, "Head", 32, 22)
    ellipsoid((0, 0.46, -0.10), (0.54, 0.46, 0.48), HAIR, "Head", 32, 22)
    for sx in (1, -1):
        ellipsoid((0.17 * sx, 0.30, 0.38), (0.085, 0.11, 0.06), EYE_WHITE, "Head")
        ellipsoid((0.17 * sx, 0.29, 0.43), (0.040, 0.055, 0.025), PUPIL, "Head")
        ellipsoid((0.50 * sx, 0.24, -0.05), (0.06, 0.10, 0.06), SKIN, "Head")            # ears
    ellipsoid((0, 0.17, 0.46), (0.05, 0.04, 0.04), SKIN, "Head")                        # nose
    ellipsoid((0, 0.02, 0.40), (0.14, 0.05, 0.05), MOUTH, "Jaw")                        # mouth
    # body
    capsule(J["Spine2"], J["Head"], 0.075, SKIN, "Neck")
    ellipsoid((0, -0.46, -0.05), (0.17, 0.09, 0.12), SHIRT, "Spine2")
    ellipsoid((0, -0.53, -0.05), (0.165, 0.08, 0.118), SHIRT, "Spine")
    ellipsoid((0, -0.615, -0.05), (0.165, 0.065, 0.115), PANTS, "Hips")
    for s, sx in (("Left", 1), ("Right", -1)):
        capsule(J[s + "Shoulder"], J[s + "Arm"], 0.05, SHIRT, s + "Shoulder")
        capsule(J[s + "Arm"], J[s + "ForeArm"], 0.045, SHIRT, s + "Arm")
        capsule(J[s + "ForeArm"], J[s + "Hand"], 0.04, SKIN, s + "ForeArm")
        ellipsoid(add(J[s + "Hand"], (0.01 * sx, -0.03, 0)), (0.045, 0.05, 0.04), SKIN, s + "Hand")
        capsule(J[s + "UpLeg"], J[s + "Leg"], 0.055, PANTS, s + "UpLeg")
        capsule(J[s + "Leg"], J[s + "Foot"], 0.05, PANTS, s + "Leg")
        foot = J[s + "Foot"]
        ellipsoid((foot[0], -0.915, 0.02), (0.06, 0.035, 0.10), SHOES, s + "Foot")


def pack(fmt, rows):
    return b"".join(struct.pack(fmt, *r) for r in rows)


def write(path):
    blob = bytearray()
    views, accs = [], []

    def put(data, ctype, typ, count, target=None, mn=None, mx=None):
        while len(blob) % 4:
            blob.append(0)
        views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data)})
        if target:
            views[-1]["target"] = target
        blob.extend(data)
        a = {"bufferView": len(views) - 1, "componentType": ctype, "count": count, "type": typ}
        if mn is not None:
            a["min"], a["max"] = mn, mx
        accs.append(a)
        return len(accs) - 1

    n = len(pos)
    mn = [min(p[i] for p in pos) for i in range(3)]
    mx = [max(p[i] for p in pos) for i in range(3)]
    attrs = {
        "POSITION": put(pack("<3f", pos), 5126, "VEC3", n, 34962, mn, mx),
        "NORMAL": put(pack("<3f", nrm), 5126, "VEC3", n, 34962),
        "COLOR_0": put(pack("<3f", col), 5126, "VEC3", n, 34962),
        "JOINTS_0": put(pack("<4B", [(j, 0, 0, 0) for j in jnt]), 5121, "VEC4", n, 34962),
        "WEIGHTS_0": put(pack("<4f", [(1, 0, 0, 0)] * n), 5126, "VEC4", n, 34962),
    }
    ind = put(pack("<I", [(i,) for i in idx]), 5125, "SCALAR", len(idx), 34963)
    ibm = []
    for k in NAMES:
        x, y, z = J[k]
        ibm.append((1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -x, -y, -z, 1))    # column-major
    ibm_acc = put(pack("<16f", ibm), 5126, "MAT4", len(NAMES))

    nodes = [{"name": "Henry", "mesh": 0, "skin": 0}]
    base = len(nodes)
    for k in NAMES:
        p = PARENT[k]
        t = sub(J[k], J[p]) if p else J[k]
        nodes.append({"name": "mixamorig" + k, "translation": [float(v) for v in t]})
    for k in NAMES:
        if PARENT[k]:
            nodes[base + IDX[PARENT[k]]].setdefault("children", []).append(base + IDX[k])

    gltf = {
        "asset": {"version": "2.0", "generator": "make_buddy.py"},
        "scene": 0, "scenes": [{"nodes": [0, base]}], "nodes": nodes,
        "meshes": [{"name": "Buddy", "primitives": [{"attributes": attrs, "indices": ind, "material": 0}]}],
        "materials": [{"name": "Buddy", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1],
                                                                  "metallicFactor": 0, "roughnessFactor": 0.8}}],
        "skins": [{"joints": [base + i for i in range(len(NAMES))], "skeleton": base,
                   "inverseBindMatrices": ibm_acc}],
        "accessors": accs, "bufferViews": views, "buffers": [{"byteLength": 0}],
    }
    while len(blob) % 4:
        blob.append(0)
    gltf["buffers"][0]["byteLength"] = len(blob)
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    out = (struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) +
           struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\0") + bytes(blob))
    with open(path, "wb") as f:
        f.write(out)
    print("Made %s: %d points, %d bones, %.0f KB" % (path, n, len(NAMES), len(out) / 1024))


if __name__ == "__main__":
    build()
    write(sys.argv[1] if len(sys.argv) > 1 else "buddy.glb")
