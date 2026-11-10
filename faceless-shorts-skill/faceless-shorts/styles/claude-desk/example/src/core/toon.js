// 3D Stylized Characters for Claude-Desk format:
// 1. ClaudeBot (Guide): Anthropic Coral Red cube character with glowing LED digital face.
// 2. SkepticBot (Skeptic): Cute soft pastel pink avatar with hair bow and expressive anime LED face.
import * as THREE from 'three';

const CLAUDE_RED = '#D95338';
const SKEPTIC_PINK = '#F4A7B9';
const BOW_MAGENTA = '#E84393';
const SCREEN_BG = '#12131C';

function makeFaceTexture(isClaude = true) {
  const c = document.createElement('canvas');
  c.width = 512;
  c.height = 512;
  const ctx = c.getContext('2d');
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return { canvas: c, ctx, tex, isClaude };
}

function updateFaceCanvas(face, { mood = 'neutral', talk = 0, blink = 0, look = [0, 0] }) {
  const { ctx, canvas, isClaude, tex } = face;
  ctx.fillStyle = SCREEN_BG;
  ctx.fillRect(0, 0, 512, 512);

  // Subtle screen scanlines
  ctx.fillStyle = 'rgba(255, 255, 255, 0.03)';
  for (let y = 0; y < 512; y += 8) {
    ctx.fillRect(0, y, 512, 2);
  }

  const eyeColor = isClaude ? '#00F0FF' : '#FFD1DC';
  const glowColor = isClaude ? 'rgba(0, 240, 255, 0.45)' : 'rgba(255, 105, 180, 0.5)';
  const [lx, ly] = look;

  ctx.shadowColor = glowColor;
  ctx.shadowBlur = 18;
  ctx.fillStyle = eyeColor;

  const eyeY = 210 + ly * 20;
  const leftX = 160 + lx * 25;
  const rightX = 352 + lx * 25;

  if (blink > 0.6) {
    // Blinking slit
    ctx.fillRect(leftX - 35, eyeY - 3, 70, 8);
    ctx.fillRect(rightX - 35, eyeY - 3, 70, 8);
  } else if (mood === 'shock') {
    // Wide shocked circles
    ctx.beginPath();
    ctx.arc(leftX, eyeY, 44, 0, Math.PI * 2);
    ctx.arc(rightX, eyeY, 44, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = SCREEN_BG;
    ctx.beginPath();
    ctx.arc(leftX + lx * 8, eyeY + ly * 8, 20, 0, Math.PI * 2);
    ctx.arc(rightX + lx * 8, eyeY + ly * 8, 20, 0, Math.PI * 2);
    ctx.fill();
  } else if (mood === 'skeptic') {
    // One raised eyebrow / squinting skeptic eye
    ctx.fillRect(leftX - 35, eyeY - 10, 70, 16);
    ctx.beginPath();
    ctx.arc(rightX, eyeY - 5, 32, 0, Math.PI * 2);
    ctx.fill();
  } else {
    // Normal friendly expressive digital eyes
    ctx.beginPath();
    ctx.roundRect(leftX - 32, eyeY - 26, 64, 52, 16);
    ctx.roundRect(rightX - 32, eyeY - 26, 64, 52, 16);
    ctx.fill();
  }

  // Mouth
  ctx.fillStyle = eyeColor;
  ctx.strokeStyle = eyeColor;
  ctx.lineWidth = 10;
  ctx.lineCap = 'round';
  const mouthY = 345;

  if (talk > 0.05) {
    const mouthH = Math.min(65, talk * 55 + 10);
    ctx.beginPath();
    ctx.roundRect(256 - 45, mouthY - mouthH / 2, 90, mouthH, mouthH / 2);
    ctx.fill();
  } else {
    // Neutral smile
    ctx.beginPath();
    ctx.arc(256, mouthY - 10, 32, 0.2 * Math.PI, 0.8 * Math.PI);
    ctx.stroke();
  }

  ctx.shadowBlur = 0;
  tex.needsUpdate = true;
}

export class ClaudeBot {
  constructor() {
    this.group = new THREE.Group();
    this.face = makeFaceTexture(true);

    // Torso (rounded coral box)
    const bodyMat = new THREE.MeshStandardMaterial({
      color: CLAUDE_RED,
      roughness: 0.35,
      metalness: 0.1
    });
    const bodyGeo = new THREE.BoxGeometry(1.2, 1.4, 0.9);
    this.torso = new THREE.Mesh(bodyGeo, bodyMat);
    this.torso.position.y = 1.0;
    this.torso.castShadow = true;
    this.group.add(this.torso);

    // Claude star badge on chest
    const starTex = this._makeStarTexture();
    const starMat = new THREE.MeshBasicMaterial({ map: starTex, transparent: true });
    const starMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.38, 0.38), starMat);
    starMesh.position.set(0, 1.25, 0.46);
    this.group.add(starMesh);

    // Head pivot
    this.headGroup = new THREE.Group();
    this.headGroup.position.set(0, 1.9, 0);
    this.group.add(this.headGroup);

    // Screen face material (front face) + coral red for other sides
    const screenMat = new THREE.MeshBasicMaterial({ map: this.face.tex });
    const headMats = [
      bodyMat, bodyMat, bodyMat, bodyMat, screenMat, bodyMat
    ];
    this.headMesh = new THREE.Mesh(new THREE.BoxGeometry(1.3, 1.15, 1.1), headMats);
    this.headMesh.position.y = 0.55;
    this.headMesh.castShadow = true;
    this.headGroup.add(this.headMesh);

    // Hands
    const handMat = new THREE.MeshStandardMaterial({ color: '#E8634A', roughness: 0.4 });
    this.handL = new THREE.Mesh(new THREE.SphereGeometry(0.2, 16, 16), handMat);
    this.handR = new THREE.Mesh(new THREE.SphereGeometry(0.2, 16, 16), handMat);
    this.handL.position.set(-0.85, 0.95, 0.35);
    this.handR.position.set(0.85, 0.95, 0.35);
    this.handL.castShadow = true;
    this.handR.castShadow = true;
    this.group.add(this.handL);
    this.group.add(this.handR);

    this.st = { mood: 'neutral', talk: 0, blink: 0, look: [0, 0] };
    updateFaceCanvas(this.face, this.st);
  }

  _makeStarTexture() {
    const c = document.createElement('canvas');
    c.width = 128;
    c.height = 128;
    const g = c.getContext('2d');
    g.fillStyle = '#FFFFFF';
    g.font = '900 110px Inter, sans-serif';
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    g.fillText('*', 64, 76);
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  }

  set(st) {
    Object.assign(this.st, st);
    updateFaceCanvas(this.face, this.st);

    // Subtle head tilt & talking bounce
    const t = performance.now() / 1000;
    if (this.st.talk > 0.1) {
      this.headGroup.position.y = 1.9 + Math.sin(t * 18) * 0.04 * this.st.talk;
      this.headGroup.rotation.z = Math.sin(t * 9) * 0.05 * this.st.talk;
      this.headGroup.rotation.x = -0.05 + Math.sin(t * 14) * 0.04 * this.st.talk;
      this.handR.position.y = 0.95 + Math.sin(t * 12) * 0.08 * this.st.talk;
    } else {
      this.headGroup.position.y = 1.9 + Math.sin(t * 2) * 0.015;
      this.headGroup.rotation.set(0, 0, 0);
      this.handR.position.y = 0.95;
    }
  }
}

export class SkepticBot {
  constructor() {
    this.group = new THREE.Group();
    this.face = makeFaceTexture(false);

    // Torso (soft pastel pink)
    const bodyMat = new THREE.MeshStandardMaterial({
      color: SKEPTIC_PINK,
      roughness: 0.45,
      metalness: 0.05
    });
    this.torso = new THREE.Mesh(new THREE.BoxGeometry(1.05, 1.25, 0.8), bodyMat);
    this.torso.position.y = 0.9;
    this.torso.castShadow = true;
    this.group.add(this.torso);

    // Head pivot
    this.headGroup = new THREE.Group();
    this.headGroup.position.set(0, 1.7, 0);
    this.group.add(this.headGroup);

    // Head with screen face
    const screenMat = new THREE.MeshBasicMaterial({ map: this.face.tex });
    const headMats = [
      bodyMat, bodyMat, bodyMat, bodyMat, screenMat, bodyMat
    ];
    this.headMesh = new THREE.Mesh(new THREE.BoxGeometry(1.15, 1.05, 0.95), headMats);
    this.headMesh.position.y = 0.52;
    this.headMesh.castShadow = true;
    this.headGroup.add(this.headMesh);

    // Cute Magenta Bow on top-right of head
    const bowMat = new THREE.MeshStandardMaterial({ color: BOW_MAGENTA, roughness: 0.3 });
    const bowL = new THREE.Mesh(new THREE.ConeGeometry(0.18, 0.35, 16), bowMat);
    bowL.rotation.z = Math.PI / 2;
    bowL.position.set(0.42, 1.12, 0.15);
    const bowR = new THREE.Mesh(new THREE.ConeGeometry(0.18, 0.35, 16), bowMat);
    bowR.rotation.z = -Math.PI / 2;
    bowR.position.set(0.68, 1.12, 0.15);
    const knot = new THREE.Mesh(new THREE.SphereGeometry(0.1, 16, 16), bowMat);
    knot.position.set(0.55, 1.12, 0.15);
    this.headGroup.add(bowL);
    this.headGroup.add(bowR);
    this.headGroup.add(knot);

    // Hands
    const handMat = new THREE.MeshStandardMaterial({ color: '#FFB8C6', roughness: 0.4 });
    this.handL = new THREE.Mesh(new THREE.SphereGeometry(0.17, 16, 16), handMat);
    this.handR = new THREE.Mesh(new THREE.SphereGeometry(0.17, 16, 16), handMat);
    this.handL.position.set(-0.75, 0.85, 0.3);
    this.handR.position.set(0.75, 0.85, 0.3);
    this.handL.castShadow = true;
    this.handR.castShadow = true;
    this.group.add(this.handL);
    this.group.add(this.handR);

    this.st = { mood: 'skeptic', talk: 0, blink: 0, look: [0, 0] };
    updateFaceCanvas(this.face, this.st);
  }

  set(st) {
    Object.assign(this.st, st);
    updateFaceCanvas(this.face, this.st);

    const t = performance.now() / 1000;
    if (this.st.talk > 0.1) {
      this.headGroup.position.y = 1.7 + Math.sin(t * 18) * 0.04 * this.st.talk;
      this.headGroup.rotation.z = -0.06 + Math.sin(t * 8) * 0.05 * this.st.talk;
      this.headGroup.rotation.x = Math.sin(t * 14) * 0.03 * this.st.talk;
      this.handL.position.y = 0.85 + Math.sin(t * 11) * 0.07 * this.st.talk;
    } else {
      this.headGroup.position.y = 1.7 + Math.sin(t * 2 + 1) * 0.015;
      this.headGroup.rotation.set(0, 0, -0.06); // Cute curious resting head-tilt
      this.handL.position.y = 0.85;
    }
  }
}
