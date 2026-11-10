// 3D Procedural Props for Claude-Desk Viral Tech Format
import * as THREE from 'three';

const INK = '#0F111A';
const CYAN_GLOW = '#00F0FF';
const RED_ACCENT = '#FF3B30';

/** Modern Tech Studio Desk + Floor */
export function studioDesk() {
  const g = new THREE.Group();

  // Studio Floor
  const floorGeo = new THREE.PlaneGeometry(30, 30);
  const floorMat = new THREE.MeshStandardMaterial({
    color: '#0D0E15',
    roughness: 0.8,
    metalness: 0.2
  });
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -0.01;
  floor.receiveShadow = true;
  g.add(floor);

  // Desk Surface (Sleek dark matte with beveled front)
  const deskMat = new THREE.MeshStandardMaterial({
    color: '#1A1C29',
    roughness: 0.35,
    metalness: 0.3
  });
  const deskTop = new THREE.Mesh(new THREE.BoxGeometry(7.2, 0.25, 2.8), deskMat);
  deskTop.position.set(0, 0.88, 0.2);
  deskTop.castShadow = true;
  deskTop.receiveShadow = true;
  g.add(deskTop);

  // Glowing neon edge accent strip
  const stripMat = new THREE.MeshBasicMaterial({ color: CYAN_GLOW });
  const strip = new THREE.Mesh(new THREE.BoxGeometry(7.22, 0.04, 0.05), stripMat);
  strip.position.set(0, 0.98, 1.6);
  g.add(strip);

  // Desk Legs
  const legMat = new THREE.MeshStandardMaterial({ color: '#11121A', roughness: 0.5 });
  [-3.2, 3.2].forEach((x) => {
    const leg = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.88, 2.2), legMat);
    leg.position.set(x, 0.44, 0.2);
    leg.castShadow = true;
    g.add(leg);
  });

  return g;
}

/** 1. Sword Slicing $1B Block */
export function swordCutProp() {
  const g = new THREE.Group();
  g.position.set(0, 1.4, 0.2);

  // Glowing energy katana/sword
  const bladeMat = new THREE.MeshBasicMaterial({ color: CYAN_GLOW });
  const blade = new THREE.Mesh(new THREE.BoxGeometry(0.06, 2.2, 0.18), bladeMat);
  blade.rotation.z = 0.55;
  blade.position.set(-0.3, 0.5, 0.4);
  g.add(blade);

  // Golden $1,000,000,000 block split in two halves
  const goldMat = new THREE.MeshStandardMaterial({
    color: '#FFD700',
    metalness: 0.85,
    roughness: 0.2
  });

  const makeHalf = (sign) => {
    const half = new THREE.Group();
    const b = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.8, 0.4), goldMat);
    b.castShadow = true;
    half.add(b);

    // Text on block face
    const c = document.createElement('canvas');
    c.width = 256; c.height = 256;
    const ctx = c.getContext('2d');
    ctx.fillStyle = '#FFD700';
    ctx.fillRect(0, 0, 256, 256);
    ctx.fillStyle = '#1A1100';
    ctx.font = '900 48px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(sign < 0 ? '$1B' : 'JARVIS', 128, 128);
    const tex = new THREE.CanvasTexture(c);
    tex.needsUpdate = true;
    const label = new THREE.Mesh(new THREE.PlaneGeometry(0.85, 0.75), new THREE.MeshBasicMaterial({ map: tex }));
    label.position.set(0, 0, 0.21);
    half.add(label);

    return half;
  };

  const halfL = makeHalf(-1);
  const halfR = makeHalf(1);
  halfL.position.set(-0.55, 0, 0);
  halfR.position.set(0.55, 0, 0);
  g.add(halfL);
  g.add(halfR);

  g.update = (t) => {
    const cut = Math.min(1, Math.max(0, (t % 4.0) * 1.5));
    halfL.position.x = -0.48 - cut * 0.35;
    halfL.rotation.z = cut * 0.2;
    halfR.position.x = 0.48 + cut * 0.35;
    halfR.rotation.z = -cut * 0.2;
    blade.position.y = 0.5 - cut * 0.4;
  };

  return g;
}

/** 2. Glowing Holographic Orb */
export function glowingOrbProp() {
  const g = new THREE.Group();
  g.position.set(0, 1.45, 0.2);

  // Pedestal
  const pedMat = new THREE.MeshStandardMaterial({ color: '#222536', roughness: 0.3 });
  const ped = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.65, 0.2, 32), pedMat);
  ped.position.y = -0.4;
  g.add(ped);

  // Concentric floating holographic rings
  const ringMat = new THREE.MeshBasicMaterial({ color: CYAN_GLOW, wireframe: true });
  const ring1 = new THREE.Mesh(new THREE.TorusGeometry(0.65, 0.02, 16, 64), ringMat);
  const ring2 = new THREE.Mesh(new THREE.TorusGeometry(0.82, 0.02, 16, 64), ringMat);
  g.add(ring1);
  g.add(ring2);

  // Center Glowing Orb
  const orbMat = new THREE.MeshBasicMaterial({ color: '#E0FAFF' });
  const orb = new THREE.Mesh(new THREE.SphereGeometry(0.38, 32, 32), orbMat);
  g.add(orb);

  g.update = (t) => {
    ring1.rotation.x = t * 2.2;
    ring1.rotation.y = t * 1.5;
    ring2.rotation.y = -t * 1.8;
    ring2.rotation.z = t * 2.5;
    orb.position.y = Math.sin(t * 3) * 0.05;
    orb.scale.setScalar(1 + Math.sin(t * 6) * 0.06);
  };

  return g;
}

/** 3. CRT / Cyberpunk Terminal Monitor */
export function terminalDeskProp() {
  const g = new THREE.Group();
  g.position.set(0, 1.4, 0.1);

  // Monitor casing
  const caseMat = new THREE.MeshStandardMaterial({ color: '#181A24', roughness: 0.4 });
  const casing = new THREE.Mesh(new THREE.BoxGeometry(2.2, 1.4, 0.3), caseMat);
  casing.castShadow = true;
  g.add(casing);

  // Stand
  const stand = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.18, 0.5, 16), caseMat);
  stand.position.set(0, -0.7, 0);
  g.add(stand);

  // Matrix code canvas
  const c = document.createElement('canvas');
  c.width = 512; c.height = 340;
  const ctx = c.getContext('2d');
  const tex = new THREE.CanvasTexture(c);

  const screen = new THREE.Mesh(
    new THREE.PlaneGeometry(2.0, 1.25),
    new THREE.MeshBasicMaterial({ map: tex })
  );
  screen.position.set(0, 0, 0.16);
  g.add(screen);

  const lines = [
    '> git clone https://github.com/open-jarvis',
    '> connecting local neural model: kokoro-v1',
    '> loading calendar & unread emails...',
    '> intelligence briefing ready.',
    '> 100% OFFLINE / ZERO SUBSCRIPTION'
  ];

  g.update = (t) => {
    ctx.fillStyle = '#070A0E';
    ctx.fillRect(0, 0, 512, 340);
    ctx.fillStyle = '#00FF66';
    ctx.font = '700 22px Courier New, monospace';
    const count = Math.min(lines.length, Math.floor(t * 3) + 1);
    for (let i = 0; i < count; i++) {
      ctx.fillText(lines[i], 24, 50 + i * 48);
    }
    // Blinking cursor
    if (Math.sin(t * 10) > 0) {
      ctx.fillRect(24 + (lines[count - 1]?.length || 0) * 13, 50 + (count - 1) * 48 - 18, 12, 22);
    }
    tex.needsUpdate = true;
  };

  g.update(0);

  return g;
}

/** 4. Cascading 3D Envelopes / Falling Papers */
export function fallingLettersProp() {
  const g = new THREE.Group();
  g.position.set(0, 1.05, 0.3);

  const envMat = new THREE.MeshStandardMaterial({ color: '#F7F8FA', roughness: 0.3 });
  const count = 18;
  const letters = [];

  for (let i = 0; i < count; i++) {
    const env = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.04, 0.38), envMat);
    env.castShadow = true;
    env.position.set((Math.random() - 0.5) * 1.8, Math.random() * 2.5, (Math.random() - 0.5) * 1.0);
    env.rotation.set(Math.random() * 0.4, Math.random() * Math.PI, Math.random() * 0.4);
    g.add(env);
    letters.push({ mesh: env, speed: 0.8 + Math.random() * 1.2, rotSpeed: (Math.random() - 0.5) * 2 });
  }

  g.update = (t) => {
    letters.forEach(({ mesh, speed, rotSpeed }) => {
      mesh.position.y -= speed * 0.02;
      mesh.rotation.y += rotSpeed * 0.02;
      if (mesh.position.y < 0.05) {
        mesh.position.y = 2.2 + Math.random() * 0.8;
      }
    });
  };

  return g;
}

/** 5. Downward Scanning Hologram Laser */
export function scannerBeamProp() {
  const g = new THREE.Group();
  g.position.set(0, 1.1, 0.2);

  // Glowing laser fan/cone
  const beamMat = new THREE.MeshBasicMaterial({
    color: CYAN_GLOW,
    transparent: true,
    opacity: 0.28,
    side: THREE.DoubleSide
  });
  const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 1.8, 1.8, 32, 1, true), beamMat);
  beam.position.y = 0.9;
  g.add(beam);

  // Floating notification badges
  const makeBadge = (text, y) => {
    const c = document.createElement('canvas');
    c.width = 320; c.height = 80;
    const ctx = c.getContext('2d');
    ctx.fillStyle = 'rgba(0, 240, 255, 0.85)';
    ctx.roundRect(0, 0, 320, 80, 20);
    ctx.fill();
    ctx.fillStyle = '#060B14';
    ctx.font = '900 28px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, 160, 42);
    const tex = new THREE.CanvasTexture(c);
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 0.3), new THREE.MeshBasicMaterial({ map: tex, transparent: true }));
    mesh.position.set(0, y, 0.2);
    g.add(mesh);
    return mesh;
  };

  const b1 = makeBadge('URGENT: 3 EMAILS', 0.6);
  const b2 = makeBadge('CALENDAR: BRIEFING READY', 1.1);

  g.update = (t) => {
    beam.position.x = Math.sin(t * 3) * 0.5;
    b1.position.y = 0.6 + Math.sin(t * 2) * 0.06;
    b2.position.y = 1.1 + Math.sin(t * 2 + 1) * 0.06;
  };

  return g;
}

/** 6. Holographic Audio Equalizer Waveform */
export function waveformAudioProp() {
  const g = new THREE.Group();
  g.position.set(0, 1.4, 0.3);

  const barCount = 12;
  const bars = [];
  const barMat = new THREE.MeshBasicMaterial({ color: CYAN_GLOW });

  for (let i = 0; i < barCount; i++) {
    const bar = new THREE.Mesh(new THREE.BoxGeometry(0.08, 1.0, 0.08), barMat);
    bar.position.x = (i - barCount / 2) * 0.16;
    g.add(bar);
    bars.push(bar);
  }

  g.update = (t) => {
    bars.forEach((b, i) => {
      const h = Math.abs(Math.sin(t * 10 + i * 0.8)) * 0.8 + 0.15;
      b.scale.y = h;
    });
  };

  return g;
}

/** 7. Black Server Tower ($0 Subscription) */
export function serverTowerProp() {
  const g = new THREE.Group();
  g.position.set(0, 1.35, 0.2);

  const rackMat = new THREE.MeshStandardMaterial({ color: '#13141C', roughness: 0.35 });
  const rack = new THREE.Mesh(new THREE.BoxGeometry(1.5, 1.8, 0.8), rackMat);
  rack.castShadow = true;
  g.add(rack);

  // Floating $0.00 Badge
  const c = document.createElement('canvas');
  c.width = 400; c.height = 120;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#FF3B30';
  ctx.roundRect(0, 0, 400, 120, 24);
  ctx.fill();
  ctx.fillStyle = '#FFFFFF';
  ctx.font = '900 48px Inter, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('$0 / 100% LOCAL', 200, 62);
  const tex = new THREE.CanvasTexture(c);
  tex.needsUpdate = true;
  const badge = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 0.42), new THREE.MeshBasicMaterial({ map: tex }));
  badge.position.set(0, 0.2, 0.42);
  g.add(badge);

  g.update = (t) => {
    badge.scale.setScalar(1 + Math.sin(t * 5) * 0.04);
  };

  return g;
}

/** 8. 3D Instagram Comment Call-To-Action UI */
export function commentUiProp(keyword = 'JARVIS') {
  const g = new THREE.Group();
  g.position.set(0, 1.35, 0.4);

  const c = document.createElement('canvas');
  c.width = 800; c.height = 200;
  const ctx = c.getContext('2d');
  const tex = new THREE.CanvasTexture(c);

  const panel = new THREE.Mesh(
    new THREE.PlaneGeometry(2.4, 0.6),
    new THREE.MeshBasicMaterial({ map: tex, transparent: true })
  );
  panel.castShadow = true;
  g.add(panel);

  g.update = (t) => {
    ctx.clearRect(0, 0, 800, 200);

    // Dark sleek glass comment pill (matches cyber tech studio look)
    ctx.fillStyle = '#141624';
    ctx.roundRect(10, 10, 780, 180, 36);
    ctx.fill();
    ctx.lineWidth = 4;
    ctx.strokeStyle = '#00F0FF';
    ctx.stroke();

    // User avatar icon
    ctx.fillStyle = '#D95338';
    ctx.beginPath();
    ctx.arc(80, 100, 45, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '900 40px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('C', 80, 102);

    // Typing keyword animation
    const charsToShow = Math.min(keyword.length, Math.floor((t * 5) % (keyword.length + 4)));
    const typed = keyword.slice(0, charsToShow);

    ctx.fillStyle = '#FFFFFF';
    ctx.font = '800 44px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(typed, 160, 102);

    // Blinking cursor
    if (Math.sin(t * 8) > 0) {
      ctx.fillRect(160 + ctx.measureText(typed).width + 4, 75, 5, 50);
    }

    // Glowing vibrant Post button
    ctx.fillStyle = RED_ACCENT;
    ctx.roundRect(620, 50, 140, 100, 24);
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '900 36px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Post', 690, 102);

    tex.needsUpdate = true;
  };

  g.update(0);

  return g;
}
