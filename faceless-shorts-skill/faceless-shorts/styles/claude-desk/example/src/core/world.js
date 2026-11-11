// CurioCut Cinematic Cyber Studio World for Claude-Desk
// Expansive 3D futuristic tech command center with grand depth, glowing hologram stage,
// multi-tier presenter podiums, server monoliths, and panoramic cyber telemetry screens.
import * as THREE from 'three';

const CYAN_NEON = '#00F0FF';
const CORAL_NEON = '#FF6B4A';
const MAGENTA_NEON = '#FF2A85';
const AMBER_GLOW = '#F5B041';
const DARK_SLATE = '#0D111A';
const MID_SLATE = '#161D2B';

/** Procedural carbon & hex circuit grid texture for the grand studio floor */
function makeFloorTexture() {
  const c = document.createElement('canvas');
  c.width = 1024;
  c.height = 1024;
  const ctx = c.getContext('2d');

  // Deep dark carbon-slate base
  ctx.fillStyle = '#0B0F17';
  ctx.fillRect(0, 0, 1024, 1024);

  // Subtle grid tiles
  ctx.strokeStyle = '#182234';
  ctx.lineWidth = 3;
  const tileSize = 64;
  for (let x = 0; x <= 1024; x += tileSize) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, 1024);
    ctx.stroke();
  }
  for (let y = 0; y <= 1024; y += tileSize) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(1024, y);
    ctx.stroke();
  }

  // Glowing circuit nodes
  ctx.fillStyle = 'rgba(0, 240, 255, 0.45)';
  for (let x = 0; x <= 1024; x += tileSize * 2) {
    for (let y = 0; y <= 1024; y += tileSize * 2) {
      if ((x + y) % (tileSize * 4) === 0) {
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }

  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(8, 8);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

/** Procedural animated panoramic hologram display texture */
function makeHoloBackdropTexture() {
  const c = document.createElement('canvas');
  c.width = 1024;
  c.height = 512;
  const ctx = c.getContext('2d');
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return { canvas: c, ctx, tex };
}

export function buildCyberWorld(scene) {
  const worldGroup = new THREE.Group();
  scene.add(worldGroup);

  // 1. Expansive High-Tech Studio Floor
  const floorTex = makeFloorTexture();
  const floorMat = new THREE.MeshStandardMaterial({
    map: floorTex,
    roughness: 0.18,
    metalness: 0.85,
  });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(50, 50), floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = 0;
  floor.receiveShadow = true;
  worldGroup.add(floor);

  // 2. Central Holographic Emitter Stage (Where topic props float majestically)
  const emitterGroup = new THREE.Group();
  emitterGroup.position.set(0, 0.02, 0.0);
  worldGroup.add(emitterGroup);

  // Outer glowing ring
  const outerRingGeo = new THREE.RingGeometry(1.25, 1.35, 64);
  const outerRingMat = new THREE.MeshBasicMaterial({ color: CYAN_NEON, side: THREE.DoubleSide });
  const outerRing = new THREE.Mesh(outerRingGeo, outerRingMat);
  outerRing.rotation.x = -Math.PI / 2;
  emitterGroup.add(outerRing);

  // Inner rotating ring
  const innerRingGeo = new THREE.RingGeometry(0.85, 0.95, 48);
  const innerRingMat = new THREE.MeshBasicMaterial({ color: AMBER_GLOW, side: THREE.DoubleSide });
  const innerRing = new THREE.Mesh(innerRingGeo, innerRingMat);
  innerRing.rotation.x = -Math.PI / 2;
  emitterGroup.add(innerRing);

  // Core projection disc
  const coreDiscGeo = new THREE.CircleGeometry(0.75, 48);
  const coreDiscMat = new THREE.MeshBasicMaterial({
    color: '#002B3D',
    transparent: true,
    opacity: 0.8,
    side: THREE.DoubleSide
  });
  const coreDisc = new THREE.Mesh(coreDiscGeo, coreDiscMat);
  coreDisc.rotation.x = -Math.PI / 2;
  emitterGroup.add(coreDisc);

  // Upward Hologram Light Pillar (Subtle ethereal energy beam)
  const beamGeo = new THREE.CylinderGeometry(1.2, 0.85, 4.0, 32, 1, true);
  const beamMat = new THREE.MeshBasicMaterial({
    color: CYAN_NEON,
    transparent: true,
    opacity: 0.07,
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  });
  const beam = new THREE.Mesh(beamGeo, beamMat);
  beam.position.y = 2.0;
  emitterGroup.add(beam);

  // 3. Dual Presenter Dais / Podiums (Separated with generous cinematic space)
  // Claude Podium (Left side: x = -1.35)
  const claudePodium = new THREE.Group();
  claudePodium.position.set(-1.35, 0, 0.35);
  worldGroup.add(claudePodium);

  const daisGeo = new THREE.CylinderGeometry(0.95, 1.05, 0.12, 36);
  const claudeDaisMat = new THREE.MeshStandardMaterial({
    color: MID_SLATE,
    metalness: 0.75,
    roughness: 0.25
  });
  const claudeDais = new THREE.Mesh(daisGeo, claudeDaisMat);
  claudeDais.position.y = 0.06;
  claudeDais.receiveShadow = true;
  claudePodium.add(claudeDais);

  const claudeTrim = new THREE.Mesh(
    new THREE.TorusGeometry(0.96, 0.025, 16, 48),
    new THREE.MeshBasicMaterial({ color: CORAL_NEON })
  );
  claudeTrim.rotation.x = Math.PI / 2;
  claudeTrim.position.y = 0.12;
  claudePodium.add(claudeTrim);

  // Skeptic Podium (Right side: x = +1.35)
  const skepticPodium = new THREE.Group();
  skepticPodium.position.set(1.35, 0, 0.35);
  worldGroup.add(skepticPodium);

  const skepticDais = new THREE.Mesh(daisGeo, claudeDaisMat);
  skepticDais.position.y = 0.06;
  skepticDais.receiveShadow = true;
  skepticPodium.add(skepticDais);

  const skepticTrim = new THREE.Mesh(
    new THREE.TorusGeometry(0.96, 0.025, 16, 48),
    new THREE.MeshBasicMaterial({ color: MAGENTA_NEON })
  );
  skepticTrim.rotation.x = Math.PI / 2;
  skepticTrim.position.y = 0.12;
  skepticPodium.add(skepticTrim);

  // 4. Background Curved Studio Wall & Quantum Architecture (Grand Depth)
  const wallGeo = new THREE.CylinderGeometry(14, 14, 12, 48, 1, true, -Math.PI * 0.45, Math.PI * 0.9);
  const wallMat = new THREE.MeshStandardMaterial({
    color: '#0E1420',
    roughness: 0.65,
    metalness: 0.4,
    side: THREE.BackSide
  });
  const backWall = new THREE.Mesh(wallGeo, wallMat);
  backWall.position.set(0, 6, -3.5);
  worldGroup.add(backWall);

  // Horizontal Accent Light Ribbons on Back Wall
  [-0.5, 3.5, 7.5].forEach((yPos, i) => {
    const stripGeo = new THREE.CylinderGeometry(13.9, 13.9, 0.08, 48, 1, true, -Math.PI * 0.45, Math.PI * 0.9);
    const stripMat = new THREE.MeshBasicMaterial({
      color: i === 1 ? CYAN_NEON : AMBER_GLOW,
      side: THREE.BackSide
    });
    const strip = new THREE.Mesh(stripGeo, stripMat);
    strip.position.set(0, 6 + yPos, -3.5);
    worldGroup.add(strip);
  });

  // Vertical Architectural Columns / Ribs
  for (let a = -Math.PI * 0.38; a <= Math.PI * 0.38; a += Math.PI * 0.12) {
    const colX = Math.sin(a) * 13.7;
    const colZ = -Math.cos(a) * 13.7 - 3.5;
    const colMesh = new THREE.Mesh(
      new THREE.BoxGeometry(0.4, 12, 0.6),
      new THREE.MeshStandardMaterial({ color: '#162030', roughness: 0.5, metalness: 0.6 })
    );
    colMesh.position.set(colX, 6, colZ);
    colMesh.lookAt(0, 6, -3.5);
    worldGroup.add(colMesh);
  }

  // 5. Far Background Quantum Server Monoliths (Left & Right)
  const buildServerMonolith = (x, z, angle) => {
    const g = new THREE.Group();
    g.position.set(x, 0, z);
    g.rotation.y = angle;

    const tower = new THREE.Mesh(
      new THREE.BoxGeometry(1.6, 7.5, 0.9),
      new THREE.MeshStandardMaterial({ color: '#090D14', roughness: 0.3, metalness: 0.85 })
    );
    tower.position.y = 3.75;
    g.add(tower);

    // Blinking LED activity rack lines
    for (let y = 0.8; y <= 6.8; y += 0.35) {
      const ledBar = new THREE.Mesh(
        new THREE.BoxGeometry(1.3, 0.04, 0.05),
        new THREE.MeshBasicMaterial({ color: (y % 0.7 < 0.2) ? CYAN_NEON : '#007ACC' })
      );
      ledBar.position.set(0, y, 0.46);
      g.add(ledBar);
    }
    return g;
  };

  const serverL = buildServerMonolith(-5.2, -6.8, 0.35);
  const serverR = buildServerMonolith(5.2, -6.8, -0.35);
  worldGroup.add(serverL);
  worldGroup.add(serverR);

  // 6. Holographic Curved Mainframe Backdrop Screen
  const holoBackdrop = makeHoloBackdropTexture();
  const holoScreenGeo = new THREE.PlaneGeometry(8.5, 3.8);
  const holoScreenMat = new THREE.MeshBasicMaterial({
    map: holoBackdrop.tex,
    transparent: true,
    opacity: 0.72,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide
  });
  const holoScreen = new THREE.Mesh(holoScreenGeo, holoScreenMat);
  holoScreen.position.set(0, 4.4, -6.2);
  worldGroup.add(holoScreen);

  // 7. Ambient Cyber Dust & Floating Energy Sparkles
  const count = 120;
  const pCoords = new Float32Array(count * 3);
  for (let i = 0; i < count * 3; i += 3) {
    pCoords[i] = (Math.random() - 0.5) * 16;
    pCoords[i + 1] = Math.random() * 7.5 + 0.2;
    pCoords[i + 2] = (Math.random() - 0.5) * 8 - 1;
  }
  const sparkGeo = new THREE.BufferGeometry();
  sparkGeo.setAttribute('position', new THREE.BufferAttribute(pCoords, 3));
  const sparkMat = new THREE.PointsMaterial({
    color: CYAN_NEON,
    size: 0.075,
    transparent: true,
    opacity: 0.75,
    blending: THREE.AdditiveBlending
  });
  const sparks = new THREE.Points(sparkGeo, sparkMat);
  worldGroup.add(sparks);

  // World Update Loop
  worldGroup.update = (t, scriptContext = {}) => {
    // Rotate center hologram rings
    innerRing.rotation.z = t * 0.8;
    outerRing.rotation.z = -t * 0.5;

    // Pulse emitter beam
    beam.scale.set(1 + Math.sin(t * 3.5) * 0.04, 1, 1 + Math.sin(t * 3.5) * 0.04);
    beamMat.opacity = 0.06 + Math.sin(t * 4.0) * 0.025;

    // Float cyber dust upwards
    const arr = sparkGeo.attributes.position.array;
    for (let i = 1; i < count * 3; i += 3) {
      arr[i] += 0.009;
      if (arr[i] > 8.0) arr[i] = 0.2;
    }
    sparkGeo.attributes.position.needsUpdate = true;

    // Redraw animated hologram mainframe screen
    const ctx = holoBackdrop.ctx;
    ctx.clearRect(0, 0, 1024, 512);

    // Glowing border frame
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.45)';
    ctx.lineWidth = 4;
    ctx.strokeRect(16, 16, 992, 480);

    // Header bar
    ctx.fillStyle = 'rgba(0, 240, 255, 0.15)';
    ctx.fillRect(20, 20, 984, 52);
    ctx.fillStyle = '#00F0FF';
    ctx.font = 'bold 26px Inter, monospace';
    ctx.fillText('◈ AUTONOMOUS AI NEXUS ◈ LIVE TELEMETRY', 42, 56);

    const topicTitle = (scriptContext.title || 'AUTONOMOUS AGENTS').toUpperCase();
    ctx.fillStyle = '#FFB74D';
    ctx.font = 'bold 22px Inter, monospace';
    ctx.textAlign = 'right';
    ctx.fillText(topicTitle.slice(0, 36), 980, 56);
    ctx.textAlign = 'left';

    // Live streaming sine / telemetry wave
    ctx.strokeStyle = '#00F0FF';
    ctx.lineWidth = 3;
    ctx.beginPath();
    for (let x = 40; x < 984; x += 12) {
      const y = 180 + Math.sin(x * 0.02 + t * 4) * 36 + Math.cos(x * 0.04 - t * 2) * 18;
      if (x === 40) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Data bars
    const barWidths = [0.85, 0.62, 0.94, 0.78, 0.55];
    const barLabels = ['MODEL EFFICIENCY', 'INFERENCE SPEED', 'ACCURACY BENCH', 'TOKEN THROUGHPUT', 'AUTONOMY'];
    barWidths.forEach((bw, idx) => {
      const by = 260 + idx * 42;
      ctx.fillStyle = '#64748B';
      ctx.font = '16px Inter, sans-serif';
      ctx.fillText(barLabels[idx], 42, by + 18);

      ctx.fillStyle = 'rgba(30, 41, 59, 0.8)';
      ctx.fillRect(260, by + 4, 680, 20);

      const dynamicFill = Math.min(1, bw * (0.95 + Math.sin(t * 3 + idx) * 0.05));
      ctx.fillStyle = idx === 0 ? '#10B981' : (idx === 1 ? '#00F0FF' : '#FF6B4A');
      ctx.fillRect(260, by + 4, 680 * dynamicFill, 20);
    });

    holoBackdrop.tex.needsUpdate = true;
  };

  return worldGroup;
}
