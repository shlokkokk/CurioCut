// Dev-Studio Signature 3D Characters:
// 1. DevGuy: Stylized humanoid developer (tapered jawline, expressive anime/Pixar eyes with lash wing & dual catchlights, layered modern dark hair with sideburns & fringe, navy hoodie with drawstrings & collar, ergonomic high-back desk chair, arms naturally resting on desk & holding smartphone).
// 2. MascotBot: Adorable floating companion robot (glossy ceramic egg body, seamlessly integrated curved OLED visor with glowing cyan capsule eyes & pink LED blush, cyber-ear audio pucks, animated flipper paws, pulsing amber antenna, cyan hover thruster).
import * as THREE from 'three';

const SKIN_TONE = '#FCE0CE';     // Healthy warm stylized human skin
const SKIN_SHADOW = '#F2C2A8';   // Warm subsurface shadow
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

  // Clear canvas completely so the facial features overlay seamlessly onto the 3D skin cranium
  ctx.clearRect(0, 0, 512, 512);

  const leftX = 188 + lookX * 16;
  const rightX = 324 + lookX * 16;
  const eyeY = 224 + lookY * 10;

  // Soft Rosy Cheeks (Blush)
  ctx.fillStyle = 'rgba(238, 118, 128, 0.40)';
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
    ctx.moveTo(leftX - 32, eyeY - 60);
    ctx.quadraticCurveTo(leftX, eyeY - 76, leftX + 32, eyeY - 56);
    ctx.moveTo(rightX - 32, eyeY - 44);
    ctx.quadraticCurveTo(rightX, eyeY - 38, rightX + 32, eyeY - 48);
  } else if (mood === 'shock' || mood === 'amazed') {
    // Both high arched
    ctx.moveTo(leftX - 32, eyeY - 70);
    ctx.quadraticCurveTo(leftX, eyeY - 84, leftX + 32, eyeY - 68);
    ctx.moveTo(rightX - 32, eyeY - 70);
    ctx.quadraticCurveTo(rightX, eyeY - 84, rightX + 32, eyeY - 68);
  } else {
    // Confident, relaxed friendly arch
    ctx.moveTo(leftX - 32, eyeY - 50);
    ctx.quadraticCurveTo(leftX, eyeY - 58, leftX + 32, eyeY - 48);
    ctx.moveTo(rightX - 32, eyeY - 48);
    ctx.quadraticCurveTo(rightX, eyeY - 58, rightX + 32, eyeY - 50);
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
    ctx.strokeStyle = 'rgba(60, 25, 15, 0.28)';
    ctx.lineWidth = 3.5;
    ctx.beginPath();
    ctx.arc(leftX, eyeY - 8, 30, Math.PI * 1.15, Math.PI * 1.85);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(rightX, eyeY - 8, 30, Math.PI * 1.15, Math.PI * 1.85);
    ctx.stroke();

    // Eye Whites (Almond shape)
    ctx.fillStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.ellipse(leftX, eyeY, 34, 26, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#2B1810';
    ctx.lineWidth = 4;
    ctx.stroke();

    ctx.beginPath();
    ctx.ellipse(rightX, eyeY, 34, 26, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Stylized Upper Eyelash Wing
    ctx.strokeStyle = '#180E09';
    ctx.lineWidth = 5;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.arc(leftX, eyeY - 2, 33, Math.PI * 1.12, Math.PI * 1.88);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(rightX, eyeY - 2, 33, Math.PI * 1.12, Math.PI * 1.88);
    ctx.stroke();

    // Deep warm espresso iris
    const eyeIris = (cx, cy) => {
      const ig = ctx.createRadialGradient(cx, cy, 2, cx, cy, 21);
      ig.addColorStop(0, '#5A3827');
      ig.addColorStop(0.7, '#26170F');
      ig.addColorStop(1, '#150C07');
      ctx.fillStyle = ig;
      ctx.beginPath();
      ctx.arc(cx, cy, 20, 0, Math.PI * 2);
      ctx.fill();

      // Deep pupil
      ctx.fillStyle = '#080504';
      ctx.beginPath();
      ctx.arc(cx, cy, 10, 0, Math.PI * 2);
      ctx.fill();
    };
    eyeIris(leftX + lookX * 6, eyeY + lookY * 4);
    eyeIris(rightX + lookX * 6, eyeY + lookY * 4);

    // Clean catchlight highlight sparkles (No connecting lines)
    ctx.fillStyle = '#FFFFFF';
    const drawCatchlight = (cx, cy) => {
      ctx.beginPath();
      ctx.arc(cx - 6, cy - 6, 6.0, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(cx + 6, cy + 6, 3.0, 0, Math.PI * 2);
      ctx.fill();
    };
    drawCatchlight(leftX + lookX * 6, eyeY + lookY * 4);
    drawCatchlight(rightX + lookX * 6, eyeY + lookY * 4);
  }

  // Sculpted Nose (Subtle bridge shading + cute button tip)
  ctx.strokeStyle = 'rgba(210, 140, 110, 0.45)';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(254, 276);
  ctx.lineTo(254, 308);
  ctx.stroke();

  ctx.fillStyle = '#E29E7D';
  ctx.beginPath();
  ctx.arc(256, 312, 5, 0, Math.PI * 2);
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

  // Clear with transparency so only the rounded organic visor is visible
  ctx.clearRect(0, 0, 512, 340);

  // Smooth contoured elliptical OLED screen that fits inside the bezel
  const bgGrad = ctx.createRadialGradient(256, 170, 40, 256, 170, 230);
  bgGrad.addColorStop(0, '#0a1426');
  bgGrad.addColorStop(0.85, '#040711');
  bgGrad.addColorStop(1, '#02040a');
  ctx.fillStyle = bgGrad;
  ctx.beginPath();
  ctx.ellipse(256, 170, 230, 155, 0, 0, Math.PI * 2);
  ctx.fill();

  // Curved Glass Sheen Across Top-Right
  const sheen = ctx.createLinearGradient(0, 0, 512, 340);
  sheen.addColorStop(0, 'rgba(255, 255, 255, 0.18)');
  sheen.addColorStop(0.32, 'rgba(255, 255, 255, 0.03)');
  sheen.addColorStop(0.55, 'rgba(0, 0, 0, 0)');
  ctx.fillStyle = sheen;
  ctx.beginPath();
  ctx.ellipse(256, 170, 230, 155, 0, 0, Math.PI * 2);
  ctx.fill();

  // Soft CRT horizontal scanline texture clipped to visor ellipse
  ctx.save();
  ctx.beginPath();
  ctx.ellipse(256, 170, 230, 155, 0, 0, Math.PI * 2);
  ctx.clip();
  ctx.fillStyle = 'rgba(0, 240, 255, 0.025)';
  for (let y = 0; y < 340; y += 4) {
    ctx.fillRect(0, y, 512, 2);
  }
  ctx.restore();

  const leftX = 160 + lookX * 18;
  const rightX = 352 + lookX * 18;
  const eyeY = 160 + lookY * 12;

  // Soft Pink LED Blush
  ctx.fillStyle = 'rgba(244, 114, 182, 0.45)';
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

    // 0. Ergonomic Studio Office Chair (Behind character at -Z)
    const chairGroup = new THREE.Group();
    const chromeMat = new THREE.MeshStandardMaterial({ color: '#475569', metalness: 0.85, roughness: 0.2 });
    const meshMat = new THREE.MeshStandardMaterial({ color: '#0F172A', roughness: 0.8, metalness: 0.1 });

    // Caster Base + Hydraulic Cylinder
    const baseHub = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.08, 16), chromeMat);
    baseHub.position.set(0, 0.06, -0.06);
    chairGroup.add(baseHub);
    for (let i = 0; i < 5; i++) {
      const ang = (i * Math.PI * 2) / 5;
      const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.016, 0.36, 8), chromeMat);
      leg.rotation.z = Math.PI / 2;
      leg.rotation.y = ang;
      leg.position.set(Math.cos(ang) * 0.18, 0.06, -0.06 + Math.sin(ang) * 0.18);
      chairGroup.add(leg);
    }
    const cylinder = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.38, 16), chromeMat);
    cylinder.position.set(0, 0.25, -0.06);
    chairGroup.add(cylinder);

    // Sculpted Seat Cushion
    const seatGeo = new THREE.BoxGeometry(0.56, 0.09, 0.52);
    const seatCushion = new THREE.Mesh(seatGeo, meshMat);
    seatCushion.position.set(0, 0.44, -0.02);
    chairGroup.add(seatCushion);

    // High-back Ergonomic Spine Support & Mesh Backrest (Behind DevGuy at -Z, framing his silhouette)
    const backGeo = new THREE.BoxGeometry(0.50, 0.74, 0.06);
    const backMesh = new THREE.Mesh(backGeo, meshMat);
    backMesh.position.set(0, 0.88, -0.26);
    backMesh.rotation.x = 0.10;
    chairGroup.add(backMesh);

    // Adjustable Headrest behind neck
    const headrest = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.14, 0.07), meshMat);
    headrest.position.set(0, 1.34, -0.32);
    chairGroup.add(headrest);

    // Chair Armrests
    const chairArmGeo = new THREE.BoxGeometry(0.07, 0.035, 0.32);
    const chairArmL = new THREE.Mesh(chairArmGeo, meshMat);
    const chairArmR = new THREE.Mesh(chairArmGeo, meshMat);
    chairArmL.position.set(-0.31, 0.65, -0.02);
    chairArmR.position.set(0.31, 0.65, -0.02);
    chairGroup.add(chairArmL);
    chairGroup.add(chairArmR);

    this.group.add(chairGroup);

    // 1. Torso: Tapered Humanoid Navy Hoodie Seated Naturally on Chair Facing Camera (+Z)
    const torsoGeo = new THREE.CylinderGeometry(0.30, 0.36, 0.82, 24);
    torsoGeo.scale(1.15, 1.0, 0.76); // Natural human chest depth
    const hoodieMat = new THREE.MeshStandardMaterial({
      color: HOODIE_BLUE,
      roughness: 0.68,
      metalness: 0.04
    });
    this.torso = new THREE.Mesh(torsoGeo, hoodieMat);
    this.torso.position.y = 0.82;
    this.torso.castShadow = true;
    this.bodyGroup.add(this.torso);

    // Folded Hood Ring around neck
    const collarGeo = new THREE.TorusGeometry(0.20, 0.07, 16, 24);
    collarGeo.scale(1.1, 0.75, 1.0);
    const collarMesh = new THREE.Mesh(collarGeo, hoodieMat);
    collarMesh.rotation.x = Math.PI / 2;
    collarMesh.position.set(0, 1.22, 0.02);
    this.bodyGroup.add(collarMesh);

    // Draped Hood Volume on Upper Back (-Z)
    const hoodDrape = new THREE.Mesh(
      new THREE.SphereGeometry(0.22, 16, 16),
      hoodieMat
    );
    hoodDrape.scale.set(1.05, 0.6, 0.7);
    hoodDrape.position.set(0, 1.12, -0.16);
    this.bodyGroup.add(hoodDrape);

    // White Braided Hoodie Drawstrings on Front (+Z)
    const stringGeo = new THREE.CylinderGeometry(0.010, 0.010, 0.32, 8);
    const stringMat = new THREE.MeshStandardMaterial({ color: HOODIE_STRING, roughness: 0.5 });
    const strL = new THREE.Mesh(stringGeo, stringMat);
    const strR = new THREE.Mesh(stringGeo, stringMat);
    strL.position.set(-0.10, 1.02, 0.22);
    strR.position.set(0.10, 1.02, 0.22);
    this.bodyGroup.add(strL);
    this.bodyGroup.add(strR);

    // 2. Sculpted Humanoid Head & Neck Facing Camera (+Z)
    this.headGroup = new THREE.Group();
    this.headGroup.position.set(0, 1.54, 0);
    this.bodyGroup.add(this.headGroup);

    // Human Neck
    const neckGeo = new THREE.CylinderGeometry(0.12, 0.14, 0.22, 20);
    const skinMat = new THREE.MeshStandardMaterial({ color: SKIN_TONE, roughness: 0.55 });
    const neckMesh = new THREE.Mesh(neckGeo, skinMat);
    neckMesh.position.set(0, -0.16, 0);
    this.headGroup.add(neckMesh);

    // Humanoid Head Sculpt: Cranium (Sculpted with humanoid proportion)
    const craniumGeo = new THREE.SphereGeometry(0.25, 32, 24);
    craniumGeo.scale(0.88, 1.16, 0.94);
    const craniumMesh = new THREE.Mesh(craniumGeo, skinMat);
    craniumMesh.castShadow = true;
    this.headGroup.add(craniumMesh);

    // Tapered Jaw / Chin
    const jawGeo = new THREE.CylinderGeometry(0.16, 0.11, 0.22, 24);
    jawGeo.scale(1.0, 1.0, 0.82);
    const jawMesh = new THREE.Mesh(jawGeo, skinMat);
    jawMesh.position.set(0, -0.11, 0.04);
    this.headGroup.add(jawMesh);

    // Seamless Face Decal Mesh (Flush curved surface mapped to the dynamic 2D face)
    const faceGeo = new THREE.SphereGeometry(
      0.252, 32, 24,
      Math.PI * 0.175, Math.PI * 0.65,
      Math.PI * 0.20, Math.PI * 0.52
    );
    faceGeo.scale(0.882, 1.162, 0.942);
    const faceMat = new THREE.MeshBasicMaterial({
      map: this.face.tex,
      transparent: true,
      depthWrite: false
    });
    this.faceMesh = new THREE.Mesh(faceGeo, faceMat);
    this.faceMesh.position.set(0, 0, 0);
    this.headGroup.add(this.faceMesh);

    // Cute Stylized Human Ears on Sides
    const earGeo = new THREE.TorusGeometry(0.045, 0.016, 12, 16);
    const earL = new THREE.Mesh(earGeo, skinMat);
    const earR = new THREE.Mesh(earGeo, skinMat);
    earL.position.set(-0.22, -0.01, -0.02);
    earL.rotation.y = Math.PI / 2;
    earR.position.set(0.22, -0.01, -0.02);
    earR.rotation.y = -Math.PI / 2;
    this.headGroup.add(earL);
    this.headGroup.add(earR);

    // Modern Layered Haircut (Styled neatly above eyebrows)
    const hairMat = new THREE.MeshStandardMaterial({ color: HAIR_DARK, roughness: 0.8 });
    const hairCap = new THREE.Mesh(
      new THREE.SphereGeometry(0.262, 32, 24, 0, Math.PI * 2, 0, Math.PI * 0.38),
      hairMat
    );
    hairCap.scale.set(0.92, 1.18, 0.98);
    hairCap.position.set(0, 0.08, -0.02);
    this.headGroup.add(hairCap);

    // Natural Sculpted Hair Sideburns
    const sideburnGeo = new THREE.BoxGeometry(0.035, 0.14, 0.08);
    const sideburnL = new THREE.Mesh(sideburnGeo, hairMat);
    const sideburnR = new THREE.Mesh(sideburnGeo, hairMat);
    sideburnL.position.set(-0.22, 0.04, 0.03);
    sideburnR.position.set(0.22, 0.04, 0.03);
    this.headGroup.add(sideburnL);
    this.headGroup.add(sideburnR);

    // Natural Sculpted Hair Fringe Torus along Hairline
    const fringeMat = new THREE.MeshStandardMaterial({ color: HAIR_HILIGHT, roughness: 0.75 });
    const fringeTorus = new THREE.Mesh(
      new THREE.TorusGeometry(0.21, 0.036, 12, 24, Math.PI * 0.75),
      fringeMat
    );
    fringeTorus.rotation.set(0.32, 0, -Math.PI * 0.38);
    fringeTorus.position.set(0.01, 0.16, 0.08);
    this.headGroup.add(fringeTorus);

    // 3. Natural Arms & Hands (Extending forward +Z toward desk)
    const armMat = new THREE.MeshStandardMaterial({ color: HOODIE_BLUE, roughness: 0.68 });
    const armGeo = new THREE.CylinderGeometry(0.075, 0.065, 0.46, 16);

    // Left Arm (Forearm extending forward onto desk typing near laptop)
    this.armL = new THREE.Mesh(armGeo, armMat);
    this.armL.position.set(-0.38, 0.82, 0.16);
    this.armL.rotation.set(0.70, 0, -0.22);
    this.armL.castShadow = true;
    this.bodyGroup.add(this.armL);

    // Hand on desk
    const handL = new THREE.Mesh(new THREE.SphereGeometry(0.055, 12, 12), skinMat);
    handL.scale.set(1.0, 0.6, 1.4);
    handL.position.set(0, -0.24, 0.05);
    this.armL.add(handL);

    // Right Arm (Holding phone upright naturally facing camera)
    this.armR = new THREE.Mesh(armGeo, armMat);
    this.armR.position.set(0.36, 0.86, 0.18);
    this.armR.rotation.set(0.78, 0, 0.25);
    this.armR.castShadow = true;
    this.bodyGroup.add(this.armR);

    // Stylized Smartphone in Hand
    this.phone = this._makePhone();
    this.phone.position.set(0.02, -0.24, 0.08);
    this.phone.rotation.x = -0.45;
    this.armR.add(this.phone);

    this.st = { mood: 'neutral', talk: 0, blink: 0 };
    renderHumanFace(this.face, this.st);
  }

  _makePhone() {
    const g = new THREE.Group();
    // Glass smartphone chassis
    const body = new THREE.Mesh(
      new THREE.BoxGeometry(0.14, 0.28, 0.015),
      new THREE.MeshStandardMaterial({ color: '#0F172A', metalness: 0.85, roughness: 0.2 })
    );
    g.add(body);
    // Glowing OLED Screen (facing camera +Z)
    const screen = new THREE.Mesh(
      new THREE.PlaneGeometry(0.12, 0.25),
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
    const breath = Math.sin(t * 1.8) * 0.010;
    this.bodyGroup.position.y = breath;
    this.headGroup.rotation.y = (this.st.lookX || 0) * 0.20;
    this.headGroup.rotation.x = (this.st.lookY || 0) * 0.10;

    // Speech gesture
    if (this.st.talk > 0.1) {
      this.armR.rotation.x = 0.78 + Math.sin(t * 5.2) * 0.05;
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
    bodyGeo.scale(0.92, 1.12, 0.92);
    const bodyMat = new THREE.MeshStandardMaterial({
      color: BOT_WHITE,
      roughness: 0.08,
      metalness: 0.04
    });
    this.bodyMesh = new THREE.Mesh(bodyGeo, bodyMat);
    this.bodyMesh.position.y = 1.35;
    this.bodyMesh.castShadow = true;
    this.botBody.add(this.bodyMesh);

    // 2. Seamless Inset Curved OLED Visor (Curved spherical shell flush with egg surface)
    // Sized to fit precisely inside the dark metallic bezel ring
    const visorGeo = new THREE.SphereGeometry(
      0.442, 36, 24,
      Math.PI * 0.25, Math.PI * 0.50,
      Math.PI * 0.31, Math.PI * 0.38
    );
    visorGeo.scale(0.922, 1.122, 0.922);

    const visorMat = new THREE.MeshBasicMaterial({
      map: this.face.tex,
      transparent: true,
      depthWrite: false
    });
    this.visor = new THREE.Mesh(visorGeo, visorMat);
    this.visor.position.y = 1.35;
    this.botBody.add(this.visor);

    // Sleek Dark Gunmetal Bezel Trim around Visor Contour on +Z
    const bezelMat = new THREE.MeshStandardMaterial({
      color: '#0F172A',
      metalness: 0.85,
      roughness: 0.18
    });
    const bezelRing = new THREE.Mesh(new THREE.TorusGeometry(0.23, 0.016, 16, 32), bezelMat);
    bezelRing.scale.set(1.22, 0.92, 1.0);
    bezelRing.position.set(0, 1.35, 0.38);
    this.botBody.add(bezelRing);

    // 3. Cyber Headphone Audio Pucks on Sides (Ultra-cute companion styling)
    const puckMat = new THREE.MeshStandardMaterial({ color: '#1E293B', metalness: 0.7, roughness: 0.3 });
    const ringMat = new THREE.MeshBasicMaterial({ color: CYAN_GLOW });

    [-0.41, 0.41].forEach((px) => {
      const puck = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, 0.035, 24), puckMat);
      puck.rotation.z = Math.PI / 2;
      puck.position.set(px, 1.38, 0);
      this.botBody.add(puck);

      const lightRing = new THREE.Mesh(new THREE.TorusGeometry(0.065, 0.010, 16, 24), ringMat);
      lightRing.rotation.y = Math.PI / 2;
      lightRing.position.set(px > 0 ? px + 0.018 : px - 0.018, 1.38, 0);
      this.botBody.add(lightRing);
    });

    // 4. Cute Top Antenna with Glowing Warm Amber Light
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

    // 5. Adorable Floating Flipper Paws
    const finGeo = new THREE.SphereGeometry(0.12, 16, 16);
    finGeo.scale(0.35, 1.5, 0.75);
    const finMat = new THREE.MeshStandardMaterial({ color: BOT_WHITE, roughness: 0.1 });
    this.finL = new THREE.Mesh(finGeo, finMat);
    this.finR = new THREE.Mesh(finGeo, finMat);
    this.finL.position.set(-0.45, 1.28, 0.02);
    this.finR.position.set(0.45, 1.28, 0.02);
    this.finL.rotation.z = 0.22;
    this.finR.rotation.z = -0.22;
    this.botBody.add(this.finL);
    this.botBody.add(this.finR);

    // 6. Cyan Holographic Hover Thruster Ring
    const thrusterRing = new THREE.TorusGeometry(0.22, 0.022, 16, 32);
    this.ring = new THREE.Mesh(thrusterRing, ringMat);
    this.ring.rotation.x = Math.PI / 2;
    this.ring.position.set(0, 0.85, 0);
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

    // Fluttering flipper paws (like an excited puppy/penguin)
    const flap = Math.sin(t * 3.8) * 0.14;
    this.finL.rotation.z = 0.22 + flap;
    this.finR.rotation.z = -0.22 - flap;

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
