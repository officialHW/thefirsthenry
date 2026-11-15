// Tiny full-body Henry: loads the rigged Meshy model and moves him with code (no baked animations).
// Model axes: +Y up, +Z is his front, +X is his left. Every bone's rest rotation is zero,
// so bone.rotation is simply "how far from the rest pose", in those same axes.
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

// Graphics quality: "low" (default, for weak laptops) or "high". Set it with ?gfx=high in the
// address, or window.HENRY_GFX = "high" before this file loads.
const GFX = (new URLSearchParams(location.search).get("gfx") || window.HENRY_GFX || "low") === "high" ? "high" : "low";
const HIGH = GFX === "high";
const canvas = document.getElementById("c");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: HIGH, alpha: true, powerPreference: HIGH ? "high-performance" : "low-power" });
renderer.toneMapping = THREE.ACESFilmicToneMapping;
const scene = new THREE.Scene();
// the reflected-room lighting is the costly part, so low graphics uses a brighter plain light instead
if (HIGH) scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
scene.add(new THREE.HemisphereLight(0xffffff, 0x555577, HIGH ? 1.3 : 2.2));
const key = new THREE.DirectionalLight(0xfff1e0, 1.6); key.position.set(-1, 2, 3); scene.add(key);
// the camera works in screen pixels, so his size on screen is exact
const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, -2000, 2000);

const MODEL_H = 1.9, FEET_Y = -0.95;      // model height and where his soles are, in model units
const mover = new THREE.Group(); scene.add(mover);   // walks and turns
const scaler = new THREE.Group(); mover.add(scaler); // sets his size
const shadow = new THREE.Mesh(new THREE.CircleGeometry(0.42, 32),
  new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.35, depthWrite: false }));
shadow.rotation.x = -Math.PI / 2; shadow.scale.y = 0.6; shadow.position.y = FEET_Y; scaler.add(shadow);

const B = {};
const st = {
  ready: false, size: 110, margin: 28,
  x: 0, to: 0, dir: 1, amt: 0, ph: 0, face: 0, next: 0,
  waveUntil: 0, waveStart: 0, talkUntil: 0, mouth: 0, look: { x: 0, y: 0 }, mood: "neutral", speaking: false,
  y: 0, home: null, drag: null, dangle: 0,   // y: pixels above the floor; home: where you last put him
  // senses: where your pointer is, how fast it moves, short reactions that sit on top of his mood
  lookT: { x: 0, y: 0 }, cur: { x: -1e4, y: -1e4, v: 0, t: 0 }, mouseIn: false, lastInput: 0,
  reacts: [], hover: 0, waveCool: 0, scareCool: 0, hopStart: 0, hopUntil: 0, drowsy: 0,
  yawnStart: 0, yawnUntil: 0, nextYawn: 0, away: 0,
  // other screens: which sides have one, which way he is heading off (-1 left, 1 right), and when he left
  exits: { l: false, r: false }, crossing: 0, gone: 0,
};
st.lastInput = performance.now();

// a short reaction: a list of [mood, milliseconds] played in order, then back to his own mood
function react(list) {
  let at = performance.now();
  st.reacts = list.map(([m, ms]) => ({ m, from: at, to: (at += ms) }));
}
function reactMood(t) {
  while (st.reacts.length && t > st.reacts[0].to) st.reacts.shift();
  return st.reacts.length ? st.reacts[0].m : null;
}
function hop(ms = 380) { st.hopStart = performance.now(); st.hopUntil = st.hopStart + ms; }
function yawn() { st.yawnStart = performance.now(); st.yawnUntil = st.yawnStart + 1800; }
function wakeUp() {             // anything you do brings him back from dozing
  const t = performance.now();
  if (st.drowsy > 0.5) { react([["surprised", 600], ["happy", 1600]]); hop(); }
  st.drowsy = Math.min(st.drowsy, 0.5); st.lastInput = t;
}

// His own body if there is one, otherwise "Buddy", the simple stand-in body (same skeleton).
const MODEL = window.HENRY_MODEL || "henry-rigged.glb";
const BUDDY = MODEL.replace(/[^/]*$/, "buddy.glb");
function loadBody(url) {
  new GLTFLoader().load(url, (g) => {
    g.scene.traverse((o) => {
      if (o.isBone) B[o.name.replace(/^mixamorig:?/, "")] = o;
      if (o.isMesh) { o.frustumCulled = false; o.material.metalness = 0; o.material.roughness = 0.8; }
    });
    scaler.add(g.scene); st.ready = true;
  }, undefined, () => { if (url !== BUDDY) loadBody(BUDDY); });
}
loadBody(MODEL);

// Moods: how far each part moves from his normal stance. L/R = his left/right arm:
// [arm forward(-)/back(+), arm out to the side, forearm bend forward(-), forearm bend sideways].
// head: [nod down(+)/up(-), tilt]. lean: forward(+). bounce and shake are 0..1. jaw holds his mouth open.
const MOODS = {
  neutral:       {},
  calm:          { L: [0, .05, -.15, 0], R: [0, .05, -.15, 0], head: [.03, 0] },
  happy:         { L: [0, .30, -.2, 0], R: [0, .30, -.2, 0], head: [-.04, .05], bounce: .35 },
  excited:       { L: [-.3, 1.5, 0, .5], R: [-.3, 1.5, 0, .5], head: [-.08, 0], bounce: 1 },
  playful:       { L: [-.2, .9, -.3, .3], R: [.1, .3, -.6, 0], head: [0, .12], bounce: .6, sway: 1 },
  thinking:      { L: [0, .05, -.2, 0], R: [-.9, .25, -1.5, .2], head: [-.07, .09] },
  curious:       { L: [0, .1, -.3, 0], R: [-.3, .2, -.9, 0], head: [-.02, .17], lean: .09 },
  confused:      { L: [-.2, .55, -1.0, .2], R: [-.2, .55, -1.0, .2], head: [0, .15] },
  surprised:     { L: [-.3, .9, -.4, .2], R: [-.3, .9, -.4, .2], head: [-.1, 0], lean: -.05, jaw: .5 },
  shock:         { L: [-.4, 1.35, -.3, .3], R: [-.4, 1.35, -.3, .3], head: [-.12, 0], lean: -.1, jaw: .9 },
  nervous:       { L: [-.25, .05, -1.1, -.35], R: [-.25, .05, -1.1, -.35], head: [.08, .04], shake: .6 },
  embarrassment: { L: [0, .05, -.3, 0], R: [-.5, .15, -1.3, .1], head: [.16, .11], lean: .04 },
  sad:           { L: [.05, 0, -.05, 0], R: [.05, 0, -.05, 0], head: [.22, .04], lean: .12 },
  crying:        { L: [-.9, .2, -1.6, -.2], R: [-.9, .2, -1.6, -.2], head: [.26, 0], lean: .14, shake: .8 },
  angry:         { L: [.1, .45, -.9, -.5], R: [.1, .45, -.9, -.5], head: [.12, 0], lean: .06, shake: .3 },
  arrogance:     { L: [.15, .6, -.2, -1.2], R: [.15, .6, -.2, -1.2], head: [-.16, .05], lean: -.06 },
};
const Z4 = [0, 0, 0, 0];
const pose = { L: [0, 0, 0, 0], R: [0, 0, 0, 0], head: [0, 0], lean: 0, bounce: 0, shake: 0, sway: 0, jaw: 0 };

const noise = (t, s) => Math.sin(t * .00071 + s) * .5 + Math.sin(t * .00113 + s * 2.3) * .3 + Math.sin(t * .00197 + s * 4.1) * .2;
const lerp = (a, b, k) => a + (b - a) * Math.min(1, k);
const range = () => Math.max(0, innerWidth / 2 - st.size * 0.6);
// where he may wander: the whole floor, or a little patch around the spot you put him
const lo = () => st.home === null ? -range() : Math.max(-range(), st.home - st.size * 1.5);
const hi = () => st.home === null ? range() : Math.min(range(), st.home + st.size * 1.5);
const maxY = () => Math.max(0, innerHeight - st.margin - st.size * 1.15);
const off = () => innerWidth / 2 + st.size * 0.7;      // just out of sight past the edge
// walk off one side towards the screen next door (the desktop overlay moves his window there)
function cross(side) {
  if (!(side < 0 ? st.exits.l : st.exits.r) || st.crossing || st.drag) return false;
  st.home = null; st.crossing = side; st.to = side * off(); st.next = performance.now() + 20000;
  return true;
}
// he comes in from the edge opposite the way he was walking
function arrive(side) {
  resizeT = performance.now() + 2500;
  setTimeout(() => {
    st.x = -side * off(); st.to = -side * range() * (0.1 + Math.random() * 0.7);
    st.dir = side; st.crossing = 0; st.gone = 0; mover.visible = true;
    st.next = performance.now() + 8000;
  }, 250);
}

let last = performance.now();
const FRAME_MS = HIGH ? 0 : 1000 / 30 - 2;   // low graphics draws about 30 times a second
function frame(t) {
  requestAnimationFrame(frame);
  if (t - last < FRAME_MS) return;
  const sec = Math.min(0.1, (t - last) / 1000); last = t;
  const w = innerWidth, h = innerHeight;
  renderer.setPixelRatio(HIGH ? Math.min(2, devicePixelRatio) : 1); renderer.setSize(w, h, false);
  cam.left = -w / 2; cam.right = w / 2; cam.top = h / 2; cam.bottom = -h / 2; cam.updateProjectionMatrix();
  if (!st.ready) return;
  const s = st.size / MODEL_H; scaler.scale.setScalar(s);

  // ----- senses: your pointer, being left alone, the time of day -----
  const busyNow = st.speaking || st.drag || t < st.talkUntil;
  const hx = w / 2 + st.x, hy = h - st.margin - st.y - st.size * 0.55;       // his middle, in page pixels
  const dist = st.mouseIn ? Math.hypot(st.cur.x - hx, (st.cur.y - hy) * 1.3) : 1e9;
  const near = dist < st.size * 1.4, onHim = dist < st.size * 0.45;
  const fresh = t - st.cur.t < 400;                                            // pointer moved just now
  if (!busyNow) {
    if (near && fresh && st.cur.v > 1.6 && t > st.scareCool) {                 // a fast swipe right past him
      react([["surprised", 900], ["nervous", 900]]); hop(300);
      st.to = st.x - Math.sign(st.cur.x - hx || 1) * st.size * 0.9;           // hops back out of the way
      st.next = t + 5000; st.scareCool = t + 3000;
    } else if (near && !st.reacts.length) {
      react([["curious", 1200]]);                                              // what's that?
    }
    if (near && st.amt < 0.3 && t > st.scareCool - 1500) { st.to = st.x; st.next = Math.max(st.next, t + 2500); }   // stops to watch it
    st.hover = onHim && st.cur.v < 0.5 ? st.hover + sec * 1000 : 0;
    if (st.hover > 1300 && t > st.waveCool) {                                  // you hover over him: he says hi
      Henry.wave(1800); react([["happy", 2200]]); st.waveCool = t + 15000; st.hover = 0;
    }
  }
  // left alone for a while, he gets sleepy (sooner at night), and yawns now and then
  const hr = new Date().getHours(), night = hr >= 22 || hr < 6;
  const quiet = t - st.lastInput, sleepAfter = night ? 25000 : 60000;
  st.drowsy = lerp(st.drowsy, !busyNow && quiet > sleepAfter ? 1 : 0, sec * 0.6);
  if (!st.nextYawn) st.nextYawn = t + 20000;
  if (!busyNow && t > st.nextYawn && (night || st.drowsy > 0.3 || quiet > 30000)) {
    yawn(); st.nextYawn = t + (night ? 25000 : 45000) + Math.random() * 20000;
  }
  // he looks where your pointer is; with no pointer around he looks out at you
  if (!st.mouseIn && !st.typing) { st.lookT.x = 0; st.lookT.y = 0; }
  st.look.x = lerp(st.look.x, st.lookT.x, sec * 6); st.look.y = lerp(st.look.y, st.lookT.y, sec * 6);

  // ----- where he is going -----
  if (!st.next) st.next = t + 2500;
  if (t > st.next && st.amt < 0.02 && t > st.waveUntil && t > st.talkUntil && !st.speaking && !st.drag && st.drowsy < 0.4 && !near) {
    st.to = lo() + Math.random() * (hi() - lo()); st.next = t + 5000 + Math.random() * 7000;
    const sides = [st.exits.l && -1, st.exits.r && 1].filter(Boolean);       // now and then he visits another screen
    if (st.home === null && sides.length && Math.random() < 0.3) cross(sides[Math.floor(Math.random() * sides.length)]);
  }
  if (st.drag) st.to = st.x;
  if (st.crossing && !st.gone && st.to !== st.crossing * off()) st.crossing = 0;   // something stopped him: he stays
  if (st.gone && t - st.gone > 3000) arrive(-st.crossing), st.gone = t;           // nobody moved the window: come back in
  if (!st.crossing) st.to = Math.max(-range(), Math.min(range(), st.to));
  st.y = Math.max(0, Math.min(maxY(), st.y));
  st.dangle = lerp(st.dangle, st.drag ? 1 : 0, sec * 10);
  const dx = st.to - st.x, moving = Math.abs(dx) > 1;
  if (moving) st.dir = Math.sign(dx);
  const turned = Math.abs(st.face - st.dir * 1.25) < 0.5;       // turn first, then step off (no moonwalk)
  st.amt = lerp(st.amt, moving && turned ? 1 : 0, sec * 5);
  const step = moving ? st.dir * Math.min(Math.abs(dx), st.size * 0.55 * st.amt * sec) : 0;
  st.x += step;
  if (st.crossing && !st.gone && Math.abs(st.x - st.to) <= 1) {      // out of sight: ask for the next screen
    st.gone = t; mover.visible = false; resizeT = t + 2500;
    window.dispatchEvent(new CustomEvent("henry-cross", { detail: st.crossing }));
  }
  st.ph += Math.abs(step) / (st.size * 0.30) * Math.PI * 2;      // steps match distance, so feet don't slide
  st.face = lerp(st.face, moving ? st.dir * 1.25 : st.look.x * 0.5, sec * 7);   // turns his body toward you too

  const a = st.amt, ph = st.ph, sw = Math.sin(ph), idle = 1 - a;
  // ease toward the current mood's pose (a short reaction wins, unless he's talking or being carried)
  const r = busyNow ? null : reactMood(t);
  const mood = r || (st.drowsy > 0.6 && st.mood === "neutral" ? "calm" : st.mood);
  const M = MOODS[mood] || MOODS.neutral, k = sec * 6;
  for (let i = 0; i < 4; i++) { pose.L[i] = lerp(pose.L[i], (M.L || Z4)[i], k); pose.R[i] = lerp(pose.R[i], (M.R || Z4)[i], k); }
  for (let i = 0; i < 2; i++) pose.head[i] = lerp(pose.head[i], (M.head || Z4)[i], k);
  for (const f of ["lean", "bounce", "shake", "sway", "jaw"]) pose[f] = lerp(pose[f], M[f] || 0, k);
  const jump = t < st.hopUntil ? Math.sin((t - st.hopStart) / (st.hopUntil - st.hopStart) * Math.PI) * st.size * 0.14 : 0;
  const hop = Math.abs(Math.sin(t / 170)) * pose.bounce * idle * st.size * 0.035 + jump;
  const yw = t < st.yawnUntil ? Math.sin((t - st.yawnStart) / (st.yawnUntil - st.yawnStart) * Math.PI) : 0;
  const jit = Math.sin(t / 38) * pose.shake * 0.02, swy = Math.sin(t / 420) * pose.sway * 0.12 * idle;
  mover.position.set(st.x, -h / 2 + st.margin + st.y - FEET_Y * s + Math.abs(Math.cos(ph)) * a * st.size * 0.012 + hop, 0);
  mover.rotation.y = st.face;
  mover.rotation.z = st.drag ? Math.sin(t / 160) * 0.12 * st.dangle : 0;   // swings a little while carried
  shadow.visible = !st.drag;

  // ----- body -----
  const breath = Math.sin(t / 900);
  B.Hips.rotation.set(0.02 * a, sw * 0.08 * a, Math.cos(ph) * 0.03 * a + swy * 0.4);
  B.Spine.rotation.set(0.05 * a + breath * 0.012 + pose.lean * idle, -sw * 0.10 * a, noise(t, 1) * 0.02 + swy + jit);
  // ----- head: looks at the mouse when standing, ahead when walking -----
  // dozing: head droops with a slow nod; yawning: head tips back
  const doze = st.drowsy * (0.22 + Math.sin(t / 1400) * 0.05);
  B.Neck.rotation.set((-st.look.y * 0.35 + noise(t, 5) * 0.03 + pose.head[0] + doze - yw * 0.25) * idle,
    (st.look.x * 0.55 + noise(t, 9) * 0.05) * idle + jit, noise(t, 3) * 0.035 + pose.head[1] * idle);
  // ----- legs -----
  for (const [S, k] of [["Left", 1], ["Right", -1]]) {
    const p = Math.sin(ph + (k > 0 ? 0 : Math.PI)), lift = Math.max(0, Math.cos(ph + (k > 0 ? 0 : Math.PI)));
    const kick = st.dangle * Math.sin(t / 110 + (k > 0 ? 0 : 1.7)) * 0.35;   // legs wiggle while carried
    B[S + "UpLeg"].rotation.set(-p * 0.6 * a + kick, 0, 0);
    B[S + "Leg"].rotation.set(lift * 0.9 * a + Math.abs(kick) * 0.8, 0, 0);
    B[S + "Foot"].rotation.set(-lift * 0.3 * a, 0, 0);
  }
  // ----- arms: swing while walking, hang with a little life when idle -----
  // his left arm goes out with +z and his right with -z, so the right side's sideways numbers are flipped
  const armL = { x: sw * 0.55 * a + pose.L[0] * idle, z: 0.06 + breath * 0.015 + pose.L[1] * idle, fx: -0.25 * a + pose.L[2] * idle, fz: pose.L[3] * idle };
  const armR = { x: -sw * 0.55 * a + pose.R[0] * idle, z: -0.06 - breath * 0.015 - pose.R[1] * idle, fx: -0.25 * a + pose.R[2] * idle, fz: -pose.R[3] * idle };
  // wave with his right arm: out to the side and a little forward, forearm rocking
  const wv = t < st.waveUntil ? Math.min(1, (t - st.waveStart) / 250, (st.waveUntil - t) / 300) : 0;
  if (wv > 0) {
    armR.x = lerp(armR.x, -0.55, wv); armR.z = lerp(armR.z, -1.75, wv);
    armR.fz = (-0.55 + Math.sin((t - st.waveStart) / 95) * 0.45) * wv; armR.fx = 0;
  }
  // talking: small hand gestures
  const talking = t < st.talkUntil || st.speaking;
  if (talking && wv === 0) { armL.z += 0.25 + noise(t * 3, 2) * 0.2; armL.fx = -0.5 + noise(t * 3, 7) * 0.3; armR.z -= 0.2; }
  B.LeftArm.rotation.set(armL.x, 0, armL.z); B.LeftForeArm.rotation.set(armL.fx, 0, armL.fz);
  B.RightArm.rotation.set(armR.x, 0, armR.z); B.RightForeArm.rotation.set(armR.fx, 0, armR.fz);
  // ----- jaw -----
  const target = talking && !st.realMouth ? Math.max(0, 0.5 + 0.5 * Math.sin(t / 70) * Math.sin(t / 190 + 1)) : 0;
  st.mouth = lerp(st.mouth, Math.max(target, st.mouthExt || 0), sec * 22);
  if (B.Jaw) B.Jaw.rotation.x = Math.max(st.mouth, pose.jaw, yw * 1.1) * 0.11;
  if (yw > 0) { B.LeftArm.rotation.z += yw * 0.5; B.RightArm.rotation.z -= yw * 0.5; }   // a little stretch

  renderer.render(scene, cam);
}
requestAnimationFrame(frame);

// ----- pick him up and put him anywhere with the mouse (or a finger) -----
const feetY = () => innerHeight - st.margin - st.y;     // his soles, in page pixels from the top
function onHenry(e) {
  const cx = innerWidth / 2 + st.x;
  return Math.abs(e.clientX - cx) < st.size * 0.35 && e.clientY < feetY() + 6 && e.clientY > feetY() - st.size;
}
canvas.style.touchAction = "none";
canvas.addEventListener("pointerdown", (e) => {
  wakeUp();
  if (!onHenry(e)) {                       // clicked somewhere else: he goes over to have a look
    if (st.speaking || st.drag) return;
    st.to = st.home = Math.max(-range(), Math.min(range(), e.clientX - innerWidth / 2));
    st.next = performance.now() + 7000; react([["curious", 2500]]);
    return;
  }
  st.drag = { dx: e.clientX - (innerWidth / 2 + st.x), dy: e.clientY - feetY(), mood: st.mood,
              sx: e.clientX, sy: e.clientY, t: performance.now() };
  st.mood = "surprised"; st.face = 0; st.amt = 0;
  canvas.setPointerCapture(e.pointerId); canvas.style.cursor = "grabbing";
  window.dispatchEvent(new Event("henry-pickup"));
});
// where your pointer is and how fast it's going (pixels per millisecond)
function sense(e) {
  const t = performance.now(), dt = Math.max(1, t - st.cur.t);
  const sp = st.cur.t ? Math.hypot(e.clientX - st.cur.x, e.clientY - st.cur.y) / dt : 0;
  st.cur.v = lerp(st.cur.v, Math.min(sp, 5), 0.5);
  st.cur.x = e.clientX; st.cur.y = e.clientY; st.cur.t = t; st.mouseIn = true; st.typing = false;
  if (st.drowsy > 0.5 && sp > 0.3) wakeUp(); else st.lastInput = t;
}
document.addEventListener("mouseleave", () => { st.mouseIn = false; st.cur.v = 0; });
addEventListener("blur", () => { st.mouseIn = false; st.away = performance.now(); });
addEventListener("focus", () => {          // you came back to his window after a while: he waves
  const t = performance.now();
  if (st.away && t - st.away > 20000 && !st.speaking) { Henry.wave(1800); react([["happy", 2000]]); }
  st.away = 0; wakeUp();
});
// typing: he looks over at the box you're typing in
addEventListener("keydown", () => {
  wakeUp();
  const el = document.activeElement;
  if (!el || !/^(INPUT|TEXTAREA)$/.test(el.tagName)) return;
  const b = el.getBoundingClientRect();
  st.lookT.x = Math.max(-1, Math.min(1, (b.left + b.width * 0.3 - innerWidth / 2 - st.x) / 250));
  st.lookT.y = Math.max(-1, Math.min(1, (feetY() - st.size * 0.7 - (b.top + b.height / 2)) / 250));
  st.typing = true;
  if (!st.speaking && !st.reacts.length) react([["curious", 1500]]);
});
let resizeT = 0;
addEventListener("resize", () => {          // the window changes size: the floor moved under him
  const t = performance.now();
  if (t > resizeT && !st.speaking) { react([["surprised", 700]]); hop(300); }
  resizeT = t + 1500;
});
addEventListener("pointermove", (e) => {
  sense(e);
  st.lookT.x = Math.max(-1, Math.min(1, (e.clientX - innerWidth / 2 - st.x) / 250));
  st.lookT.y = Math.max(-1, Math.min(1, (feetY() - st.size * 0.7 - e.clientY) / 250));
  if (st.drag) {
    st.x = Math.max(-range(), Math.min(range(), e.clientX - st.drag.dx - innerWidth / 2));
    st.y = Math.max(0, Math.min(maxY(), innerHeight - st.margin - (e.clientY - st.drag.dy)));
    st.to = st.x;
  } else canvas.style.cursor = onHenry(e) ? "grab" : "";
});
function drop() {
  if (!st.drag) return;
  const d = st.drag, poke = performance.now() - d.t < 300 && Math.hypot(st.cur.x - d.sx, st.cur.y - d.sy) < 6;
  st.mood = d.mood; st.drag = null; st.home = st.x; st.to = st.x;
  if (poke) {                               // a quick click on him is a poke: he giggles and hops
    react([["playful", 1600]]); hop(); Henry.say(700);
    window.dispatchEvent(new Event("henry-poke"));
  }
  st.next = performance.now() + 8000; canvas.style.cursor = "";
  if (!poke && Math.abs(st.x) >= range() - 2) cross(Math.sign(st.x));   // put down against an edge: he carries on to the next screen
  window.dispatchEvent(new Event("henry-drop"));
}
addEventListener("pointerup", drop);
addEventListener("pointercancel", drop);

// what the rest of the app calls
window.Henry = {
  get size() { return st.size; }, state: st, bones: B, graphics: GFX,
  setSize(px) { st.size = px; },                              // his height on screen, in pixels
  walkTo(f) { st.to = f * range(); st.next = performance.now() + 6000; },   // -1 = far left, 1 = far right
  wave(ms = 2200) { st.waveStart = performance.now(); st.waveUntil = st.waveStart + ms; st.to = st.x; },
  say(ms = 2500) { st.talkUntil = performance.now() + ms; st.to = st.x; },  // jaw + gestures for that long
  setMouth(v) { st.mouthExt = v; },                           // 0..1, to drive the jaw from real speech
  moods: Object.keys(MOODS),
  setMood(name) { if (MOODS[name]) st.mood = name; return st.mood; },
  comeHere() { st.home = null; st.y = 0; st.to = 0; st.next = performance.now() + 8000; },   // back to the floor, middle
  placeAt(x, y) { st.x = st.to = st.home = x; st.y = y; },   // x from the middle, y above the floor, in pixels
  freeRoam() { st.home = null; },                            // wander the whole width again
  setExits(l, r) { st.exits.l = !!l; st.exits.r = !!r; },    // is there another screen to the left / right
  cross, arrive,                                             // cross(-1 | 1): walk off to the screen on that side
  // says the text out loud with the browser's own voice; his jaw and hands move until it ends
  speak(text, voiceName) {
    return new Promise((done) => {
      if (!("speechSynthesis" in window) || !text) return done(false);
      const u = new SpeechSynthesisUtterance(text);
      const v = speechSynthesis.getVoices().find((x) => x.name === voiceName); if (v) u.voice = v;
      const stop = (ok) => { st.speaking = false; done(ok); };
      u.onstart = () => { st.speaking = true; st.to = st.x; };
      u.onend = () => stop(true); u.onerror = () => stop(false);
      speechSynthesis.cancel(); speechSynthesis.speak(u);
    });
  },
  hush() { if ("speechSynthesis" in window) speechSynthesis.cancel(); st.speaking = false; },
};
window.dispatchEvent(new Event("henry-api"));
