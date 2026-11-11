// CurioCut Topic-Driven 3D Holographic Props Engine for Claude-Desk
// 100% procedural Three.js holographic models generated dynamically from topic semantics.
// All props hover majestically in clear air at the Center Hologram Stage (x=0, y=1.75, z=0.0)
// with zero character clipping or intersection.
import * as THREE from 'three';

const CYAN_NEON = '#00F0FF';
const EMERALD_GREEN = '#10B981';
const AMBER_GOLD = '#F5B041';
const CORAL_ACCENT = '#FF6B4A';
const MAGENTA_NEON = '#FF2A85';

/** 1. Dynamic Floating Glass Code Terminal (For code, agents, tools, git, CLI) */
export function buildCodeTerminal(line, scriptContext) {
  const g = new THREE.Group();
  g.position.set(0, 1.75, 0.0);

  const c = document.createElement('canvas');
  c.width = 768;
  c.height = 432;
  const ctx = c.getContext('2d');
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;

  // Futuristic curved glass holographic terminal
  const panelGeo = new THREE.PlaneGeometry(1.4, 0.78);
  const panelMat = new THREE.MeshBasicMaterial({
    map: tex,
    transparent: true,
    opacity: 0.95,
    side: THREE.DoubleSide
  });
  const panel = new THREE.Mesh(panelGeo, panelMat);
  g.add(panel);

  // Hologram outer glowing border frame
  const border = new THREE.LineSegments(
    new THREE.EdgesGeometry(panelGeo),
    new THREE.LineBasicMaterial({ color: CYAN_NEON, linewidth: 2 })
  );
  panel.add(border);

  const headerText = (line.header || 'CLAUDE CODE').toUpperCase();
  const rawText = line.text || 'Autonomous Agent Execution';

  g.update = (t) => {
    ctx.clearRect(0, 0, 768, 432);

    // Dark glass body with cyber glow
    ctx.fillStyle = 'rgba(10, 16, 28, 0.92)';
    ctx.roundRect(8, 8, 752, 416, 18);
    ctx.fill();

    // Top window bar
    ctx.fillStyle = 'rgba(0, 240, 255, 0.2)';
    ctx.fillRect(12, 12, 744, 48);

    // Terminal window dots
    ctx.fillStyle = '#EF4444';
    ctx.beginPath(); ctx.arc(36, 36, 8, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#F59E0B';
    ctx.beginPath(); ctx.arc(60, 36, 8, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#10B981';
    ctx.beginPath(); ctx.arc(84, 36, 8, 0, Math.PI * 2); ctx.fill();

    ctx.fillStyle = '#00F0FF';
    ctx.font = 'bold 22px monospace';
    ctx.fillText(`◈ ${headerText.slice(0, 28)} ◈`, 120, 44);

    // Syntax-highlighted code execution
    ctx.font = 'bold 20px monospace';
    ctx.fillStyle = '#94A3B8';
    ctx.fillText('$ claude --dangerously-skip-permissions', 32, 105);

    ctx.fillStyle = '#10B981';
    ctx.fillText('✔ Initializing autonomous agent swarm...', 32, 145);

    ctx.fillStyle = '#38BDF8';
    ctx.fillText('> git clone repository --verified', 32, 185);

    ctx.fillStyle = '#F59E0B';
    ctx.fillText('> auto-fixing dependencies & compiling...', 32, 225);

    // Live blinking cursor and progress
    const blink = Math.sin(t * 8) > 0;
    ctx.fillStyle = '#00F0FF';
    ctx.fillText(`[AGENT ACTIVE] ${blink ? '█' : ' '}`, 32, 280);

    // Action summary pill at bottom
    ctx.fillStyle = 'rgba(16, 185, 129, 0.25)';
    ctx.roundRect(32, 320, 704, 76, 12);
    ctx.fill();
    ctx.strokeStyle = '#10B981';
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 24px Inter, sans-serif';
    ctx.fillText(rawText.slice(0, 44).toUpperCase(), 48, 368);

    tex.needsUpdate = true;
    panel.position.y = Math.sin(t * 2.8) * 0.04;
    panel.rotation.y = Math.sin(t * 1.4) * 0.06;
  };

  return g;
}

/** 2. Dynamic 3D Speedometer Tachometer (For speed, latency, instant, 4-sec benchmarks) */
export function buildSpeedGauge(line, scriptContext) {
  const g = new THREE.Group();
  g.position.set(0, 1.75, 0.0);

  const c = document.createElement('canvas');
  c.width = 640;
  c.height = 400;
  const ctx = c.getContext('2d');
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;

  const cardGeo = new THREE.PlaneGeometry(1.3, 0.82);
  const cardMat = new THREE.MeshBasicMaterial({
    map: tex,
    transparent: true,
    opacity: 0.95,
    side: THREE.DoubleSide
  });
  const card = new THREE.Mesh(cardGeo, cardMat);
  g.add(card);

  const border = new THREE.LineSegments(
    new THREE.EdgesGeometry(cardGeo),
    new THREE.LineBasicMaterial({ color: EMERALD_GREEN })
  );
  card.add(border);

  const headerText = (line.header || 'SPEED BENCHMARK').toUpperCase();

  g.update = (t) => {
    ctx.clearRect(0, 0, 640, 400);

    ctx.fillStyle = 'rgba(11, 19, 32, 0.94)';
    ctx.roundRect(10, 10, 620, 380, 22);
    ctx.fill();

    // Top Header Badge
    ctx.fillStyle = '#38BDF8';
    ctx.font = '900 24px Inter, sans-serif';
    ctx.fillText(`⚡ ${headerText.slice(0, 26)}`, 36, 52);

    // Tachometer Arc
    const cx = 320, cy = 250, r = 125;
    ctx.strokeStyle = '#1E293B';
    ctx.lineWidth = 26;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.arc(cx, cy, r, Math.PI, 0);
    ctx.stroke();

    // Revving animated green arc
    const rev = Math.min(1, Math.max(0.2, (Math.sin(t * 5) * 0.5 + 0.5)));
    const grad = ctx.createLinearGradient(cx - r, cy, cx + r, cy);
    grad.addColorStop(0, '#00F0FF');
    grad.addColorStop(0.7, '#10B981');
    grad.addColorStop(1, '#F59E0B');
    ctx.strokeStyle = grad;
    ctx.beginPath();
    ctx.arc(cx, cy, r, Math.PI, Math.PI + rev * Math.PI);
    ctx.stroke();

    // Digital readout in center
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '900 78px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('4 SEC', cx, cy - 22);

    ctx.fillStyle = '#94A3B8';
    ctx.font = 'bold 22px Inter, sans-serif';
    ctx.fillText('PROMPT TO COMPLETE APP', cx, cy + 32);
    ctx.textAlign = 'left';

    tex.needsUpdate = true;
    card.position.y = Math.sin(t * 3.0) * 0.04;
    card.rotation.y = Math.sin(t * 1.5) * 0.05;
  };

  return g;
}

/** 3. Dynamic 3D Price / Cost Obliterator ($20/mo -> 100% FREE) */
export function buildPriceSlicer(line, scriptContext) {
  const g = new THREE.Group();
  g.position.set(0, 1.75, 0.0);

  const c = document.createElement('canvas');
  c.width = 640;
  c.height = 380;
  const ctx = c.getContext('2d');
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;

  const cardGeo = new THREE.PlaneGeometry(1.35, 0.8);
  const cardMat = new THREE.MeshBasicMaterial({
    map: tex,
    transparent: true,
    opacity: 0.95,
    side: THREE.DoubleSide
  });
  const card = new THREE.Mesh(cardGeo, cardMat);
  g.add(card);

  const border = new THREE.LineSegments(
    new THREE.EdgesGeometry(cardGeo),
    new THREE.LineBasicMaterial({ color: AMBER_GOLD })
  );
  card.add(border);

  g.update = (t) => {
    ctx.clearRect(0, 0, 640, 380);

    ctx.fillStyle = 'rgba(15, 23, 42, 0.94)';
    ctx.roundRect(10, 10, 620, 360, 20);
    ctx.fill();

    // Crossed out paid price
    ctx.fillStyle = '#94A3B8';
    ctx.font = '900 46px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('$20 / MONTH', 320, 110);

    // Red slash line
    ctx.strokeStyle = '#EF4444';
    ctx.lineWidth = 10;
    ctx.beginPath();
    ctx.moveTo(160, 125);
    ctx.lineTo(480, 85);
    ctx.stroke();

    // 100% Free Glowing Banner
    ctx.fillStyle = 'rgba(16, 185, 129, 0.25)';
    ctx.roundRect(40, 170, 560, 150, 16);
    ctx.fill();
    ctx.strokeStyle = '#10B981';
    ctx.lineWidth = 4;
    ctx.stroke();

    ctx.fillStyle = '#10B981';
    ctx.font = '900 72px Inter, sans-serif';
    ctx.fillText('100% FREE', 320, 248);

    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 22px Inter, sans-serif';
    ctx.fillText('SELF-HOSTED ◈ ZERO SUBSCRIPTION', 320, 296);
    ctx.textAlign = 'left';

    tex.needsUpdate = true;
    card.position.y = Math.sin(t * 3.0) * 0.04;
    card.rotation.y = Math.sin(t * 1.6) * 0.06;
  };

  return g;
}

/** 4. Dynamic 3D Neural Network Core & Model Architecture */
export function buildNeuralCore(line, scriptContext) {
  const g = new THREE.Group();
  g.position.set(0, 1.75, 0.0);

  // Rotating quantum core sphere
  const coreGeo = new THREE.SphereGeometry(0.35, 24, 24);
  const coreMat = new THREE.MeshStandardMaterial({
    color: '#00F0FF',
    emissive: '#007ACC',
    emissiveIntensity: 0.8,
    roughness: 0.2,
    metalness: 0.9
  });
  const core = new THREE.Mesh(coreGeo, coreMat);
  g.add(core);

  // Orbiting synaptic rings
  const ringGeo = new THREE.TorusGeometry(0.55, 0.02, 16, 48);
  const ring1 = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({ color: CYAN_NEON }));
  const ring2 = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({ color: AMBER_GOLD }));
  g.add(ring1);
  g.add(ring2);

  // Floating benchmark HUD badge above core
  const c = document.createElement('canvas');
  c.width = 512;
  c.height = 160;
  const ctx = c.getContext('2d');
  ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
  ctx.roundRect(8, 8, 496, 144, 16);
  ctx.fill();
  ctx.strokeStyle = '#00F0FF';
  ctx.lineWidth = 3;
  ctx.stroke();

  ctx.fillStyle = '#00F0FF';
  ctx.font = 'bold 22px Inter, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('◈ AUTONOMOUS MODEL ARCHITECTURE ◈', 256, 48);

  ctx.fillStyle = '#10B981';
  ctx.font = '900 48px Inter, sans-serif';
  ctx.fillText('OUTPERFORMS GPT-4o', 256, 114);

  const tex = new THREE.CanvasTexture(c);
  const hud = new THREE.Mesh(
    new THREE.PlaneGeometry(1.2, 0.38),
    new THREE.MeshBasicMaterial({ map: tex, transparent: true })
  );
  hud.position.set(0, 0.65, 0);
  g.add(hud);

  g.update = (t) => {
    ring1.rotation.x = t * 2.2;
    ring1.rotation.y = t * 1.6;
    ring2.rotation.y = -t * 1.8;
    ring2.rotation.z = t * 2.4;
    core.scale.setScalar(1 + Math.sin(t * 5) * 0.08);
    hud.position.y = 0.65 + Math.sin(t * 3) * 0.03;
    g.position.y = 1.75 + Math.sin(t * 2.5) * 0.03;
  };

  return g;
}

/** 5. Dynamic 3D Quantum Server Rack & Cloud Infrastructure */
export function buildServerRack(line, scriptContext) {
  const g = new THREE.Group();
  g.position.set(0, 1.75, 0.0);

  // Floating sleek server module
  const rackGeo = new THREE.BoxGeometry(1.2, 0.6, 0.4);
  const rackMat = new THREE.MeshStandardMaterial({
    color: '#0F172A',
    roughness: 0.25,
    metalness: 0.85
  });
  const rack = new THREE.Mesh(rackGeo, rackMat);
  g.add(rack);

  // Glowing LED rack lines
  for (let y = -0.2; y <= 0.2; y += 0.1) {
    const led = new THREE.Mesh(
      new THREE.BoxGeometry(1.05, 0.03, 0.04),
      new THREE.MeshBasicMaterial({ color: CYAN_NEON })
    );
    led.position.set(0, y, 0.21);
    rack.add(led);
  }

  // Floating HUD badge above rack
  const c = document.createElement('canvas');
  c.width = 512;
  c.height = 140;
  const ctx = c.getContext('2d');
  ctx.fillStyle = 'rgba(15, 23, 42, 0.92)';
  ctx.roundRect(6, 6, 500, 128, 14);
  ctx.fill();
  ctx.strokeStyle = '#10B981';
  ctx.lineWidth = 3;
  ctx.stroke();

  ctx.fillStyle = '#10B981';
  ctx.font = '900 36px Inter, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('1-CLICK CONTAINER DEPLOY', 256, 58);

  ctx.fillStyle = '#94A3B8';
  ctx.font = 'bold 20px Inter, sans-serif';
  ctx.fillText('LIGHTWEIGHT ◈ ZERO OVERHEAD', 256, 102);

  const tex = new THREE.CanvasTexture(c);
  const hud = new THREE.Mesh(
    new THREE.PlaneGeometry(1.2, 0.33),
    new THREE.MeshBasicMaterial({ map: tex, transparent: true })
  );
  hud.position.set(0, 0.55, 0);
  g.add(hud);

  g.update = (t) => {
    rack.position.y = Math.sin(t * 2.8) * 0.04;
    rack.rotation.y = Math.sin(t * 1.4) * 0.06;
    hud.position.y = 0.55 + Math.sin(t * 2.8) * 0.04;
  };

  return g;
}

/** 6. Dynamic Final CTA Hologram Card */
export function buildCtaHoloCard(line, scriptContext) {
  const g = new THREE.Group();
  g.position.set(0, 1.75, 0.0);

  const keyword = scriptContext.cta_keyword || 'FAST';

  const c = document.createElement('canvas');
  c.width = 640;
  c.height = 360;
  const ctx = c.getContext('2d');
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;

  const cardGeo = new THREE.PlaneGeometry(1.35, 0.76);
  const cardMat = new THREE.MeshBasicMaterial({
    map: tex,
    transparent: true,
    opacity: 0.95,
    side: THREE.DoubleSide
  });
  const card = new THREE.Mesh(cardGeo, cardMat);
  g.add(card);

  const border = new THREE.LineSegments(
    new THREE.EdgesGeometry(cardGeo),
    new THREE.LineBasicMaterial({ color: MAGENTA_NEON })
  );
  card.add(border);

  g.update = (t) => {
    ctx.clearRect(0, 0, 640, 360);

    ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
    ctx.roundRect(10, 10, 620, 340, 22);
    ctx.fill();

    ctx.fillStyle = '#FF2A85';
    ctx.font = '900 28px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('◈ INSTANT ACCESS LINK ◈', 320, 64);

    // Glowing Keyword Pill
    ctx.fillStyle = '#00F0FF';
    ctx.roundRect(80, 100, 480, 120, 20);
    ctx.fill();

    ctx.fillStyle = '#0A0F1D';
    ctx.font = '900 64px Inter, sans-serif';
    ctx.fillText(`"${keyword}"`, 320, 185);

    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 24px Inter, sans-serif';
    ctx.fillText(`COMMENT "${keyword}" BELOW FOR LINK`, 320, 275);

    ctx.fillStyle = '#10B981';
    ctx.font = 'bold 20px Inter, sans-serif';
    ctx.fillText('⚡ SENT AUTOMATICALLY VIA DM', 320, 312);

    tex.needsUpdate = true;
    card.position.y = Math.sin(t * 3.2) * 0.04;
    card.scale.setScalar(1 + Math.sin(t * 4.5) * 0.02);
  };

  return g;
}

/** Master Dynamic Topic Prop Selector */
export function createDynamicTopicProp(line, scriptContext, index, isLast) {
  if (isLast) {
    return buildCtaHoloCard(line, scriptContext);
  }

  const h = (line.header || '').toUpperCase();
  const txt = (line.text || '').toUpperCase();
  const comb = h + ' ' + txt;

  if (comb.includes('SPEED') || comb.includes('FAST') || comb.includes('SECOND') || comb.includes('MINUTE') || comb.includes('INSTANT') || comb.includes('BENCHMARK')) {
    return buildSpeedGauge(line, scriptContext);
  }

  if (comb.includes('FREE') || comb.includes('PRICE') || comb.includes('COST') || comb.includes('$') || comb.includes('PAY') || comb.includes('DOLLAR')) {
    return buildPriceSlicer(line, scriptContext);
  }

  if (comb.includes('SERVER') || comb.includes('CLOUD') || comb.includes('DASHBOARD') || comb.includes('DOCKER') || comb.includes('HOST') || comb.includes('PANEL')) {
    return buildServerRack(line, scriptContext);
  }

  if (comb.includes('MODEL') || comb.includes('NEURAL') || comb.includes('AI') || comb.includes('WEIGHT') || comb.includes('REASON') || comb.includes('INTELLIGENCE')) {
    return buildNeuralCore(line, scriptContext);
  }

  // Default to interactive code / agent terminal
  return buildCodeTerminal(line, scriptContext);
}
