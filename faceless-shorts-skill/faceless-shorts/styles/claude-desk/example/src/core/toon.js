// CurioCut Signature 3D Animated Toons:
// 1. ClaudeBot: The authoritative AI Architect (Anthropic Coral Red voxel-curved cube, CRT animated face, 4 stubby walking legs, multi-action robotic arms with energy cutter & holographic stylus).
// 2. SkepticBot: The witty, doubting tech creator (Pastel pink voxel cube, animated anime-style expressive face, dynamic magenta bow, dynamic 3D reaction bubbles & emotive hands).
import * as THREE from 'three';

const CLAUDE_RED = '#D94D34';
const CLAUDE_DARK = '#7A2214';
const CLAUDE_NEON = '#FF6B4A';
const SKEPTIC_PINK = '#F48FB1';
const SKEPTIC_DARK = '#AD1457';
const BOW_MAGENTA = '#D81B60';
const CYAN_GLOW = '#00F0FF';

/** Procedural dynamic face texture generator for 3D toons */
function makeFaceCanvas(isClaude = true) {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return { canvas, ctx, tex, isClaude };
}

function renderFace(face, st) {
  const { ctx, isClaude, tex } = face;
  const { mood = 'neutral', talk = 0, blink = 0, lookX = 0, lookY = 0 } = st;

  // Background face plate
  ctx.fillStyle = isClaude ? CLAUDE_RED : SKEPTIC_PINK;
  ctx.fillRect(0, 0, 512, 512);

  const eyeColor = '#151322';
  const pupilGlow = '#FFFFFF';
  const leftX = 152 + lookX * 18;
  const rightX = 360 + lookX * 18;
  const eyeY = 224 + lookY * 12;

  // 1. EYES
  if (blink > 0.45) {
    // Blinking / closed eyes
    ctx.strokeStyle = eyeColor;
    ctx.lineWidth = 14;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(leftX - 36, eyeY + 12);
    ctx.quadraticCurveTo(leftX, eyeY + 22, leftX + 36, eyeY + 12);
    ctx.moveTo(rightX - 36, eyeY + 12);
    ctx.quadraticCurveTo(rightX, eyeY + 22, rightX + 36, eyeY + 12);
    ctx.stroke();
  } else if (mood === 'shock' || mood === 'amazed') {
    // Huge wide eyes with double shine
    ctx.fillStyle = eyeColor;
    ctx.beginPath();
    ctx.arc(leftX, eyeY, 52, 0, Math.PI * 2);
    ctx.arc(rightX, eyeY, 52, 0, Math.PI * 2);
    ctx.fill();

    // Dual anime highlight sparkles
    ctx.fillStyle = pupilGlow;
    ctx.beginPath();
    ctx.arc(leftX - 14, eyeY - 16, 18, 0, Math.PI * 2);
    ctx.arc(rightX - 14, eyeY - 16, 18, 0, Math.PI * 2);
    ctx.arc(leftX + 18, eyeY + 16, 9, 0, Math.PI * 2);
    ctx.arc(rightX + 18, eyeY + 16, 9, 0, Math.PI * 2);
    ctx.fill();

    // Eyebrows raised high
    ctx.strokeStyle = eyeColor;
    ctx.lineWidth = 14;
    ctx.beginPath();
    ctx.arc(leftX, eyeY - 62, 40, Math.PI * 1.15, Math.PI * 1.85);
    ctx.arc(rightX, eyeY - 62, 40, Math.PI * 1.15, Math.PI * 1.85);
    ctx.stroke();
  } else if (mood === 'skeptic' || mood === 'doubt') {
    // One squinted eye, one raised arched brow
    ctx.fillStyle = eyeColor;
    // Left squint
    ctx.fillRect(leftX - 38, eyeY - 4, 76, 24);
    // Right wide curious
    ctx.beginPath();
    ctx.arc(rightX, eyeY - 8, 40, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = pupilGlow;
    ctx.beginPath();
    ctx.arc(rightX - 12, eyeY - 18, 14, 0, Math.PI * 2);
    ctx.fill();

    // Skeptic angled brows
    ctx.strokeStyle = eyeColor;
    ctx.lineWidth = 14;
    ctx.beginPath();
    ctx.moveTo(leftX - 42, eyeY - 38);
    ctx.lineTo(leftX + 42, eyeY - 24);
    ctx.moveTo(rightX - 42, eyeY - 62);
    ctx.lineTo(rightX + 42, eyeY - 82);
    ctx.stroke();
  } else if (mood === 'smug' || mood === 'confident') {
    // Confident half-lidded eyes
    ctx.fillStyle = eyeColor;
    ctx.beginPath();
    ctx.roundRect(leftX - 36, eyeY - 12, 72, 48, 12);
    ctx.roundRect(rightX - 36, eyeY - 12, 72, 48, 12);
    ctx.fill();

    ctx.fillStyle = pupilGlow;
    ctx.fillRect(leftX - 22, eyeY + 2, 22, 22);
    ctx.fillRect(rightX - 22, eyeY + 2, 22, 22);

    // Smug tilted brows
    ctx.strokeStyle = eyeColor;
    ctx.lineWidth = 12;
    ctx.beginPath();
    ctx.moveTo(leftX - 38, eyeY - 42);
    ctx.lineTo(leftX + 38, eyeY - 50);
    ctx.moveTo(rightX - 38, eyeY - 50);
    ctx.lineTo(rightX + 38, eyeY - 42);
    ctx.stroke();
  } else {
    // Neutral friendly rounded eyes
    ctx.fillStyle = eyeColor;
    ctx.beginPath();
    ctx.roundRect(leftX - 34, eyeY - 30, 68, 60, 14);
    ctx.roundRect(rightX - 34, eyeY - 30, 68, 60, 14);
    ctx.fill();

    ctx.fillStyle = pupilGlow;
    ctx.fillRect(leftX - 22, eyeY - 20, 22, 22);
    ctx.fillRect(rightX - 22, eyeY - 20, 22, 22);
    ctx.fillRect(leftX + 10, eyeY + 8, 10, 10);
    ctx.fillRect(rightX + 10, eyeY + 8, 10, 10);

    // Friendly brows
    ctx.strokeStyle = eyeColor;
    ctx.lineWidth = 12;
    ctx.beginPath();
    ctx.moveTo(leftX - 34, eyeY - 54);
    ctx.lineTo(leftX + 34, eyeY - 54);
    ctx.moveTo(rightX - 34, eyeY - 54);
    ctx.lineTo(rightX + 34, eyeY - 54);
    ctx.stroke();
  }

  // Skeptic Eyelashes and Blush
  if (!isClaude && blink <= 0.45) {
    ctx.strokeStyle = eyeColor;
    ctx.lineWidth = 9;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(leftX - 30, eyeY - 30); ctx.lineTo(leftX - 48, eyeY - 52);
    ctx.moveTo(leftX + 2, eyeY - 36); ctx.lineTo(leftX + 2, eyeY - 60);
    ctx.moveTo(leftX + 30, eyeY - 30); ctx.lineTo(leftX + 48, eyeY - 50);
    ctx.moveTo(rightX - 30, eyeY - 30); ctx.lineTo(rightX - 48, eyeY - 50);
    ctx.moveTo(rightX - 2, eyeY - 36); ctx.lineTo(rightX - 2, eyeY - 60);
    ctx.moveTo(rightX + 30, eyeY - 30); ctx.lineTo(rightX + 48, eyeY - 52);
    ctx.stroke();

    // Cute rosy cheeks
    ctx.fillStyle = 'rgba(233, 30, 99, 0.35)';
    ctx.beginPath();
    ctx.ellipse(leftX - 24, eyeY + 68, 32, 16, -0.1, 0, Math.PI * 2);
    ctx.ellipse(rightX + 24, eyeY + 68, 32, 16, 0.1, 0, Math.PI * 2);
    ctx.fill();
  }

  // 2. MOUTH (Audio-Reactive Synced)
  const mouthY = 372;
  const mouthOpen = Math.min(74, talk * 72);

  if (isClaude) {
    if (talk > 0.08) {
      ctx.fillStyle = '#100E1C';
      ctx.beginPath();
      ctx.roundRect(256 - 56, mouthY - mouthOpen / 2, 112, mouthOpen, 12);
      ctx.fill();

      // Sharp white teeth row
      ctx.fillStyle = '#FFFFFF';
      for (let tx = 256 - 46; tx <= 256 + 34; tx += 20) {
        ctx.fillRect(tx, mouthY - mouthOpen / 2 + 2, 16, Math.min(24, mouthOpen * 0.45));
      }
    } else {
      // Confident smirk
      ctx.fillStyle = '#FFFFFF';
      ctx.fillRect(256 - 46, mouthY - 10, 92, 22);
      ctx.strokeStyle = eyeColor;
      ctx.lineWidth = 6;
      ctx.strokeRect(256 - 46, mouthY - 10, 92, 22);
      for (let tx = 256 - 24; tx <= 256 + 24; tx += 22) {
        ctx.beginPath();
        ctx.moveTo(tx, mouthY - 10);
        ctx.lineTo(tx, mouthY + 12);
        ctx.stroke();
      }
    }
  } else {
    if (talk > 0.08) {
      ctx.fillStyle = '#4A0E24';
      ctx.beginPath();
      ctx.roundRect(256 - 44, mouthY - mouthOpen / 2, 88, mouthOpen, mouthOpen / 2);
      ctx.fill();
      ctx.fillStyle = '#FF4081';
      ctx.beginPath();
      ctx.arc(256, mouthY + mouthOpen / 2 - 4, 26, Math.PI, 0);
      ctx.fill();
    } else {
      ctx.strokeStyle = '#4A0E24';
      ctx.lineWidth = 11;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.arc(256, mouthY - 8, 28, 0.15 * Math.PI, 0.85 * Math.PI);
      ctx.stroke();
    }
  }

  tex.needsUpdate = true;
}

export class ClaudeBot {
  constructor() {
    this.group = new THREE.Group();
    this.face = makeFaceCanvas(true);

    this.bodyGroup = new THREE.Group();
    this.group.add(this.bodyGroup);

    // Beveled Main Cube Body
    const bodyGeo = new THREE.BoxGeometry(1.0, 1.0, 1.0);
    const bodyMat = new THREE.MeshStandardMaterial({
      color: CLAUDE_RED,
      roughness: 0.32,
      metalness: 0.12
    });
    const faceMat = new THREE.MeshBasicMaterial({ map: this.face.tex });
    const mats = [bodyMat, bodyMat, bodyMat, bodyMat, faceMat, bodyMat];
    this.body = new THREE.Mesh(bodyGeo, mats);
    this.body.position.y = 0.75;
    this.body.castShadow = true;
    this.bodyGroup.add(this.body);

    // Holographic Cyber Antenna on Top
    const antStem = new THREE.Mesh(
      new THREE.CylinderGeometry(0.02, 0.02, 0.3, 12),
      new THREE.MeshStandardMaterial({ color: CLAUDE_DARK, roughness: 0.4 })
    );
    antStem.position.set(0, 1.38, 0);
    this.bodyGroup.add(antStem);

    const antBeacon = new THREE.Mesh(
      new THREE.SphereGeometry(0.08, 16, 16),
      new THREE.MeshBasicMaterial({ color: CYAN_GLOW })
    );
    antBeacon.position.set(0, 1.55, 0);
    this.bodyGroup.add(antBeacon);
    this.antBeacon = antBeacon;

    // Glowing Claude Star Badge on Chest
    const starTex = this._makeStarTexture();
    const starMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(0.24, 0.24),
      new THREE.MeshBasicMaterial({ map: starTex, transparent: true })
    );
    starMesh.position.set(-0.34, 1.1, 0.51);
    this.bodyGroup.add(starMesh);

    // 4 Walking Stubby Legs
    const legGeo = new THREE.BoxGeometry(0.22, 0.38, 0.22);
    const legMat = new THREE.MeshStandardMaterial({ color: CLAUDE_DARK, roughness: 0.45 });
    this.legs = [
      new THREE.Mesh(legGeo, legMat), // FL
      new THREE.Mesh(legGeo, legMat), // FR
      new THREE.Mesh(legGeo, legMat), // BL
      new THREE.Mesh(legGeo, legMat), // BR
    ];
    this.legs[0].position.set(-0.34, 0.19, 0.3);
    this.legs[1].position.set(0.34, 0.19, 0.3);
    this.legs[2].position.set(-0.34, 0.19, -0.3);
    this.legs[3].position.set(0.34, 0.19, -0.3);
    this.legs.forEach(l => { l.castShadow = true; this.group.add(l); });

    // Multi-Articulation Dynamic Arms
    const armGeo = new THREE.BoxGeometry(0.18, 0.42, 0.18);
    const armMat = new THREE.MeshStandardMaterial({ color: CLAUDE_RED, roughness: 0.35 });
    this.armL = new THREE.Mesh(armGeo, armMat);
    this.armR = new THREE.Mesh(armGeo, armMat);
    this.armL.position.set(-0.62, 0.74, 0.08);
    this.armR.position.set(0.62, 0.74, 0.08);
    this.armL.castShadow = true;
    this.armR.castShadow = true;
    this.bodyGroup.add(this.armL);
    this.bodyGroup.add(this.armR);

    // Dynamic Prop 1: Glowing Cyan Energy Laser Blade (for cost-cutting / breaking limits)
    this.laserBlade = this._makeLaserBlade();
    this.laserBlade.visible = false;
    this.armR.add(this.laserBlade);

    // Dynamic Prop 2: Holographic Stylus / Wand (for pointing & architecting)
    this.stylus = this._makeStylus();
    this.stylus.visible = true;
    this.armR.add(this.stylus);

    // Dynamic Prop 3: Floating Hologram Matrix Keyboard (when coding/installing)
    this.holoKeyboard = this._makeHoloKeyboard();
    this.holoKeyboard.visible = false;
    this.bodyGroup.add(this.holoKeyboard);

    this.st = { mood: 'neutral', talk: 0, blink: 0, action: 'idle' };
    renderFace(this.face, this.st);
  }

  _makeStarTexture() {
    const c = document.createElement('canvas');
    c.width = 128; c.height = 128;
    const g = c.getContext('2d');
    g.fillStyle = '#FFFFFF';
    g.font = '900 114px Inter, sans-serif';
    g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText('*', 64, 78);
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  }

  _makeLaserBlade() {
    const g = new THREE.Group();
    // Hilt
    const hilt = new THREE.Mesh(
      new THREE.CylinderGeometry(0.04, 0.04, 0.22, 16),
      new THREE.MeshStandardMaterial({ color: '#2B2B36', roughness: 0.3 })
    );
    hilt.position.set(0, -0.22, 0.12);
    hilt.rotation.x = Math.PI / 2.6;
    g.add(hilt);

    // Energy Blade (Glowing pure cyan)
    const blade = new THREE.Mesh(
      new THREE.BoxGeometry(0.05, 0.85, 0.015),
      new THREE.MeshBasicMaterial({ color: CYAN_GLOW })
    );
    blade.position.set(0, 0.35, 0);
    hilt.add(blade);
    return g;
  }

  _makeStylus() {
    const cyl = new THREE.Mesh(
      new THREE.CylinderGeometry(0.02, 0.02, 0.42, 12),
      new THREE.MeshBasicMaterial({ color: CYAN_GLOW })
    );
    cyl.position.set(0, -0.2, 0.12);
    cyl.rotation.x = Math.PI / 3;
    return cyl;
  }

  _makeHoloKeyboard() {
    const c = document.createElement('canvas');
    c.width = 256; c.height = 128;
    const ctx = c.getContext('2d');
    ctx.fillStyle = 'rgba(0, 240, 255, 0.85)';
    ctx.roundRect(4, 4, 248, 120, 12);
    ctx.fill();
    ctx.fillStyle = '#0B101E';
    ctx.font = 'bold 20px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('⌨ CLAUDE CODE', 128, 48);
    ctx.fillText('> git clone --fast', 128, 86);
    const tex = new THREE.CanvasTexture(c);
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.45), new THREE.MeshBasicMaterial({ map: tex, transparent: true, opacity: 0.9 }));
    mesh.position.set(0, 0.45, 0.65);
    mesh.rotation.x = -Math.PI / 4;
    return mesh;
  }

  set(st, t = 0) {
    Object.assign(this.st, st);
    renderFace(this.face, this.st);

    const isTalking = this.st.talk > 0.05;
    const animSpeed = isTalking ? 9.5 : 4.0;
    const walkAmt = isTalking ? 0.75 : 0.2;
    const action = this.st.action || 'idle';

    // Antenna pulse
    if (this.antBeacon) {
      this.antBeacon.scale.setScalar(1 + Math.sin(t * 8) * 0.25);
    }

    // Waddling leg physics
    this.legs[0].position.y = 0.19 + Math.max(0, Math.sin(t * animSpeed)) * 0.1 * walkAmt;
    this.legs[1].position.y = 0.19 + Math.max(0, Math.sin(t * animSpeed + Math.PI)) * 0.1 * walkAmt;
    this.legs[2].position.y = 0.19 + Math.max(0, Math.sin(t * animSpeed + Math.PI)) * 0.1 * walkAmt;
    this.legs[3].position.y = 0.19 + Math.max(0, Math.sin(t * animSpeed)) * 0.1 * walkAmt;

    // Rhythmic body bounce
    this.bodyGroup.position.y = Math.sin(t * animSpeed * 2) * 0.038 * walkAmt;
    this.bodyGroup.rotation.z = Math.sin(t * animSpeed) * 0.045 * walkAmt;

    // Dynamic Action Choreography
    if (action === 'slash' || action === 'cut') {
      this.laserBlade.visible = true;
      this.stylus.visible = false;
      this.holoKeyboard.visible = false;
      // High-energy dramatic sword chop gesture
      const chop = Math.sin(t * 7);
      this.armR.rotation.set(-1.4 + chop * 0.9, 0.2, -0.4);
      this.armL.rotation.set(-0.2, 0, 0.35);
    } else if (action === 'code' || action === 'type') {
      this.laserBlade.visible = false;
      this.stylus.visible = false;
      this.holoKeyboard.visible = true;
      // Cyber hacker air-typing
      this.armR.rotation.set(-0.6 + Math.sin(t * 22) * 0.18, 0.15, -0.2);
      this.armL.rotation.set(-0.6 + Math.cos(t * 22) * 0.18, -0.15, 0.2);
    } else if (action === 'point' || isTalking) {
      this.laserBlade.visible = false;
      this.stylus.visible = true;
      this.holoKeyboard.visible = false;
      // Confident tech guide pointing at 3D props
      this.armR.rotation.x = -0.65 + Math.sin(t * 11) * 0.32;
      this.armR.rotation.z = -0.28 + Math.sin(t * 7) * 0.16;
      this.armL.rotation.x = -0.25 + Math.cos(t * 9) * 0.14;
    } else {
      this.laserBlade.visible = false;
      this.stylus.visible = true;
      this.holoKeyboard.visible = false;
      this.armR.rotation.set(0, 0, -0.12);
      this.armL.rotation.set(0, 0, 0.12);
    }
  }
}

export class SkepticBot {
  constructor() {
    this.group = new THREE.Group();
    this.face = makeFaceCanvas(false);

    this.bodyGroup = new THREE.Group();
    this.group.add(this.bodyGroup);

    // Beveled Main Cube Body
    const bodyGeo = new THREE.BoxGeometry(0.94, 0.94, 0.94);
    const bodyMat = new THREE.MeshStandardMaterial({
      color: SKEPTIC_PINK,
      roughness: 0.42,
      metalness: 0.05
    });
    const faceMat = new THREE.MeshBasicMaterial({ map: this.face.tex });
    const mats = [bodyMat, bodyMat, bodyMat, bodyMat, faceMat, bodyMat];
    this.body = new THREE.Mesh(bodyGeo, mats);
    this.body.position.y = 0.72;
    this.body.castShadow = true;
    this.bodyGroup.add(this.body);

    // Magenta Ribbon Bow on Top
    this.bow = this._makeBow();
    this.bow.position.set(0.24, 1.24, 0.12);
    this.bodyGroup.add(this.bow);

    // 4 Walking Stubby Legs
    const legGeo = new THREE.BoxGeometry(0.2, 0.35, 0.2);
    const legMat = new THREE.MeshStandardMaterial({ color: SKEPTIC_DARK, roughness: 0.5 });
    this.legs = [
      new THREE.Mesh(legGeo, legMat),
      new THREE.Mesh(legGeo, legMat),
      new THREE.Mesh(legGeo, legMat),
      new THREE.Mesh(legGeo, legMat),
    ];
    this.legs[0].position.set(-0.32, 0.175, 0.28);
    this.legs[1].position.set(0.32, 0.175, 0.28);
    this.legs[2].position.set(-0.32, 0.175, -0.28);
    this.legs[3].position.set(0.32, 0.175, -0.28);
    this.legs.forEach(l => { l.castShadow = true; this.group.add(l); });

    // Emotive Arms
    const armGeo = new THREE.BoxGeometry(0.17, 0.38, 0.17);
    const armMat = new THREE.MeshStandardMaterial({ color: SKEPTIC_PINK, roughness: 0.45 });
    this.armL = new THREE.Mesh(armGeo, armMat);
    this.armR = new THREE.Mesh(armGeo, armMat);
    this.armL.position.set(-0.58, 0.72, 0.08);
    this.armR.position.set(0.58, 0.72, 0.08);
    this.armL.castShadow = true;
    this.armR.castShadow = true;
    this.bodyGroup.add(this.armL);
    this.bodyGroup.add(this.armR);

    // Dynamic 3D Reaction Bubbles (Pop up dynamically per emotion)
    this.bubbleShock = this._makeReactionPill('?!', '#FF3D71');
    this.bubbleDoubt = this._makeReactionPill('CAP?', '#FF9F1C');
    this.bubbleMoney = this._makeReactionPill('$$$?', '#2EC4B6');
    this.bodyGroup.add(this.bubbleShock);
    this.bodyGroup.add(this.bubbleDoubt);
    this.bodyGroup.add(this.bubbleMoney);

    this.st = { mood: 'neutral', talk: 0, blink: 0, action: 'idle' };
    renderFace(this.face, this.st);
  }

  _makeBow() {
    const g = new THREE.Group();
    const bowMat = new THREE.MeshStandardMaterial({ color: BOW_MAGENTA, roughness: 0.25 });
    const wingL = new THREE.Mesh(new THREE.ConeGeometry(0.15, 0.3, 16), bowMat);
    wingL.rotation.z = Math.PI / 2;
    wingL.position.x = -0.14;
    g.add(wingL);
    const wingR = new THREE.Mesh(new THREE.ConeGeometry(0.15, 0.3, 16), bowMat);
    wingR.rotation.z = -Math.PI / 2;
    wingR.position.x = 0.14;
    g.add(wingR);
    const knot = new THREE.Mesh(new THREE.SphereGeometry(0.09, 16, 16), bowMat);
    g.add(knot);
    return g;
  }

  _makeReactionPill(text, bg) {
    const c = document.createElement('canvas');
    c.width = 160; c.height = 160;
    const ctx = c.getContext('2d');
    ctx.fillStyle = bg;
    ctx.beginPath();
    ctx.arc(80, 80, 72, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '900 68px Inter, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(text, 80, 84);
    const tex = new THREE.CanvasTexture(c);
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(0.48, 0.48), new THREE.MeshBasicMaterial({ map: tex, transparent: true }));
    mesh.position.set(0.42, 1.58, 0.2);
    mesh.visible = false;
    return mesh;
  }

  set(st, t = 0) {
    Object.assign(this.st, st);
    renderFace(this.face, this.st);

    const isTalking = this.st.talk > 0.05;
    const animSpeed = isTalking ? 9.5 : 4.0;
    const walkAmt = isTalking ? 0.75 : 0.2;
    const mood = this.st.mood || 'neutral';

    // Walking leg cycle
    this.legs[0].position.y = 0.175 + Math.max(0, Math.sin(t * animSpeed)) * 0.09 * walkAmt;
    this.legs[1].position.y = 0.175 + Math.max(0, Math.sin(t * animSpeed + Math.PI)) * 0.09 * walkAmt;
    this.legs[2].position.y = 0.175 + Math.max(0, Math.sin(t * animSpeed + Math.PI)) * 0.09 * walkAmt;
    this.legs[3].position.y = 0.175 + Math.max(0, Math.sin(t * animSpeed)) * 0.09 * walkAmt;

    this.bodyGroup.position.y = Math.sin(t * animSpeed * 2) * 0.032 * walkAmt;
    this.bodyGroup.rotation.z = (mood === 'skeptic' ? -0.07 : 0) + Math.sin(t * animSpeed) * 0.04 * walkAmt;
    this.bow.rotation.z = Math.sin(t * 12) * 0.09 * walkAmt;

    // Hide all reaction bubbles by default
    this.bubbleShock.visible = false;
    this.bubbleDoubt.visible = false;
    this.bubbleMoney.visible = false;

    // Emotive Reacting Arms & Reaction Bubbles
    if (mood === 'shock' || mood === 'amazed') {
      this.bubbleShock.visible = true;
      this.bubbleShock.position.y = 1.58 + Math.sin(t * 6) * 0.06;
      this.bubbleShock.rotation.z = Math.sin(t * 4) * 0.12;
      // Hands thrown up in disbelief
      this.armL.rotation.set(-1.2 + Math.sin(t * 8) * 0.15, 0, 0.5);
      this.armR.rotation.set(-1.2 + Math.sin(t * 8) * 0.15, 0, -0.5);
    } else if (mood === 'skeptic' || mood === 'doubt') {
      this.bubbleDoubt.visible = true;
      this.bubbleDoubt.position.y = 1.58 + Math.sin(t * 5) * 0.05;
      // Hand on chin, one arm crossed
      this.armL.rotation.set(0.1, 0, 0.45 + Math.sin(t * 6) * 0.08);
      this.armR.rotation.set(-0.75 + Math.sin(t * 8) * 0.12, 0.2, -0.15);
    } else if (mood === 'money') {
      this.bubbleMoney.visible = true;
      this.bubbleMoney.position.y = 1.58 + Math.sin(t * 5) * 0.05;
      this.armL.rotation.set(-0.4, 0, 0.3);
      this.armR.rotation.set(-0.4, 0, -0.3);
    } else if (isTalking) {
      this.armL.rotation.set(-0.35 + Math.sin(t * 10) * 0.2, 0, 0.25);
      this.armR.rotation.set(-0.45 + Math.cos(t * 10) * 0.2, 0, -0.25);
    } else {
      this.armL.rotation.set(0, 0, 0.12);
      this.armR.rotation.set(0, 0, -0.12);
    }
  }
}
