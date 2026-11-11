// Dev-Studio Characters:
// 1. DevGuy: The human developer creator (seated at desk, blue hoodie, expressive 3D face, holding phone/gesturing).
// 2. MascotBot: The cute floating AI companion (glossy white egg bot, curved cyber visor with glowing LED eyes, antenna, hovering fins).
import * as THREE from 'three';

const SKIN_TONE = '#E5A65D';
const HOODIE_BLUE = '#1E293B';
const HOODIE_STRING = '#F8FAFC';
const HAIR_DARK = '#1C1917';
const BOT_WHITE = '#FFFFFF';
const BOT_VISOR = '#090D16';
const CYAN_GLOW = '#00F0FF';
const AMBER_GLOW = '#FF9800';

/** Dynamic face texture generator for Human Developer */
function makeHumanFaceCanvas() {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return { canvas, ctx, tex };
}

function renderHumanFace(face, st) {
  const { ctx, tex } = face;
  const { mood = 'neutral', talk = 0, blink = 0, lookX = 0, lookY = 0 } = st;

  // Clear skin canvas
  ctx.fillStyle = SKIN_TONE;
  ctx.fillRect(0, 0, 512, 512);

  const leftX = 160 + lookX * 18;
  const rightX = 352 + lookX * 18;
  const eyeY = 230 + lookY * 12;

  // Eyebrows
  ctx.strokeStyle = HAIR_DARK;
  ctx.lineWidth = 14;
  ctx.lineCap = 'round';
  ctx.beginPath();
  if (mood === 'skeptical' || mood === 'doubting') {
    // Left raised, right furrowed
    ctx.moveTo(leftX - 35, eyeY - 60);
    ctx.quadraticCurveTo(leftX, eyeY - 75, leftX + 35, eyeY - 55);
    ctx.moveTo(rightX - 35, eyeY - 45);
    ctx.quadraticCurveTo(rightX, eyeY - 40, rightX + 35, eyeY - 50);
  } else if (mood === 'shock' || mood === 'surprised') {
    // Both high arched
    ctx.moveTo(leftX - 35, eyeY - 70);
    ctx.quadraticCurveTo(leftX, eyeY - 85, leftX + 35, eyeY - 70);
    ctx.moveTo(rightX - 35, eyeY - 70);
    ctx.quadraticCurveTo(rightX, eyeY - 85, rightX + 35, eyeY - 70);
  } else {
    // Relaxed confident natural
    ctx.moveTo(leftX - 35, eyeY - 50);
    ctx.quadraticCurveTo(leftX, eyeY - 58, leftX + 35, eyeY - 48);
    ctx.moveTo(rightX - 35, eyeY - 48);
    ctx.quadraticCurveTo(rightX, eyeY - 58, rightX + 35, eyeY - 50);
  }
  ctx.stroke();

  // Eyes
  if (blink > 0.4) {
    // Blinking eyelids
    ctx.strokeStyle = '#2B1810';
    ctx.lineWidth = 10;
    ctx.beginPath();
    ctx.moveTo(leftX - 30, eyeY);
    ctx.quadraticCurveTo(leftX, eyeY + 12, leftX + 30, eyeY);
    ctx.moveTo(rightX - 30, eyeY);
    ctx.quadraticCurveTo(rightX, eyeY + 12, rightX + 30, eyeY);
    ctx.stroke();
  } else {
    // Eye whites
    ctx.fillStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.ellipse(leftX, eyeY, 34, 24, 0, 0, Math.PI * 2);
    ctx.ellipse(rightX, eyeY, 34, 24, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#3A1F12';
    ctx.lineWidth = 4;
    ctx.stroke();

    // Iris (Deep brown)
    ctx.fillStyle = '#321E14';
    ctx.beginPath();
    ctx.arc(leftX + lookX * 6, eyeY + lookY * 4, 18, 0, Math.PI * 2);
    ctx.arc(rightX + lookX * 6, eyeY + lookY * 4, 18, 0, Math.PI * 2);
    ctx.fill();

    // Catchlight highlight sparkles
    ctx.fillStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.arc(leftX + lookX * 6 - 5, eyeY + lookY * 4 - 5, 6, 0, Math.PI * 2);
    ctx.arc(rightX + lookX * 6 - 5, eyeY + lookY * 4 - 5, 6, 0, Math.PI * 2);
    ctx.fill();
  }

  // Mouth
  const mouthY = 380;
  if (talk > 0.25) {
    const openH = Math.min(38, Math.max(14, talk * 38));
    ctx.fillStyle = '#4A151B';
    ctx.beginPath();
    ctx.roundRect(256 - 36, mouthY - openH / 2, 72, openH, openH / 2);
    ctx.fill();
    // Teeth
    ctx.fillStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.roundRect(256 - 24, mouthY - openH / 2, 48, 8, 4);
    ctx.fill();
  } else {
    ctx.strokeStyle = '#5A1E14';
    ctx.lineWidth = 7;
    ctx.lineCap = 'round';
    ctx.beginPath();
    if (mood === 'shock' || mood === 'skeptical') {
      ctx.arc(256, mouthY + 10, 20, 1.1 * Math.PI, 1.9 * Math.PI);
    } else {
      ctx.arc(256, mouthY - 10, 28, 0.15 * Math.PI, 0.85 * Math.PI);
    }
    ctx.stroke();
  }

  tex.needsUpdate = true;
}

/** Dynamic face texture generator for Mascot Cyber Bot */
function makeBotFaceCanvas() {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return { canvas, ctx, tex };
}

function renderBotFace(face, st) {
  const { ctx, tex } = face;
  const { mood = 'neutral', talk = 0, blink = 0 } = st;

  // Dark cyber visor plate
  ctx.fillStyle = BOT_VISOR;
  ctx.fillRect(0, 0, 512, 512);

  // Subtle visor grid lines
  ctx.strokeStyle = 'rgba(0, 240, 255, 0.05)';
  ctx.lineWidth = 2;
  for (let y = 0; y < 512; y += 32) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(512, y); ctx.stroke();
  }

  const leftX = 165;
  const rightX = 347;
  const eyeY = 230;

  // Visor LED Eyes
  ctx.fillStyle = CYAN_GLOW;
  ctx.shadowColor = CYAN_GLOW;
  ctx.shadowBlur = 18;

  if (blink > 0.45) {
    // Thin horizontal slit
    ctx.fillRect(leftX - 35, eyeY - 4, 70, 8);
    ctx.fillRect(rightX - 35, eyeY - 4, 70, 8);
  } else if (mood === 'happy' || mood === 'witty') {
    // Happy curved crescents (^ ^)
    ctx.strokeStyle = CYAN_GLOW;
    ctx.lineWidth = 18;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.arc(leftX, eyeY + 14, 32, 1.15 * Math.PI, 1.85 * Math.PI);
    ctx.arc(rightX, eyeY + 14, 32, 1.15 * Math.PI, 1.85 * Math.PI);
    ctx.stroke();
  } else if (mood === 'shock' || mood === 'amazed') {
    // Big round glowing circles
    ctx.beginPath();
    ctx.arc(leftX, eyeY, 44, 0, Math.PI * 2);
    ctx.arc(rightX, eyeY, 44, 0, Math.PI * 2);
    ctx.fill();
  } else {
    // Sleek rounded capsule eyes
    ctx.beginPath();
    ctx.roundRect(leftX - 30, eyeY - 42, 60, 84, 28);
    ctx.roundRect(rightX - 30, eyeY - 42, 60, 84, 28);
    ctx.fill();
  }

  // Animated LED mouth
  if (talk > 0.2) {
    const mouthW = 44 + talk * 30;
    ctx.fillStyle = CYAN_GLOW;
    ctx.beginPath();
    ctx.roundRect(256 - mouthW / 2, 360, mouthW, 14, 7);
    ctx.fill();
  }

  ctx.shadowBlur = 0;
  tex.needsUpdate = true;
}

export class DevGuy {
  constructor() {
    this.group = new THREE.Group();
    this.face = makeHumanFaceCanvas();

    this.bodyGroup = new THREE.Group();
    this.group.add(this.bodyGroup);

    // 1. Torso: Navy Blue Developer Hoodie
    const hoodieGeo = new THREE.BoxGeometry(0.88, 1.05, 0.52);
    const hoodieMat = new THREE.MeshStandardMaterial({
      color: HOODIE_BLUE,
      roughness: 0.65,
      metalness: 0.05
    });
    this.torso = new THREE.Mesh(hoodieGeo, hoodieMat);
    this.torso.position.y = 0.85;
    this.torso.castShadow = true;
    this.bodyGroup.add(this.torso);

    // White Hoodie Drawstrings
    const stringGeo = new THREE.CylinderGeometry(0.012, 0.012, 0.38, 8);
    const stringMat = new THREE.MeshStandardMaterial({ color: HOODIE_STRING, roughness: 0.5 });
    const strL = new THREE.Mesh(stringGeo, stringMat);
    const strR = new THREE.Mesh(stringGeo, stringMat);
    strL.position.set(-0.12, 0.95, 0.28);
    strR.position.set(0.12, 0.95, 0.28);
    this.bodyGroup.add(strL);
    this.bodyGroup.add(strR);

    // 2. Head & Hair
    this.headGroup = new THREE.Group();
    this.headGroup.position.set(0, 1.72, 0);
    this.bodyGroup.add(this.headGroup);

    // Head base (Skin tone)
    const headGeo = new THREE.BoxGeometry(0.68, 0.68, 0.62);
    const skinMat = new THREE.MeshStandardMaterial({ color: SKIN_TONE, roughness: 0.55 });
    const faceMat = new THREE.MeshBasicMaterial({ map: this.face.tex });
    const headMats = [skinMat, skinMat, skinMat, skinMat, faceMat, skinMat];
    this.headMesh = new THREE.Mesh(headGeo, headMats);
    this.headMesh.castShadow = true;
    this.headGroup.add(this.headMesh);

    // Modern Stylized Dark Hair
    const hairGeo = new THREE.BoxGeometry(0.74, 0.24, 0.68);
    const hairMat = new THREE.MeshStandardMaterial({ color: HAIR_DARK, roughness: 0.8 });
    const hairTop = new THREE.Mesh(hairGeo, hairMat);
    hairTop.position.set(0, 0.36, -0.02);
    this.headGroup.add(hairTop);

    // Hair Side Burns
    const hairSideL = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.38, 0.52), hairMat);
    const hairSideR = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.38, 0.52), hairMat);
    hairSideL.position.set(-0.35, 0.12, -0.06);
    hairSideR.position.set(0.35, 0.12, -0.06);
    this.headGroup.add(hairSideL);
    this.headGroup.add(hairSideR);

    // 3. Arms & Hands
    const armGeo = new THREE.BoxGeometry(0.2, 0.54, 0.2);
    const armMat = new THREE.MeshStandardMaterial({ color: HOODIE_BLUE, roughness: 0.65 });
    
    // Left Arm (Resting naturally on desk)
    this.armL = new THREE.Mesh(armGeo, armMat);
    this.armL.position.set(-0.54, 0.82, 0.15);
    this.armL.rotation.x = 0.45;
    this.armL.castShadow = true;
    this.bodyGroup.add(this.armL);

    // Right Arm (Holding phone or gesturing)
    this.armR = new THREE.Mesh(armGeo, armMat);
    this.armR.position.set(0.54, 0.88, 0.18);
    this.armR.rotation.x = 0.65;
    this.armR.castShadow = true;
    this.bodyGroup.add(this.armR);

    // Smartphone Prop in Hand
    this.phone = this._makePhone();
    this.phone.position.set(0, -0.28, 0.12);
    this.phone.rotation.x = -0.35;
    this.armR.add(this.phone);

    // Grounded Seated Base
    this.seatBase = new THREE.Mesh(
      new THREE.BoxGeometry(0.78, 0.35, 0.72),
      new THREE.MeshStandardMaterial({ color: '#0F172A', roughness: 0.7 })
    );
    this.seatBase.position.y = 0.18;
    this.group.add(this.seatBase);

    this.st = { mood: 'neutral', talk: 0, blink: 0 };
    renderHumanFace(this.face, this.st);
  }

  _makePhone() {
    const g = new THREE.Group();
    // Glass slab
    const body = new THREE.Mesh(
      new THREE.BoxGeometry(0.18, 0.36, 0.016),
      new THREE.MeshStandardMaterial({ color: '#0F172A', metalness: 0.8, roughness: 0.2 })
    );
    g.add(body);
    // Glowing screen
    const screen = new THREE.Mesh(
      new THREE.PlaneGeometry(0.16, 0.33),
      new THREE.MeshBasicMaterial({ color: '#38BDF8' })
    );
    screen.position.z = 0.009;
    g.add(screen);
    return g;
  }

  set(st = {}, t = 0) {
    this.update(t, st);
  }

  update(t, st = {}) {
    this.st = Object.assign(this.st, st);
    renderHumanFace(this.face, this.st);

    // Subtle natural breathing sway (anchored to desk)
    const breath = Math.sin(t * 1.8) * 0.012;
    this.bodyGroup.position.y = breath;
    this.headGroup.rotation.y = (this.st.lookX || 0) * 0.25;
    this.headGroup.rotation.x = (this.st.lookY || 0) * 0.15;

    // Speech gesture
    if (this.st.talk > 0.1) {
      this.armR.rotation.x = 0.65 + Math.sin(t * 5.5) * 0.08;
    }
  }
}

export class MascotBot {
  constructor() {
    this.group = new THREE.Group();
    this.face = makeBotFaceCanvas();

    this.botBody = new THREE.Group();
    this.group.add(this.botBody);

    // 1. Egg-shaped Ceramic White Body
    const bodyGeo = new THREE.SphereGeometry(0.46, 32, 28);
    bodyGeo.scale(0.88, 1.08, 0.88);
    const bodyMat = new THREE.MeshStandardMaterial({
      color: BOT_WHITE,
      roughness: 0.12,
      metalness: 0.06
    });
    this.bodyMesh = new THREE.Mesh(bodyGeo, bodyMat);
    this.bodyMesh.position.y = 1.35;
    this.bodyMesh.castShadow = true;
    this.botBody.add(this.bodyMesh);

    // 2. Glossy Curved Front Visor Screen
    const visorGeo = new THREE.SphereGeometry(0.42, 32, 18, 0, Math.PI);
    visorGeo.scale(0.86, 0.88, 0.88);
    const visorMat = new THREE.MeshBasicMaterial({ map: this.face.tex });
    this.visor = new THREE.Mesh(visorGeo, visorMat);
    this.visor.rotation.y = -Math.PI / 2;
    this.visor.position.set(0, 1.36, 0.04);
    this.botBody.add(this.visor);

    // 3. Cute Top Antenna & Glowing Beacon
    const stemGeo = new THREE.CylinderGeometry(0.016, 0.016, 0.2, 12);
    const stemMat = new THREE.MeshStandardMaterial({ color: '#94A3B8', metalness: 0.5, roughness: 0.3 });
    const stem = new THREE.Mesh(stemGeo, stemMat);
    stem.position.set(0, 1.88, 0);
    this.botBody.add(stem);

    const beaconGeo = new THREE.SphereGeometry(0.065, 16, 16);
    const beaconMat = new THREE.MeshBasicMaterial({ color: AMBER_GLOW });
    this.beacon = new THREE.Mesh(beaconGeo, beaconMat);
    this.beacon.position.set(0, 2.0, 0);
    this.botBody.add(this.beacon);

    // 4. Floating Side Fins / Wings
    const finGeo = new THREE.BoxGeometry(0.06, 0.22, 0.14);
    const finMat = new THREE.MeshStandardMaterial({ color: BOT_WHITE, roughness: 0.2 });
    this.finL = new THREE.Mesh(finGeo, finMat);
    this.finR = new THREE.Mesh(finGeo, finMat);
    this.finL.position.set(-0.46, 1.32, 0);
    this.finR.position.set(0.46, 1.32, 0);
    this.botBody.add(this.finL);
    this.botBody.add(this.finR);

    // 5. Holographic Hover Thruster Ring
    const ringGeo = new THREE.TorusGeometry(0.24, 0.022, 16, 32);
    const ringMat = new THREE.MeshBasicMaterial({ color: CYAN_GLOW });
    this.ring = new THREE.Mesh(ringGeo, ringMat);
    this.ring.rotation.x = Math.PI / 2;
    this.ring.position.set(0, 0.88, 0);
    this.botBody.add(this.ring);

    this.st = { mood: 'neutral', talk: 0, blink: 0 };
    renderBotFace(this.face, this.st);
  }

  set(st = {}, t = 0) {
    this.update(t, st);
  }

  update(t, st = {}) {
    this.st = Object.assign(this.st, st);
    renderBotFace(this.face, this.st);

    // Smooth floating bob physics
    const bob = Math.sin(t * 2.8) * 0.045;
    this.botBody.position.y = bob;
    this.botBody.rotation.z = Math.sin(t * 1.5) * 0.035;

    // Wing flutter on speech
    if (this.st.talk > 0.1) {
      this.finL.rotation.z = Math.sin(t * 8) * 0.2;
      this.finR.rotation.z = -Math.sin(t * 8) * 0.2;
    }
  }
}

// Aliases for seamless drop-in camera & shot integration:
export const ClaudeBot = DevGuy;
export const SkepticBot = MascotBot;
