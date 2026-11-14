# Tiny 3D Henry (the body)

A thumb-sized, full-body 3D Henry that walks, waves, talks and shows moods. It is only the body:
any brain (Hermes Agent, or the old `server.js`) drives it through `window.Henry`.

## Files

- `henry-rigged.glb`: your own body, with a 23-bone skeleton (left out of the starter kit).
- `buddy.glb`: the simple stand-in body, used whenever `henry-rigged.glb` is missing.
- `henry.js`: draws him and moves him. All motion is code, there are no baked animations.
- `demo.html`: a test page with buttons. `demo.html?m=buddy.glb` tries another body file from this folder.
- `tools/make_buddy.py`: builds `buddy.glb` (plain Python): `python3 tools/make_buddy.py buddy.glb`
- `tools/rig.py`: adds a skeleton to the original Meshy model of Henry. Its numbers are tuned to that
  one model, so a different model needs its own numbers or a rig from a 3D tool.
- `vendor/three/`: the three.js 0.170.0 engine files.

## Using your own body

Any rigged `.glb` works if its bones use Mixamo names (a `mixamorig` prefix is fine): Hips, Spine,
Neck, Head, LeftArm, LeftForeArm, LeftUpLeg, LeftLeg, LeftFoot, and the Right ones. A `Jaw` bone
makes the mouth move; without one he still talks with his hands. He should stand about 1.9 units
tall with his soles at y = -0.95, facing +Z (Buddy's numbers are in `tools/make_buddy.py`).

## Try it

Serve this folder on your own computer only, then open http://localhost:4750/demo.html

    python3 -m http.server 4750 --bind 127.0.0.1 --directory rig

## What a brain can call

| Call | What he does |
| --- | --- |
| `Henry.speak("text")` | Says it with the browser's voice; jaw and hands move until it ends. Returns a promise. |
| `Henry.hush()` | Stops talking. |
| `Henry.setMood("happy")` | One of the 16 names in `Henry.moods`. |
| `Henry.wave()` | Waves with his right arm. |
| `Henry.walkTo(-1 … 1)` | Walks to a spot: -1 is far left, 1 is far right. |
| `Henry.comeHere()` | Walks to the middle. |
| `Henry.setSize(110)` | His height on screen in pixels. |
| `Henry.setMouth(0 … 1)` | Drives the jaw directly, for lip-sync from your own audio. |
| `Henry.say(ms)` | Moves jaw and hands for that long with no sound. |

He also wanders on his own every few seconds and turns his head toward the mouse.

## Limits

- On the Meshy Henry the face is one painted picture: no blinking, eye movement or lip shapes. Only the jaw drops.
- His head is very large and his arms and legs are short, so the wave sits at hip height and steps are small.
- The skeleton was made by a script, not by an artist, so sleeves and trousers stretch a little at big angles.
