// Dev-Studio Signature 3D Characters:
// 1. DevGuy: Stylized humanoid developer (clean Pixar/anime face with blush & catchlights, layered modern dark hair with front fringe, navy hoodie with hood ring & drawstrings, articulated arms holding smartphone).
// 2. MascotBot: Ultra-adorable floating AI mascot (glossy ceramic egg body, seamlessly integrated curved OLED visor with glowing cyan capsule eyes, expressive flipper wings, pulsing amber antenna, cyan hover thruster).
import * as THREE from 'three';

const SKIN_TONE = '#FCE0CE';     // Healthy warm stylized human skin
const HOODIE_BLUE = '#1E293B';   // Deep slate navy
const HOODIE_STRING = '#F8FAFC';
const HAIR_DARK = '#1C1917';     // Rich deep espresso black
const HAIR_HILIGHT = '#2E2622';
const BOT_WHITE = '#FFFFFF';
const CYAN_GLOW = '#00F0FF';
const CYAN_SOFT = '#70F6FF';
const AMBER_GLOW = '#F59E0B';

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

  // Clear skin canvas with soft warm gradient
  const grad = ctx.createRadialGradient(256, 256, 40, 256, 256, 260);
  grad.addColorStop(0, SKIN_TONE);
  grad.addColorStop(1, '#F5D2BD');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 512, 512);

  const leftX = 168 + lookX * 16;
  const rightX = 344 + lookX * 16;
  const eyeY = 224 + lookY * 10;

  // Soft Rosy Cheeks (Blush)
  ctx.fillStyle = 'rgba(235, 120, 110, 0.28)';
  ctx.beginPath();
  ctx.ellipse(leftX - 8, eyeY + 54, 32, 16, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.ellipse(rightX + 8, eyeY + 54, 32, 16, 0, 0, Math.PI * 2);
  ctx.fill();

  // Eyebrows
  ctx.strokeStyle = HAIR_DARK;
  ctx.lineWidth = 11;
  ctx.lineCap = 'round';
  ctx.beginPath();
  if (mood === 'skeptical' || mood === 'doubt') {
    // Left raised curious, right furrowed
    ctx.moveTo(leftX - 32, eyeY - 58);
    ctx.quadraticCurveTo(leftX, eyeY - 74, leftX + 32, eyeY - 54);
    ctx.moveTo(rightX - 32, eyeY - 44);
    ctx.quadraticCurveTo(rightX, eyeY - 38, rightX + 32, eyeY - 48);
  } else if (mood === 'shock' || mood === 'amazed') {
    // Both high arched
    ctx.moveTo(leftX - 32, eyeY - 68);
    ctx.quadraticCurveTo(leftX, eyeY - 82, leftX + 32, eyeY - 66);
    ctx.moveTo(rightX - 32, eyeY - 68);
    ctx.quadraticCurveTo(rightX, eyeY - 82, rightX + 32, eyeY - 66);
  } else {
    // Confident, relaxed friendly arch
    ctx.moveTo(leftX - 32, eyeY - 48);
    ctx.quadraticCurveTo(leftX, eyeY - 56, leftX + 32, eyeY - 46);
    ctx.moveTo(rightX - 32, eyeY - 46);
    ctx.quadraticCurveTo(rightX, eyeY - 56, rightX + 32, eyeY - 48);
  }
  ctx.stroke();

  // Eyes
  if (blink > 0.4) {
    // Blinking soft curved eyelids
    ctx.strokeStyle = '#2B1810';
    ctx.lineWidth = 8;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(leftX - 28, eyeY + 2);
    ctx.quadraticCurveTo(leftX, eyeY + 16, leftX + 28, eyeY + 2);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(rightX - 28, eyeY + 2);
    ctx.quadraticCurveTo(rightX, eyeY + 16, rightX + 28, eyeY + 2);
    ctx.stroke();
  } else {
    // Upper eyelid shadow crease
    ctx.strokeStyle = 'rgba(60, 25, 15, 0.22)';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.arc(leftX, eyeY - 8, 30, Math.PI * 1.15, Math.PI * 1.85);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(rightX, eyeY - 8, 30, Math.PI * 1.15, Math.PI * 1.85);
    ctx.stroke();

    // Eye Whites (Almond shape)
    ctx.fillStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.ellipse(leftX, eyeY, 30, 24, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#2B1810';
    ctx.lineWidth = 3.5;
    ctx.stroke();

    ctx.beginPath();
    ctx.ellipse(rightX, eyeY, 30, 24, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Deep warm espresso iris
    const eyeIris = (cx, cy) => {
      const ig = ctx.createRadialGradient(cx, cy, 2, cx, cy, 18);
      ig.addColorStop(0, '#533526');
      ig.addColorStop(0.7, '#24160E');
      ig.addColorStop(1, '#150C07');
      ctx.fillStyle = ig;
      ctx.beginPath();
      ctx.arc(cx, cy, 17, 0, Math.PI * 2);
      ctx.fill();

      // Deep pupil
      ctx.fillStyle = '#080504';
      ctx.beginPath();
      ctx.arc(cx, cy, 8, 0, Math.PI * 2);
      ctx.fill();
    };
    eyeIris(leftX + lookX * 6, eyeY + lookY * 4);
    eyeIris(rightX + lookX * 6, eyeY + lookY * 4);

    // Clean catchlight highlight sparkles (No connecting lines)
    ctx.fillStyle = '#FFFFFF';
    const drawCatchlight = (cx, cy) => {
      ctx.beginPath();
      ctx.arc(cx - 5, cy - 5, 5.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(cx + 5, cy + 5, 2.5, 0, Math.PI * 2);
      ctx.fill();
    };
    drawCatchlight(leftX + lookX * 6, eyeY + lookY * 4);
    drawCatchlight(rightX + lookX * 6, eyeY + lookY * 4);
  }

  // Subtle cute nose
  ctx.fillStyle = '#E5A585';
  ctx.beginPath();
  ctx.arc(256, 308, 4.5, 0, Math.PI * 2);
  ctx.fill();

  // Expressive mouth with subtle lips
  const mouthY = 380;
  if (talk > 0.22) {
    const openH = Math.min(36, Math.max(12, talk * 36));
    ctx.fillStyle = '#4A151B';
    ctx.beginPath();
    ctx.roundRect(256 - 32, mouthY - openH / 2, 64, openH, openH / 2);
    ctx.fill();

    // Top teeth
    ctx.fillStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.roundRect(256 - 22, mouthY - openH / 2, 44, 9, 3);
    ctx.fill();

    // Tongue
    ctx.fillStyle = '#E06B78';
    ctx.beginPath();
    ctx.arc(256, mouthY + openH / 2 - 2, 16, 0, Math.PI);
    ctx.fill();
  } else {
    // Friendly subtle closed smile
    ctx.strokeStyle = '#5E2228';
    ctx.lineWidth = 5;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(256 - 28, mouthY - 4);
    ctx.quadraticCurveTo(256, mouthY + 8, 256 + 28, mouthY - 4);
    ctx.stroke();
  }

  tex.needsUpdate = true;
}

/** Dynamic OLED face texture generator for Cute Mascot Bot */
function makeBotFaceCanvas() {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 340;
  const ctx = canvas.getContext('2d');
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return { canvas, ctx, tex };
}

function renderBotFace(face, st) {
  const { ctx, tex } = face;
  const { mood = 'neutral', talk = 0, blink = 0, lookX = 0, lookY = 0 } = st;

  // Clear OLED screen with soft cyber glow gradient
  const bgGrad = ctx.createLinearGradient(0, 0, 0, 340);
  bgGrad.addColorStop(0, '#040711');
  bgGrad.addColorStop(1, '#08101E');
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, 512, 340);

  // Soft CRT horizontal scanline texture
  ctx.fillStyle = 'rgba(0, 240, 255, 0.025)';
  for (let y = 0; y < 340; y += 4) {
    ctx.fillRect(0, y, 512, 2);
  }

  const leftX = 160 + lookX * 18;
  const rightX = 352 + lookX * 18;
  const eyeY = 160 + lookY * 12;

  // Soft Pink LED Blush
  ctx.fillStyle = 'rgba(244, 114, 182, 0.35)';
  ctx.beginPath();
  ctx.arc(leftX - 16, eyeY + 48, 18, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.arc(rightX + 16, eyeY + 48, 18, 0, Math.PI * 2);
  ctx.fill();

  // Glowing Cyan LED Eyes
  ctx.fillStyle = CYAN_GLOW;
  ctx.shadowColor = CYAN_GLOW;
  ctx.shadowBlur = 18;

  if (blink > 0.45) {
    // Blinking horizontal LED slit (- -)
    ctx.fillRect(leftX - 32, eyeY - 4, 64, 8);
    ctx.fillRect(rightX - 32, eyeY - 4, 64, 8);
  } else if (mood === 'happy' || mood === 'laugh' || talk > 0.4) {
    // Happy curved crescents (^ ^)
    ctx.strokeStyle = CYAN_GLOW;
    ctx.lineWidth = 14;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.arc(leftX, eyeY + 12, 28, 1.15 * Math.PI, 1.85 * Math.PI);
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(rightX, eyeY + 12, 28, 1.15 * Math.PI, 1.85 * Math.PI);
    ctx.stroke();
  } else if (mood === 'shock' || mood === 'amazed') {
    // Wonder round glowing wide eyes (O O)
    ctx.beginPath();
    ctx.arc(leftX, eyeY, 40, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(rightX, eyeY, 40, 0, Math.PI * 2);
    ctx.fill();

    // Dark inner pupil
    ctx.fillStyle = '#060A14';
    ctx.beginPath();
    ctx.arc(leftX, eyeY, 16, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(rightX, eyeY, 16, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = CYAN_GLOW;
  } else {
    // Cute curved pill capsule eyes with upper soft curve
    ctx.beginPath();
    ctx.roundRect(leftX - 26, eyeY - 36, 52, 72, 24);
    ctx.fill();
    ctx.beginPath();
    ctx.roundRect(rightX - 26, eyeY - 36, 52, 72, 24);
    ctx.fill();

    // Eye highlight gleam
    ctx.fillStyle = CYAN_SOFT;
    ctx.beginPath();
    ctx.arc(leftX - 6, eyeY - 14, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(rightX - 6, eyeY - 14, 8, 0, Math.PI * 2);
    ctx.fill();
  }

  // Animated LED smile / mouth
  if (talk > 0.15) {
    const mouthW = 36 + talk * 26;
    ctx.fillStyle = CYAN_GLOW;
    ctx.beginPath();
    ctx.roundRect(256 - mouthW / 2, 240, mouthW, 10, 5);
    ctx.fill();
  }

  ctx.shadowBlur = 0;
  tex.needsUpdate = true;
}

/** Human Developer 3D Model */
export class DevGuy {
  constructor() {
    this.group = new THREE.Group();
    this.face = makeHumanFaceCanvas();

    this.bodyGroup = new THREE.Group();
    this.group.add(this.bodyGroup);

    // 1. Torso: Tapered Ergonomic Navy Hoodie
    const torsoGeo = new THREE.CylinderGeometry(0.38, 0.42, 0.95, 24);
    torsoGeo.scale(1.15, 1.0, 0.72); // Realistic human chest depth
    const hoodieMat = new THREE.MeshStandardMaterial({
      color: HOODIE_BLUE,
      roughness: 0.65,
      metalness: 0.05
    });
    this.torso = new THREE.Mesh(torsoGeo, hoodieMat);
    this.torso.position.y = 0.82;
    this.torso.castShadow = true;
    this.bodyGroup.add(this.torso);

    // Puffy Hoodie Collar / Folded Hood Ring around neck
    const collarGeo = new THREE.TorusGeometry(0.22, 0.075, 16, 24);
    collarGeo.scale(1.1, 0.7, 1.0);
    const collarMesh = new THREE.Mesh(collarGeo, hoodieMat);
    collarMesh.rotation.x = Math.PI / 2;
    collarMesh.position.set(0, 1.30, -0.04);
    this.bodyGroup.add(collarMesh);

    // White Hoodie Drawstrings
    const stringGeo = new THREE.CylinderGeometry(0.012, 0.012, 0.34, 8);
    const stringMat = new THREE.MeshStandardMaterial({ color: HOODIE_STRING, roughness: 0.5 });
    const strL = new THREE.Mesh(stringGeo, stringMat);
    const strR = new THREE.Mesh(stringGeo, stringMat);
    strL.position.set(-0.11, 1.05, 0.26);
    strR.position.set(0.11, 1.05, 0.26);
    this.bodyGroup.add(strL);
    this.bodyGroup.add(strR);

    // 2. Sculpted Humanoid Head & Neck
    this.headGroup = new THREE.Group();
    this.headGroup.position.set(0, 1.68, 0);
    this.bodyGroup.add(this.headGroup);

    // Defined Neck
    const neckGeo = new THREE.CylinderGeometry(0.14, 0.16, 0.22, 20);
    const skinMat = new THREE.MeshStandardMaterial({ color: SKIN_TONE, roughness: 0.55 });
    const neckMesh = new THREE.Mesh(neckGeo, skinMat);
    neckMesh.position.set(0, -0.16, 0);
    this.headGroup.add(neckMesh);

    // Humanoid Head with Face Plate
    const headGeo = new THREE.BoxGeometry(0.54, 0.58, 0.52);
    const faceMat = new THREE.MeshBasicMaterial({ map: this.face.tex });
    // [right, left, top, bottom, front, back] -> front (+Z) has the expressive face canvas!
    const headMats = [skinMat, skinMat, skinMat, skinMat, faceMat, skinMat];
    this.headMesh = new THREE.Mesh(headGeo, headMats);
    this.headMesh.castShadow = true;
    this.headGroup.add(this.headMesh);

    // Cute Stylized Human Ears
    const earGeo = new THREE.CylinderGeometry(0.055, 0.055, 0.035, 16);
    const earL = new THREE.Mesh(earGeo, skinMat);
    const earR = new THREE.Mesh(earGeo, skinMat);
    earL.position.set(-0.29, 0.02, 0.02);
    earL.rotation.z = Math.PI / 2;
    earR.position.set(0.29, 0.02, 0.02);
    earR.rotation.z = Math.PI / 2;
    this.headGroup.add(earL);
    this.headGroup.add(earR);

    // Modern Styled Hair with Natural Side-Swept Fringe
    const hairMat = new THREE.MeshStandardMaterial({ color: HAIR_DARK, roughness: 0.8 });
    const hairTop = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.18, 0.56), hairMat);
    hairTop.position.set(0, 0.31, -0.02);
    this.headGroup.add(hairTop);

    const hairBack = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.48, 0.12), hairMat);
    hairBack.position.set(0, 0.08, -0.22);
    this.headGroup.add(hairBack);

    const hairSideL = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.36, 0.44), hairMat);
    const hairSideR = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.36, 0.44), hairMat);
    hairSideL.position.set(-0.28, 0.12, -0.06);
    hairSideR.position.set(0.28, 0.12, -0.06);
    this.headGroup.add(hairSideL);
    this.headGroup.add(hairSideR);

    // Sleek Natural Side-Swept Fringe Over Forehead
    const fringeGeo = new THREE.BoxGeometry(0.50, 0.10, 0.06);
    const fringeMat = new THREE.MeshStandardMaterial({ color: HAIR_HILIGHT, roughness: 0.75 });
    const hairFringe = new THREE.Mesh(fringeGeo, fringeMat);
    hairFringe.position.set(0.01, 0.25, 0.27);
    hairFringe.rotation.z = -0.06;
    this.headGroup.add(hairFringe);

    // 3. Human Arms & Hands
    const armMat = new THREE.MeshStandardMaterial({ color: HOODIE_BLUE, roughness: 0.65 });
    const armGeo = new THREE.CylinderGeometry(0.085, 0.075, 0.52, 16);

    // Left Arm (Resting naturally on desk)
    this.armL = new THREE.Mesh(armGeo, armMat);
    this.armL.position.set(-0.50, 0.86, 0.12);
    this.armL.rotation.set(0.55, 0, -0.22);
    this.armL.castShadow = true;
    this.bodyGroup.add(this.armL);

    // Right Arm (Holding phone up)
    this.armR = new THREE.Mesh(armGeo, armMat);
    this.armR.position.set(0.48, 0.88, 0.16);
    this.armR.rotation.set(0.72, 0, 0.25);
    this.armR.castShadow = true;
    this.bodyGroup.add(this.armR);

    // Stylized Smartphone in Hand
    this.phone = this._makePhone();
    this.phone.position.set(0.02, -0.26, 0.14);
    this.phone.rotation.x = -0.35;
    this.armR.add(this.phone);

    // Grounded Seated Base
    this.seatBase = new THREE.Mesh(
      new THREE.CylinderGeometry(0.36, 0.40, 0.35, 24),
      new THREE.MeshStandardMaterial({ color: '#0F172A', roughness: 0.7 })
    );
    this.seatBase.position.y = 0.18;
    this.group.add(this.seatBase);

    this.st = { mood: 'neutral', talk: 0, blink: 0 };
    renderHumanFace(this.face, this.st);
  }

  _makePhone() {
    const g = new THREE.Group();
    // Glass smartphone chassis
    const body = new THREE.Mesh(
      new THREE.BoxGeometry(0.16, 0.32, 0.016),
      new THREE.MeshStandardMaterial({ color: '#0F172A', metalness: 0.8, roughness: 0.2 })
    );
    g.add(body);
    // Glowing OLED Screen
    const screen = new THREE.Mesh(
      new THREE.PlaneGeometry(0.14, 0.29),
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

    // Natural human breathing sway
    const breath = Math.sin(t * 1.8) * 0.012;
    this.bodyGroup.position.y = breath;
    this.headGroup.rotation.y = (this.st.lookX || 0) * 0.22;
    this.headGroup.rotation.x = (this.st.lookY || 0) * 0.12;

    // Speech gesture
    if (this.st.talk > 0.1) {
      this.armR.rotation.x = 0.72 + Math.sin(t * 5.2) * 0.06;
    }
  }
}

/** Cute Floating Robot Mascot 3D Model */
export class MascotBot {
  constructor() {
    this.group = new THREE.Group();
    this.face = makeBotFaceCanvas();

    this.botBody = new THREE.Group();
    this.group.add(this.botBody);

    // 1. Ceramic Glossy White Body (Chubby adorable egg proportions)
    const bodyGeo = new THREE.SphereGeometry(0.44, 36, 32);
    bodyGeo.scale(0.90, 1.12, 0.90);
    const bodyMat = new THREE.MeshStandardMaterial({
      color: BOT_WHITE,
      roughness: 0.08,
      metalness: 0.06
    });
    this.bodyMesh = new THREE.Mesh(bodyGeo, bodyMat);
    this.bodyMesh.position.y = 1.35;
    this.bodyMesh.castShadow = true;
    this.botBody.add(this.bodyMesh);

    // 2. Glossy Curved Front OLED Visor (Placed proud at z=0.44 to prevent any body mesh intersection)
    const visorGeo = new THREE.PlaneGeometry(0.56, 0.36, 24, 16);
    const pos = visorGeo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const vx = pos.getX(i);
      pos.setZ(i, -Math.pow(vx, 2) * 0.32);
    }
    visorGeo.computeVertexNormals();

    const visorMat = new THREE.MeshBasicMaterial({ map: this.face.tex, transparent: true });
    this.visor = new THREE.Mesh(visorGeo, visorMat);
    this.visor.position.set(0, 1.40, 0.44);
    this.botBody.add(this.visor);

    // 3. Cute Top Antenna with Glowing Warm Amber Light
    const stemGeo = new THREE.CylinderGeometry(0.014, 0.016, 0.22, 12);
    const stemMat = new THREE.MeshStandardMaterial({ color: '#64748B', metalness: 0.6, roughness: 0.25 });
    this.stem = new THREE.Mesh(stemGeo, stemMat);
    this.stem.position.set(0, 1.94, 0);
    this.botBody.add(this.stem);

    const beaconGeo = new THREE.SphereGeometry(0.075, 20, 20);
    const beaconMat = new THREE.MeshBasicMaterial({ color: AMBER_GLOW });
    this.beacon = new THREE.Mesh(beaconGeo, beaconMat);
    this.beacon.position.set(0, 2.06, 0);
    this.botBody.add(this.beacon);

    // 4. Adorable Floating Flipper Wings
    const finGeo = new THREE.SphereGeometry(0.12, 16, 16);
    finGeo.scale(0.32, 1.7, 0.75);
    const finMat = new THREE.MeshStandardMaterial({ color: BOT_WHITE, roughness: 0.1 });
    this.finL = new THREE.Mesh(finGeo, finMat);
    this.finR = new THREE.Mesh(finGeo, finMat);
    this.finL.position.set(-0.46, 1.32, 0.02);
    this.finR.position.set(0.46, 1.32, 0.02);
    this.finL.rotation.z = 0.25;
    this.finR.rotation.z = -0.25;
    this.botBody.add(this.finL);
    this.botBody.add(this.finR);

    // 5. Cyan Holographic Hover Thruster Ring
    const ringGeo = new THREE.TorusGeometry(0.24, 0.024, 16, 32);
    const ringMat = new THREE.MeshBasicMaterial({ color: CYAN_GLOW });
    this.ring = new THREE.Mesh(ringGeo, ringMat);
    this.ring.rotation.x = Math.PI / 2;
    this.ring.position.set(0, 0.82, 0);
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

    // Cute physics floating bob & subtle tilt
    const bob = Math.sin(t * 2.8) * 0.045;
    const tilt = Math.sin(t * 2.1) * 0.035;
    this.botBody.position.y = bob;
    this.botBody.rotation.z = tilt;

    // Fluttering flipper wings (like an excited puppy/penguin)
    const flap = Math.sin(t * 3.8) * 0.14;
    this.finL.rotation.z = 0.25 + flap;
    this.finR.rotation.z = -0.25 - flap;

    // Glowing amber antenna pulse
    if (this.beacon) {
      const pulse = 0.85 + Math.sin(t * 4.5) * 0.15;
      this.beacon.scale.set(pulse, pulse, pulse);
    }
  }
}

// Aliases for drop-in shot compatibility
export const ClaudeBot = DevGuy;
export const SkepticBot = MascotBot;
