// CurioCut Dynamic 3D Procedural Studio & Topic-Driven Props Engine
// 100% procedural Three.js models generated dynamically from topic semantics.
import * as THREE from 'three';

const CYAN_GLOW = '#00F0FF';
const HAZARD_YELLOW = '#F5B041';
const HAZARD_BLACK = '#1C1D24';
const GOLD = '#F5C518';
const EMERALD_GREEN = '#10B981';
const NEON_PURPLE = '#A855F7';

/** 1. High-End Warm Architectural Tech Studio Environment */
export function techStudio() {
  const g = new THREE.Group();

  // Polished Studio Floor with high specular sheen
  const floorMat = new THREE.MeshStandardMaterial({
    color: '#E8E1D7',
    roughness: 0.28,
    metalness: 0.08
  });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(36, 36), floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -0.01;
  floor.receiveShadow = true;
  g.add(floor);

  // Warm Studio Back Wall with soft vertical architectural seams
  const wallMat = new THREE.MeshStandardMaterial({
    color: '#C6AA8B',
    roughness: 0.65,
    metalness: 0.02
  });
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(36, 18), wallMat);
  wall.position.set(0, 8.5, -4.8);
  wall.receiveShadow = true;
  g.add(wall);

  // Vertical Architectural Panel Seams
  for (let x = -15; x <= 15; x += 3.75) {
    const seam = new THREE.Mesh(
      new THREE.BoxGeometry(0.05, 18, 0.06),
      new THREE.MeshStandardMaterial({ color: '#A08365', roughness: 0.8 })
    );
    seam.position.set(x, 8.5, -4.76);
    g.add(seam);
  }

  // Floating Cyber Dust & Energy Sparks
  const particleCount = 85;
  const posArray = new Float32Array(particleCount * 3);
  for (let i = 0; i < particleCount * 3; i += 3) {
    posArray[i] = (Math.random() - 0.5) * 14;
    posArray[i + 1] = Math.random() * 6.5 + 0.3;
    posArray[i + 2] = (Math.random() - 0.5) * 6.5;
  }
  const partGeo = new THREE.BufferGeometry();
  partGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
  const partMat = new THREE.PointsMaterial({
    color: '#F5D061',
    size: 0.085,
    transparent: true,
    opacity: 0.8
  });
  const particles = new THREE.Points(partGeo, partMat);
  g.add(particles);

  g.update = (t) => {
    const pos = partGeo.attributes.position.array;
    for (let i = 1; i < particleCount * 3; i += 3) {
      pos[i] += 0.007;
      if (pos[i] > 6.8) pos[i] = 0.3;
    }
    partGeo.attributes.position.needsUpdate = true;
  };

  return g;
}

/** 2. DYNAMIC PROP: Price Slicer & Cost Obliterator ($1B / $20 -> $0 / FREE) */
export function buildPriceSlicer(line, scriptContext) {
  const g = new THREE.Group();
  g.position.set(0, 0, 0.2);

  const goldMat = new THREE.MeshStandardMaterial({
    color: GOLD,
    metalness: 0.88,
    roughness: 0.16
  });

  const header = (line.header || '').toUpperCase();
  const text = (line.text || '').toUpperCase();
  const initialPrice = header.includes('$1B') || text.includes('BILLION') ? '$1,000,000,000' :
                       text.includes('TWENTY') || header.includes('$20') ? '$20 / MONTH' :
                       '$999 / YEAR';

  const makeBlockHalf = (label, sign) => {
    const grp = new THREE.Group();
    const box = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.8, 0.45), goldMat);
    box.position.y = 0.4;
    box.castShadow = true;
    grp.add(box);

    const c = document.createElement('canvas');
    c.width = 300; c.height = 140;
    const ctx = c.getContext('2d');
    ctx.fillStyle = '#FFFFFF';
    ctx.roundRect(8, 8, 284, 124, 14);
    ctx.fill();
    ctx.fillStyle = '#E11D48';
    ctx.font = '900 34px Inter, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(label, 150, 70);
    const tex = new THREE.CanvasTexture(c);

    const labelMesh = new THREE.Mesh(new THREE.PlaneGeometry(0.76, 0.36), new THREE.MeshBasicMaterial({ map: tex }));
    labelMesh.position.set(0, 0.44, 0.231);
    grp.add(labelMesh);
    return grp;
  };

  const leftHalf = makeBlockHalf(initialPrice, -1);
  const rightHalf = makeBlockHalf('CUT TO $0', 1);
  g.add(leftHalf);
  g.add(rightHalf);

  // Floating $0.00 Emerald Pill Inside Cut
  const c0 = document.createElement('canvas');
  c0.width = 256; c0.height = 128;
  const ctx0 = c0.getContext('2d');
  ctx0.fillStyle = EMERALD_GREEN;
  ctx0.roundRect(8, 8, 240, 112, 20);
  ctx0.fill();
  ctx0.fillStyle = '#FFFFFF';
  ctx0.font = '900 58px Inter, sans-serif';
  ctx0.textAlign = 'center'; ctx0.textBaseline = 'middle';
  ctx0.fillText('$0.00', 128, 64);
  const t0 = new THREE.CanvasTexture(c0);
  const pill0 = new THREE.Mesh(new THREE.PlaneGeometry(0.85, 0.42), new THREE.MeshBasicMaterial({ map: t0, transparent: true }));
  pill0.position.set(0, 0.95, 0.15);
  g.add(pill0);

  // Scattered Gold Coins on Ground
  const coinMat = new THREE.MeshStandardMaterial({ color: '#FFD700', metalness: 0.92, roughness: 0.12 });
  for (let i = 0; i < 24; i++) {
    const coin = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 0.03, 16), coinMat);
    coin.position.set((Math.random() - 0.5) * 2.2, 0.015, (Math.random() - 0.5) * 1.4 + 0.3);
    coin.rotation.y = Math.random() * Math.PI;
    coin.castShadow = true;
    g.add(coin);
  }

  g.update = (t) => {
    const sliceAnim = Math.min(1, Math.max(0, (t % 3.6) * 1.7));
    leftHalf.position.x = -0.46 - sliceAnim * 0.42;
    leftHalf.rotation.z = sliceAnim * 0.22;
    rightHalf.position.x = 0.46 + sliceAnim * 0.42;
    rightHalf.rotation.z = -sliceAnim * 0.22;
    pill0.position.y = 0.95 + Math.sin(t * 4) * 0.08;
    pill0.scale.setScalar(0.85 + sliceAnim * 0.3);
  };

  return g;
}

/** 3. DYNAMIC PROP: Cyber Holographic IDE & Matrix Workspace */
export function buildHoloIDE(line, scriptContext) {
  const g = new THREE.Group();
  g.position.set(0, 1.4, 0.1);

  const toolName = scriptContext.tool_name || 'Autonomous Tool';

  // Master Floating Glass Screen
  const c = document.createElement('canvas');
  c.width = 600; c.height = 360;
  const ctx = c.getContext('2d');
  ctx.fillStyle = 'rgba(10, 14, 28, 0.95)';
  ctx.roundRect(8, 8, 584, 344, 20);
  ctx.fill();

  // Window title bar dots
  ctx.fillStyle = '#EF4444'; ctx.beginPath(); ctx.arc(36, 36, 10, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#F59E0B'; ctx.beginPath(); ctx.arc(66, 36, 10, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#10B981'; ctx.beginPath(); ctx.arc(96, 36, 10, 0, Math.PI * 2); ctx.fill();

  ctx.fillStyle = '#94A3B8';
  ctx.font = 'bold 20px monospace';
  ctx.fillText(`terminal — claude-code / ${toolName}`, 130, 42);

  // Syntax Highlighted Code
  ctx.fillStyle = '#38BDF8';
  ctx.font = 'bold 22px Courier New, monospace';
  ctx.fillText(`> claude code --skill install`, 32, 94);

  ctx.fillStyle = '#4ADE80';
  ctx.fillText(`✓ Found skill: ${toolName}`, 32, 136);

  ctx.fillStyle = '#FCD34D';
  ctx.font = '19px Courier New, monospace';
  ctx.fillText(`  [+] Cloning local repository...`, 32, 178);
  ctx.fillText(`  [+] Zero API keys required`, 32, 214);
  ctx.fillText(`  [+] Neural core running offline`, 32, 250);

  ctx.fillStyle = '#A855F7';
  ctx.font = 'bold 22px Courier New, monospace';
  ctx.fillText(`READY: Autonomous loop active.`, 32, 302);

  const tex = new THREE.CanvasTexture(c);
  const screen = new THREE.Mesh(
    new THREE.PlaneGeometry(2.2, 1.32),
    new THREE.MeshBasicMaterial({ map: tex, transparent: true, opacity: 0.94 })
  );
  g.add(screen);

  // Orbiting Glowing Network Cubes
  const cubes = [];
  const cubeGeo = new THREE.BoxGeometry(0.12, 0.12, 0.12);
  const cubeMat = new THREE.MeshBasicMaterial({ color: CYAN_GLOW });
  for (let i = 0; i < 8; i++) {
    const cb = new THREE.Mesh(cubeGeo, cubeMat);
    g.add(cb);
    cubes.push(cb);
  }

  g.update = (t) => {
    screen.position.y = Math.sin(t * 2.2) * 0.05;
    cubes.forEach((cb, idx) => {
      const ang = t * 1.5 + (idx / cubes.length) * Math.PI * 2;
      const rad = 1.35 + Math.sin(t * 2 + idx) * 0.15;
      cb.position.set(Math.cos(ang) * rad, Math.sin(ang * 0.7) * 0.5, Math.sin(ang) * 0.6);
      cb.rotation.x = t * 2;
      cb.rotation.y = t * 3;
    });
  };

  return g;
}

/** 4. DYNAMIC PROP: Quantum Neural Core with Gyroscopic Rings */
export function buildNeuralCore(line, scriptContext) {
  const g = new THREE.Group();
  g.position.set(0, 1.25, 0.2);

  // Central Glowing Synapse Core
  const core = new THREE.Mesh(
    new THREE.SphereGeometry(0.38, 32, 32),
    new THREE.MeshBasicMaterial({ color: '#FFFFFF' })
  );
  g.add(core);

  // Gyroscopic Holographic Rings
  const ringMat1 = new THREE.MeshBasicMaterial({ color: CYAN_GLOW });
  const ringMat2 = new THREE.MeshBasicMaterial({ color: NEON_PURPLE });
  const ring1 = new THREE.Mesh(new THREE.TorusGeometry(0.68, 0.026, 16, 64), ringMat1);
  const ring2 = new THREE.Mesh(new THREE.TorusGeometry(0.85, 0.026, 16, 64), ringMat2);
  g.add(ring1);
  g.add(ring2);

  // Dynamic Floating Badges (e.g. STANFORD / GITHUB / 100% BENCHMARK)
  const makeBadge = (txt, bg) => {
    const c = document.createElement('canvas');
    c.width = 256; c.height = 80;
    const ctx = c.getContext('2d');
    ctx.fillStyle = bg;
    ctx.roundRect(4, 4, 248, 72, 14);
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '900 28px Inter, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(txt, 128, 40);
    const tex = new THREE.CanvasTexture(c);
    const m = new THREE.Mesh(new THREE.PlaneGeometry(0.72, 0.24), new THREE.MeshBasicMaterial({ map: tex }));
    return m;
  };

  const badgeL = makeBadge('LOCAL MODEL', '#10B981');
  const badgeR = makeBadge('BEATS CHATGPT', '#2563EB');
  badgeL.position.set(-0.95, 0.5, 0);
  badgeR.position.set(0.95, 0.5, 0);
  g.add(badgeL);
  g.add(badgeR);

  g.update = (t) => {
    ring1.rotation.x = t * 2.4;
    ring1.rotation.y = t * 1.8;
    ring2.rotation.y = -t * 2.1;
    ring2.rotation.z = t * 2.7;
    core.scale.setScalar(1 + Math.sin(t * 6) * 0.12);
    badgeL.position.y = 0.5 + Math.sin(t * 3) * 0.08;
    badgeR.position.y = 0.5 + Math.sin(t * 3 + Math.PI) * 0.08;
  };

  return g;
}

/** 5. DYNAMIC PROP: Hyperspeed Chrono-Tachometer & 4-Second Speedometer */
export function buildSpeedGauge(line, scriptContext) {
  const g = new THREE.Group();
  g.position.set(0, 1.4, 0.2);

  const c = document.createElement('canvas');
  c.width = 512; c.height = 300;
  const ctx = c.getContext('2d');

  const tex = new THREE.CanvasTexture(c);
  const card = new THREE.Mesh(new THREE.PlaneGeometry(2.0, 1.18), new THREE.MeshBasicMaterial({ map: tex, transparent: true }));
  g.add(card);

  g.update = (t) => {
    ctx.clearRect(0, 0, 512, 300);
    ctx.fillStyle = 'rgba(15, 23, 42, 0.94)';
    ctx.roundRect(8, 8, 496, 284, 22);
    ctx.fill();

    ctx.fillStyle = '#38BDF8';
    ctx.font = 'bold 24px Inter, sans-serif';
    ctx.fillText('SPEED BENCHMARK', 32, 52);

    // Tachometer Arc
    const cx = 256, cy = 200, r = 110;
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 22;
    ctx.beginPath();
    ctx.arc(cx, cy, r, Math.PI, 0);
    ctx.stroke();

    // Revving Speed Value
    const rev = (Math.sin(t * 4) * 0.5 + 0.5);
    ctx.strokeStyle = '#10B981';
    ctx.beginPath();
    ctx.arc(cx, cy, r, Math.PI, Math.PI + rev * Math.PI);
    ctx.stroke();

    ctx.fillStyle = '#FFFFFF';
    ctx.font = '900 64px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('4 SEC', cx, cy - 20);

    ctx.fillStyle = '#94A3B8';
    ctx.font = 'bold 20px Inter, sans-serif';
    ctx.fillText('FROM SCREENSHOT TO FULL CODE', cx, cy + 28);
    ctx.textAlign = 'left';

    tex.needsUpdate = true;
    card.position.y = Math.sin(t * 3) * 0.04;
  };

  return g;
}

/** 6. DYNAMIC PROP: Audio Equalizer Monolith & Spoken Briefing */
export function buildAudioMonolith(line, scriptContext) {
  const g = new THREE.Group();
  g.position.set(0, 0.1, 0.2);

  // Equalizer Tower Pedestal
  const ped = new THREE.Mesh(
    new THREE.BoxGeometry(2.4, 0.14, 0.8),
    new THREE.MeshStandardMaterial({ color: '#1E293B', roughness: 0.4 })
  );
  ped.position.y = 0.07;
  g.add(ped);

  // Physical 3D Equalizer Pillars
  const pillars = [];
  const pilGeo = new THREE.BoxGeometry(0.08, 1.0, 0.08);
  for (let i = 0; i < 20; i++) {
    const col = i % 2 === 0 ? CYAN_GLOW : NEON_PURPLE;
    const m = new THREE.Mesh(pilGeo, new THREE.MeshBasicMaterial({ color: col }));
    m.position.set(-1.0 + i * 0.105, 0.6, 0);
    g.add(m);
    pillars.push(m);
  }

  // Floating Speech Card
  const c = document.createElement('canvas');
  c.width = 512; c.height = 140;
  const ctx = c.getContext('2d');
  ctx.fillStyle = 'rgba(15, 23, 42, 0.92)';
  ctx.roundRect(6, 6, 500, 128, 16);
  ctx.fill();
  ctx.fillStyle = '#38BDF8';
  ctx.font = 'bold 22px Inter, sans-serif';
  ctx.fillText('SPOKEN DAILY BRIEFING', 24, 46);
  ctx.fillStyle = '#FFFFFF';
  ctx.font = 'italic 20px Inter, sans-serif';
  ctx.fillText('"3 tasks require your review this morning."', 24, 94);
  const tex = new THREE.CanvasTexture(c);

  const card = new THREE.Mesh(new THREE.PlaneGeometry(1.85, 0.52), new THREE.MeshBasicMaterial({ map: tex }));
  card.position.set(0, 1.85, 0.2);
  g.add(card);

  g.update = (t) => {
    pillars.forEach((p, idx) => {
      const h = Math.abs(Math.sin(t * 8 + idx * 0.5)) * 1.2 + 0.15;
      p.scale.y = h;
      p.position.y = 0.14 + h / 2;
    });
    card.position.y = 1.85 + Math.sin(t * 2.5) * 0.05;
  };

  return g;
}

/** 7. DYNAMIC PROP: Air-Gapped Privacy Citadel & Offline Laptop */
export function buildLocalCitadel(line, scriptContext) {
  const g = new THREE.Group();
  g.position.set(0, 0.1, 0.2);

  // Modern Sleek Laptop Base
  const lapMat = new THREE.MeshStandardMaterial({ color: '#334155', metalness: 0.8, roughness: 0.2 });
  const base = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.06, 1.1), lapMat);
  base.position.y = 0.45;
  g.add(base);

  // Laptop Screen tilted open
  const screen = new THREE.Mesh(new THREE.BoxGeometry(1.6, 1.0, 0.04), lapMat);
  screen.position.set(0, 0.95, -0.45);
  screen.rotation.x = -0.18;
  g.add(screen);

  // Display Texture (100% Offline / No WiFi)
  const c = document.createElement('canvas');
  c.width = 512; c.height = 320;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#0F172A';
  ctx.fillRect(0, 0, 512, 320);
  ctx.fillStyle = '#10B981';
  ctx.font = 'bold 32px Inter, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('🔒 100% OFFLINE', 256, 110);
  ctx.fillStyle = '#FFFFFF';
  ctx.font = '24px Inter, sans-serif';
  ctx.fillText('ZERO CLOUD SUBSCRIPTIONS', 256, 170);
  ctx.fillStyle = '#64748B';
  ctx.fillText('Data stays on your machine forever', 256, 230);
  const tex = new THREE.CanvasTexture(c);

  const display = new THREE.Mesh(new THREE.PlaneGeometry(1.48, 0.9), new THREE.MeshBasicMaterial({ map: tex }));
  display.position.set(0, 0.95, -0.428);
  display.rotation.x = -0.18;
  g.add(display);

  // Floating Cyber Security Shield
  const shieldMat = new THREE.MeshBasicMaterial({ color: '#10B981', wireframe: true });
  const shield = new THREE.Mesh(new THREE.IcosahedronGeometry(0.38, 2), shieldMat);
  shield.position.set(0, 1.85, 0);
  g.add(shield);

  g.update = (t) => {
    shield.rotation.y = t * 1.5;
    shield.rotation.x = t * 0.9;
    shield.position.y = 1.85 + Math.sin(t * 3) * 0.07;
  };

  return g;
}

/** 8. DYNAMIC PROP: Viral Instagram Comment Box & Flying DM Airplane */
export function buildViralCommentBox(keyword = 'FAST') {
  const g = new THREE.Group();
  g.position.set(0, 1.55, 0.2);

  // Frosted Glass Instagram Comment Pill
  const c = document.createElement('canvas');
  c.width = 620; c.height = 144;
  const ctx = c.getContext('2d');

  ctx.fillStyle = '#FFFFFF';
  ctx.roundRect(8, 8, 604, 128, 26);
  ctx.fill();

  ctx.fillStyle = '#E1306C';
  ctx.font = '900 36px Inter, sans-serif';
  ctx.fillText('💬 Comment', 34, 78);

  ctx.fillStyle = '#0F172A';
  ctx.font = '900 44px Inter, sans-serif';
  ctx.fillText(`"${keyword}"`, 265, 78);

  ctx.fillStyle = '#2563EB';
  ctx.font = 'bold 32px Inter, sans-serif';
  ctx.textAlign = 'right';
  ctx.fillText('Send 🚀', 580, 78);

  const tex = new THREE.CanvasTexture(c);
  const card = new THREE.Mesh(
    new THREE.PlaneGeometry(2.35, 0.55),
    new THREE.MeshBasicMaterial({ map: tex, transparent: true })
  );
  g.add(card);

  // 3D Flying Origami Paper Airplane
  const planeGeo = new THREE.ConeGeometry(0.18, 0.55, 3);
  const planeMat = new THREE.MeshStandardMaterial({ color: '#FFFFFF', roughness: 0.2 });
  const plane = new THREE.Mesh(planeGeo, planeMat);
  plane.rotation.z = Math.PI / 2;
  g.add(plane);

  // 3D Bursting Heart & Confetti Particles
  const partCount = 45;
  const pPos = new Float32Array(partCount * 3);
  for (let i = 0; i < partCount * 3; i += 3) {
    pPos[i] = (Math.random() - 0.5) * 3.0;
    pPos[i + 1] = (Math.random() - 0.5) * 1.8;
    pPos[i + 2] = (Math.random() - 0.5) * 1.2;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
  const mat = new THREE.PointsMaterial({ color: '#E1306C', size: 0.11 });
  const confetti = new THREE.Points(geo, mat);
  g.add(confetti);

  g.update = (t) => {
    card.position.y = Math.sin(t * 3.2) * 0.05;
    confetti.rotation.y = t * 0.9;

    // Orbiting paper airplane delivering link straight to camera
    const ang = t * 2.8;
    plane.position.set(Math.cos(ang) * 1.4, 0.35 + Math.sin(ang * 2) * 0.25, Math.sin(ang) * 0.8);
    plane.rotation.y = -ang - Math.PI / 2;
  };

  return g;
}

/** 9. DYNAMIC PROP FACTORY: Creates custom 3D prop per line topic & keywords */
export function createDynamicTopicProp(line, scriptContext, index, isLast) {
  if (isLast) {
    const kw = scriptContext.cta_keyword || 'FAST';
    return buildViralCommentBox(kw);
  }

  const h = ((line.header || '') + ' ' + (line.text || '') + ' ' + (line.prop || '')).toUpperCase();

  if (h.includes('PRICE') || h.includes('COST') || h.includes('$') || h.includes('BILLION') || h.includes('PAY') || h.includes('SUBSCRIPTION') || h.includes('SWORD')) {
    return buildPriceSlicer(line, scriptContext);
  }
  if (h.includes('CODE') || h.includes('REPO') || h.includes('GITHUB') || h.includes('INSTALL') || h.includes('TERMINAL') || h.includes('DEV') || h.includes('TOOL')) {
    return buildHoloIDE(line, scriptContext);
  }
  if (h.includes('SPEED') || h.includes('FAST') || h.includes('SECOND') || h.includes('MINUTE') || h.includes('INSTANT') || h.includes('BENCHMARK')) {
    return buildSpeedGauge(line, scriptContext);
  }
  if (h.includes('AUDIO') || h.includes('VOICE') || h.includes('BRIEF') || h.includes('SPEAK') || h.includes('PODCAST') || h.includes('LISTEN') || h.includes('WAVE')) {
    return buildAudioMonolith(line, scriptContext);
  }
  if (h.includes('LOCAL') || h.includes('LAPTOP') || h.includes('OFFLINE') || h.includes('PRIVATE') || h.includes('WIFI') || h.includes('COMPUTER') || h.includes('CITADEL')) {
    return buildLocalCitadel(line, scriptContext);
  }
  if (h.includes('MODEL') || h.includes('AI') || h.includes('SMART') || h.includes('BRAIN') || h.includes('STANFORD') || h.includes('CHATGPT') || h.includes('REASON') || h.includes('ORB')) {
    return buildNeuralCore(line, scriptContext);
  }

  // Fallback to alternating high-tech core or IDE
  return index % 2 === 0 ? buildNeuralCore(line, scriptContext) : buildHoloIDE(line, scriptContext);
}
