// CurioCut Signature Cinematic 3D Animated Toons for Claude-Desk:
// 1. ClaudeBot: Authoritative Anthropic Coral Red AI Architect (Curved voxel cube, expressive CRT face,
//    glowing antenna beacon, star badge, presenter hands with holographic stylus & floating code keyboard).
// 2. SkepticBot: Witty Tech Creator & Skeptic (Soft pastel pink voxel cube, gorgeous expressive anime eyes,
//    magenta ribbon bow, expressive reactive hands, blushing cheeks, floating reaction holocubes).
// Strictly ZERO random sword swinging. Top-tier expressive facial animation and movie-grade presence.
import * as THREE from 'three';

const CLAUDE_RED = '#D94D34';
const CLAUDE_DARK = '#7A2214';
const CLAUDE_NEON = '#FF6B4A';
const SKEPTIC_PINK = '#F48FB1';
const SKEPTIC_DARK = '#AD1457';
const BOW_MAGENTA = '#D81B60';
const CYAN_GLOW = '#00F0FF';
const GOLD = '#F5B041';

/** 1024x1024 High-Definition Procedural Face Texture Generator */
function makeFaceCanvas(isClaude = true) {
  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 1024;
  const ctx = canvas.getContext('2d');
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return { canvas, ctx, tex, isClaude };
}

function renderFace(face, st) {
  const { ctx, isClaude, tex } = face;
  const { mood = 'neutral', talk = 0, blink = 0, lookX = 0, lookY = 0 } = st;

  ctx.clearRect(0, 0, 1024, 1024);

  // Background face plate
  ctx.fillStyle = isClaude ? CLAUDE_RED : SKEPTIC_PINK;
  ctx.fillRect(0, 0, 1024, 1024);

  const eyeColor = '#10141E';
  const leftX = 310 + lookX * 36;
  const rightX = 714 + lookX * 36;
  const eyeY = 440 + lookY * 24;

  // ==========================================
  // 1. EXPRESSIVE HIGH-TIER EYES
  // ==========================================
  if (blink > 0.4) {
    // Smooth natural closed eyelid curves
    ctx.strokeStyle = eyeColor;
    ctx.lineWidth = 26;
    ctx.lineCap = 'round';

    ctx.beginPath();
    ctx.moveTo(leftX - 80, eyeY + 16);
    ctx.quadraticCurveTo(leftX, eyeY + 48, leftX + 80, eyeY + 16);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(rightX - 80, eyeY + 16);
    ctx.quadraticCurveTo(rightX, eyeY + 48, rightX + 80, eyeY + 16);
    ctx.stroke();
  } else if (mood === 'shock' || mood === 'amazed') {
    // Huge wide-eyed wonder with dual glowing anime sparkles
    ctx.fillStyle = eyeColor;
    ctx.beginPath();
    ctx.arc(leftX, eyeY, 110, 0, Math.PI * 2);
    ctx.arc(rightX, eyeY, 110, 0, Math.PI * 2);
    ctx.fill();

    // Iris accent glow
    ctx.fillStyle = isClaude ? 'rgba(0, 240, 255, 0.4)' : 'rgba(233, 30, 99, 0.45)';
    ctx.beginPath();
    ctx.arc(leftX, eyeY + 16, 85, 0, Math.PI * 2);
    ctx.arc(rightX, eyeY + 16, 85, 0, Math.PI * 2);
    ctx.fill();

    // Primary glossy specular shine
    ctx.fillStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.arc(leftX - 32, eyeY - 34, 40, 0, Math.PI * 2);
    ctx.arc(rightX - 32, eyeY - 34, 40, 0, Math.PI * 2);
    ctx.fill();

    // Secondary sparkle
    ctx.beginPath();
    ctx.arc(leftX + 42, eyeY + 36, 22, 0, Math.PI * 2);
    ctx.arc(rightX + 42, eyeY + 36, 22, 0, Math.PI * 2);
    ctx.fill();

    // Eyebrows raised high
    ctx.strokeStyle = eyeColor;
    ctx.lineWidth = 26;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.arc(leftX, eyeY - 130, 90, Math.PI * 1.15, Math.PI * 1.85);
    ctx.arc(rightX, eyeY - 130, 90, Math.PI * 1.15, Math.PI * 1.85);
    ctx.stroke();
  } else if (mood === 'skeptic' || mood === 'doubt') {
    // Smart skeptical expression: One eye charmingly squinted, one wide, one arched brow
    ctx.fillStyle = eyeColor;

    // Left squint
    ctx.beginPath();
    ctx.roundRect(leftX - 85, eyeY - 15, 170, 60, 28);
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(leftX - 45, eyeY - 5, 45, 40);

    // Right wide inquisitive
    ctx.fillStyle = eyeColor;
    ctx.beginPath();
    ctx.arc(rightX, eyeY - 10, 95, 0, Math.PI * 2);
    ctx.fill();

    // Iris glow
    ctx.fillStyle = isClaude ? 'rgba(0, 240, 255, 0.4)' : 'rgba(233, 30, 99, 0.45)';
    ctx.beginPath();
    ctx.arc(rightX, eyeY + 4, 70, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.arc(rightX - 26, eyeY - 38, 36, 0, Math.PI * 2);
    ctx.arc(rightX + 32, eyeY + 28, 18, 0, Math.PI * 2);
    ctx.fill();

    // Skeptic angled brows
    ctx.strokeStyle = eyeColor;
    ctx.lineWidth = 26;
    ctx.lineCap = 'round';
    ctx.beginPath();
    // Left lowered brow
    ctx.moveTo(leftX - 90, eyeY - 75);
    ctx.lineTo(leftX + 90, eyeY - 50);
    // Right arched questioning brow
    ctx.moveTo(rightX - 90, eyeY - 130);
    ctx.quadraticCurveTo(rightX, eyeY - 170, rightX + 90, eyeY - 120);
    ctx.stroke();
  } else if (mood === 'smug' || mood === 'confident') {
    // Confident, sharp presenter eyes
    ctx.fillStyle = eyeColor;
    ctx.beginPath();
    ctx.roundRect(leftX - 80, eyeY - 25, 160, 110, 32);
    ctx.roundRect(rightX - 80, eyeY - 25, 160, 110, 32);
    ctx.fill();

    // Cyan/magenta iris shine
    ctx.fillStyle = isClaude ? 'rgba(0, 240, 255, 0.5)' : 'rgba(233, 30, 99, 0.5)';
    ctx.beginPath();
    ctx.arc(leftX, eyeY + 24, 55, 0, Math.PI * 2);
    ctx.arc(rightX, eyeY + 24, 55, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(leftX - 52, eyeY + 8, 48, 48);
    ctx.fillRect(rightX - 52, eyeY + 8, 48, 48);

    // Confident stylish brows
    ctx.strokeStyle = eyeColor;
    ctx.lineWidth = 24;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(leftX - 85, eyeY - 80);
    ctx.lineTo(leftX + 85, eyeY - 100);
    ctx.moveTo(rightX - 85, eyeY - 100);
    ctx.lineTo(rightX + 85, eyeY - 80);
    ctx.stroke();
  } else {
    // Friendly, vibrant rounded eyes
    ctx.fillStyle = eyeColor;
    ctx.beginPath();
    ctx.roundRect(leftX - 78, eyeY - 65, 156, 138, 36);
    ctx.roundRect(rightX - 78, eyeY - 65, 156, 138, 36);
    ctx.fill();

    // Iris glow ring
    ctx.fillStyle = isClaude ? 'rgba(0, 240, 255, 0.35)' : 'rgba(233, 30, 99, 0.4)';
    ctx.beginPath();
    ctx.arc(leftX, eyeY + 16, 56, 0, Math.PI * 2);
    ctx.arc(rightX, eyeY + 16, 56, 0, Math.PI * 2);
    ctx.fill();

    // Double glossy shine
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(leftX - 52, eyeY - 45, 50, 50);
    ctx.fillRect(rightX - 52, eyeY - 45, 50, 50);
    ctx.fillRect(leftX + 22, eyeY + 18, 24, 24);
    ctx.fillRect(rightX + 22, eyeY + 18, 24, 24);

    // Friendly brows
    ctx.strokeStyle = eyeColor;
    ctx.lineWidth = 24;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(leftX - 75, eyeY - 110);
    ctx.lineTo(leftX + 75, eyeY - 110);
    ctx.moveTo(rightX - 75, eyeY - 110);
    ctx.lineTo(rightX + 75, eyeY - 110);
    ctx.stroke();
  }

  // Skeptic Eyelashes and Rosy Cheeks
  if (!isClaude && blink <= 0.4) {
    ctx.strokeStyle = eyeColor;
    ctx.lineWidth = 20;
    ctx.lineCap = 'round';
    ctx.beginPath();
    // Cute curved eyelashes above outer eyes
    ctx.moveTo(leftX - 65, eyeY - 65);
    ctx.quadraticCurveTo(leftX - 100, eyeY - 95, leftX - 110, eyeY - 115);
    ctx.moveTo(rightX + 65, eyeY - 65);
    ctx.quadraticCurveTo(rightX + 100, eyeY - 95, rightX + 110, eyeY - 115);
    ctx.stroke();

    // Soft glowing rosy cheeks
    const leftCheek = ctx.createRadialGradient(leftX - 60, eyeY + 140, 10, leftX - 60, eyeY + 140, 75);
    leftCheek.addColorStop(0, 'rgba(255, 40, 120, 0.65)');
    leftCheek.addColorStop(1, 'rgba(255, 40, 120, 0)');
    ctx.fillStyle = leftCheek;
    ctx.beginPath();
    ctx.arc(leftX - 60, eyeY + 140, 75, 0, Math.PI * 2);
    ctx.fill();

    const rightCheek = ctx.createRadialGradient(rightX + 60, eyeY + 140, 10, rightX + 60, eyeY + 140, 75);
    rightCheek.addColorStop(0, 'rgba(255, 40, 120, 0.65)');
    rightCheek.addColorStop(1, 'rgba(255, 40, 120, 0)');
    ctx.fillStyle = rightCheek;
    ctx.beginPath();
    ctx.arc(rightX + 60, eyeY + 140, 75, 0, Math.PI * 2);
    ctx.fill();
  }

  // ==========================================
  // 2. EXPRESSIVE ORGANIC MOUTH
  // ==========================================
  const mouthY = 740;
  const mouthOpen = Math.min(145, talk * 140);

  if (isClaude) {
    if (talk > 0.08) {
      // Clean, stylish open animated mouth with smooth teeth and tongue
      ctx.fillStyle = '#0F121C';
      ctx.beginPath();
      ctx.roundRect(512 - 120, mouthY - mouthOpen / 2, 240, mouthOpen, 26);
      ctx.fill();

      // Clean upper teeth line
      ctx.fillStyle = '#FFFFFF';
      ctx.beginPath();
      ctx.roundRect(512 - 95, mouthY - mouthOpen / 2 + 6, 190, Math.min(36, mouthOpen * 0.4), 8);
      ctx.fill();

      // Red/coral animated tongue
      ctx.fillStyle = '#FF5252';
      ctx.beginPath();
      ctx.arc(512, mouthY + mouthOpen / 2 - 4, Math.min(55, mouthOpen * 0.5), Math.PI, 0);
      ctx.fill();
    } else {
      // Confident, clean friendly smirk
      ctx.strokeStyle = eyeColor;
      ctx.lineWidth = 18;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(512 - 90, mouthY);
      ctx.quadraticCurveTo(512, mouthY + 36, 512 + 105, mouthY - 12);
      ctx.stroke();
    }
  } else {
    if (talk > 0.08) {
      // Expressive cute anime talking mouth
      ctx.fillStyle = '#3E0A1E';
      ctx.beginPath();
      ctx.roundRect(512 - 90, mouthY - mouthOpen / 2, 180, mouthOpen, mouthOpen / 2);
      ctx.fill();

      // Cute pink tongue
      ctx.fillStyle = '#FF4081';
      ctx.beginPath();
      ctx.arc(512, mouthY + mouthOpen / 2 - 6, Math.min(50, mouthOpen * 0.52), Math.PI, 0);
      ctx.fill();
    } else {
      // Cute smile curve
      ctx.strokeStyle = '#3E0A1E';
      ctx.lineWidth = 20;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.arc(512, mouthY - 14, 58, 0.18 * Math.PI, 0.82 * Math.PI);
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

    // Beveled Main Cube Body (High-grade materials with soft bevel)
    const bodyGeo = new THREE.BoxGeometry(1.0, 1.0, 1.0);
    const bodyMat = new THREE.MeshStandardMaterial({
      color: CLAUDE_RED,
      roughness: 0.28,
      metalness: 0.15
    });
    const faceMat = new THREE.MeshBasicMaterial({ map: this.face.tex });
    const mats = [bodyMat, bodyMat, bodyMat, bodyMat, faceMat, bodyMat];
    this.body = new THREE.Mesh(bodyGeo, mats);
    this.body.position.y = 0.75;
    this.body.castShadow = true;
    this.bodyGroup.add(this.body);

    // Holographic Cyber Antenna Beacon on Top
    const antStem = new THREE.Mesh(
      new THREE.CylinderGeometry(0.02, 0.02, 0.32, 12),
      new THREE.MeshStandardMaterial({ color: CLAUDE_DARK, roughness: 0.4 })
    );
    antStem.position.set(0, 1.39, 0);
    this.bodyGroup.add(antStem);

    const antBeacon = new THREE.Mesh(
      new THREE.SphereGeometry(0.085, 16, 16),
      new THREE.MeshBasicMaterial({ color: CYAN_GLOW })
    );
    antBeacon.position.set(0, 1.57, 0);
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
      new THREE.Mesh(legGeo, legMat),
      new THREE.Mesh(legGeo, legMat),
      new THREE.Mesh(legGeo, legMat),
      new THREE.Mesh(legGeo, legMat),
    ];
    this.legs[0].position.set(-0.34, 0.19, 0.3);
    this.legs[1].position.set(0.34, 0.19, 0.3);
    this.legs[2].position.set(-0.34, 0.19, -0.3);
    this.legs[3].position.set(0.34, 0.19, -0.3);
    this.legs.forEach(l => { l.castShadow = true; this.group.add(l); });

    // Multi-Articulation Presenter Arms
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

    // Sleek Holographic Presenter Stylus / Pointer (NO swords!)
    this.stylus = this._makeStylus();
    this.stylus.visible = true;
    this.armR.add(this.stylus);

    // Floating Hologram Code Keyboard (when typing/coding)
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

  _makeStylus() {
    const g = new THREE.Group();
    // Ergonomic metallic handle
    const handle = new THREE.Mesh(
      new THREE.CylinderGeometry(0.025, 0.025, 0.22, 16),
      new THREE.MeshStandardMaterial({ color: '#2B3240', roughness: 0.3, metalness: 0.8 })
    );
    handle.position.set(0, -0.2, 0.1);
    handle.rotation.x = Math.PI / 3;
    g.add(handle);

    // Glowing cyan stylus tip
    const tip = new THREE.Mesh(
      new THREE.CylinderGeometry(0.008, 0.022, 0.24, 16),
      new THREE.MeshBasicMaterial({ color: CYAN_GLOW })
    );
    tip.position.set(0, 0.18, 0);
    handle.add(tip);
    return g;
  }

  _makeHoloKeyboard() {
    const c = document.createElement('canvas');
    c.width = 512; c.height = 256;
    const ctx = c.getContext('2d');
    ctx.fillStyle = 'rgba(0, 240, 255, 0.85)';
    ctx.roundRect(8, 8, 496, 240, 20);
    ctx.fill();
    ctx.fillStyle = '#0B101E';
    ctx.font = 'bold 32px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('⌨ CLAUDE CODE AUTONOMOUS', 256, 85);
    ctx.fillText('> executing agent workflow...', 256, 155);
    const tex = new THREE.CanvasTexture(c);
    const mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(1.1, 0.55),
      new THREE.MeshBasicMaterial({ map: tex, transparent: true, opacity: 0.9 })
    );
    mesh.position.set(0, 0.5, 0.72);
    mesh.rotation.x = -Math.PI / 4;
    return mesh;
  }

  set(st, t = 0) {
    Object.assign(this.st, st);
    renderFace(this.face, this.st);

    const isTalking = this.st.talk > 0.05;
    const action = this.st.action || 'idle';

    // Antenna pulse
    if (this.antBeacon) {
      this.antBeacon.scale.setScalar(1 + Math.sin(t * 8) * 0.25);
    }

    // Natural grounded posture & gentle breathing
    this.bodyGroup.position.y = Math.sin(t * 2.0) * 0.015;
    this.bodyGroup.rotation.z = Math.sin(t * 1.5) * 0.012;

    // Choreographed Presenter Actions (Zero sword swinging!)
    if (action === 'code' || action === 'type') {
      this.stylus.visible = false;
      this.holoKeyboard.visible = true;
      // High-tech typing on holographic keyboard
      this.armR.rotation.set(-0.65 + Math.sin(t * 24) * 0.16, 0.15, -0.22);
      this.armL.rotation.set(-0.65 + Math.cos(t * 24) * 0.16, -0.15, 0.22);
    } else if (action === 'point' || isTalking) {
      this.stylus.visible = true;
      this.holoKeyboard.visible = false;
      // Confident presenter gesturing toward center hologram
      this.armR.rotation.x = -0.75 + Math.sin(t * 8) * 0.25;
      this.armR.rotation.y = 0.2 + Math.sin(t * 5) * 0.12;
      this.armR.rotation.z = -0.35 + Math.sin(t * 6) * 0.12;
      this.armL.rotation.x = -0.22 + Math.cos(t * 7) * 0.12;
    } else {
      this.stylus.visible = false;
      this.holoKeyboard.visible = false;
      // Natural idle presenter posture
      this.armR.rotation.set(0, 0, -0.14);
      this.armL.rotation.set(0, 0, 0.14);
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
      roughness: 0.38,
      metalness: 0.08
    });
    const faceMat = new THREE.MeshBasicMaterial({ map: this.face.tex });
    const mats = [bodyMat, bodyMat, bodyMat, bodyMat, faceMat, bodyMat];
    this.body = new THREE.Mesh(bodyGeo, mats);
    this.body.position.y = 0.72;
    this.body.castShadow = true;
    this.bodyGroup.add(this.body);

    // Magenta Ribbon Bow on Top
    this.bow = this._makeBow();
    this.bow.position.set(0.24, 1.25, 0.12);
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
    const armMat = new THREE.MeshStandardMaterial({ color: SKEPTIC_PINK, roughness: 0.42 });
    this.armL = new THREE.Mesh(armGeo, armMat);
    this.armR = new THREE.Mesh(armGeo, armMat);
    this.armL.position.set(-0.58, 0.72, 0.08);
    this.armR.position.set(0.58, 0.72, 0.08);
    this.armL.castShadow = true;
    this.armR.castShadow = true;
    this.bodyGroup.add(this.armL);
    this.bodyGroup.add(this.armR);

    // Floating 3D Reaction Holo-Badges (Elegantly hovering above her bow)
    this.bubbleShock = this._makeReactionPill('?!', '#FF2A85');
    this.bubbleDoubt = this._makeReactionPill('CAP?', '#FF9F1C');
    this.bubbleMoney = this._makeReactionPill('FREE?', '#10B981');
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
    c.width = 256; c.height = 256;
    const ctx = c.getContext('2d');
    ctx.fillStyle = bg;
    ctx.beginPath();
    ctx.arc(128, 128, 115, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#FFFFFF';
    ctx.lineWidth = 14;
    ctx.stroke();

    ctx.fillStyle = '#FFFFFF';
    ctx.font = '900 88px Inter, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(text, 128, 134);
    const tex = new THREE.CanvasTexture(c);
    const mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(0.52, 0.52),
      new THREE.MeshBasicMaterial({ map: tex, transparent: true })
    );
    mesh.position.set(0.48, 1.68, 0.2);
    mesh.visible = false;
    return mesh;
  }

  set(st, t = 0) {
    Object.assign(this.st, st);
    renderFace(this.face, this.st);

    const isTalking = this.st.talk > 0.05;
    const mood = this.st.mood || 'neutral';

    // Gentle breathing & inquisitive head tilt
    this.bodyGroup.position.y = Math.sin(t * 2.2) * 0.012;
    this.bodyGroup.rotation.z = (mood === 'skeptic' ? -0.05 : 0) + Math.sin(t * 1.6) * 0.012;
    this.bow.rotation.z = Math.sin(t * 3.5) * 0.04;

    // Reset reaction bubbles
    this.bubbleShock.visible = false;
    this.bubbleDoubt.visible = false;
    this.bubbleMoney.visible = false;

    // Emotive Hand Performance & Reaction Holo-Badges
    if (mood === 'shock' || mood === 'amazed') {
      this.bubbleShock.visible = true;
      this.bubbleShock.position.y = 1.68 + Math.sin(t * 6) * 0.06;
      this.armL.rotation.set(-1.1 + Math.sin(t * 8) * 0.12, 0, 0.45);
      this.armR.rotation.set(-1.1 + Math.sin(t * 8) * 0.12, 0, -0.45);
    } else if (mood === 'skeptic' || mood === 'doubt') {
      this.bubbleDoubt.visible = true;
      this.bubbleDoubt.position.y = 1.68 + Math.sin(t * 5) * 0.05;
      // Inquisitive hand to chin
      this.armL.rotation.set(0.12, 0, 0.45);
      this.armR.rotation.set(-0.85 + Math.sin(t * 7) * 0.1, 0.2, -0.18);
    } else if (mood === 'money') {
      this.bubbleMoney.visible = true;
      this.bubbleMoney.position.y = 1.68 + Math.sin(t * 5) * 0.05;
      this.armL.rotation.set(-0.45, 0, 0.32);
      this.armR.rotation.set(-0.45, 0, -0.32);
    } else if (isTalking) {
      this.armL.rotation.set(-0.4 + Math.sin(t * 10) * 0.22, 0, 0.25);
      this.armR.rotation.set(-0.5 + Math.cos(t * 10) * 0.22, 0, -0.25);
    } else {
      this.armL.rotation.set(0, 0, 0.14);
      this.armR.rotation.set(0, 0, -0.14);
    }
  }
}
