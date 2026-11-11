// Dev-Studio Night Studio Environment & 3D Holographic Showcase Props
import * as THREE from 'three';

const CYAN_GLOW = '#00F0FF';
const AMBER_GLOW = '#FF9800';
const GOLD = '#F5C518';
const EMERALD_GREEN = '#10B981';

/** Modern Night Loft Developer Studio with Panoramic City Bokeh Window */
export function techStudio() {
  const g = new THREE.Group();

  // 1. Dark Studio Floor (Polished Charcoal Concrete)
  const floorMat = new THREE.MeshStandardMaterial({
    color: '#0B0F19',
    roughness: 0.35,
    metalness: 0.15
  });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(36, 36), floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -0.01;
  floor.receiveShadow = true;
  g.add(floor);

  // 2. Night Sky Background behind window
  const skyMat = new THREE.MeshBasicMaterial({ color: '#05070E' });
  const sky = new THREE.Mesh(new THREE.PlaneGeometry(42, 22), skyMat);
  sky.position.set(0, 9.5, -6.5);
  g.add(sky);

  // 3. Panoramic Glass Window Frame
  const frameMat = new THREE.MeshStandardMaterial({ color: '#1E293B', roughness: 0.5, metalness: 0.3 });
  // Horizontal bars
  for (let y = 1.2; y <= 16; y += 4.5) {
    const hBar = new THREE.Mesh(new THREE.BoxGeometry(38, 0.08, 0.1), frameMat);
    hBar.position.set(0, y, -5.8);
    g.add(hBar);
  }
  // Vertical mullions
  for (let x = -16; x <= 16; x += 4.8) {
    const vBar = new THREE.Mesh(new THREE.BoxGeometry(0.1, 18, 0.1), frameMat);
    vBar.position.set(x, 9, -5.8);
    g.add(vBar);
  }

  // 4. Distant Metropolitan Skyline & Architectural Window Lights (Beyond glass)
  const skylineGroup = new THREE.Group();
  const bldgMat = new THREE.MeshStandardMaterial({
    color: '#080C14',
    roughness: 0.9,
    metalness: 0.1
  });
  const winColors = ['#FDE68A', '#FEF3C7', '#F59E0B', '#38BDF8', '#94A3B8'];

  // Distant building silhouettes
  const buildings = [
    { x: -14, w: 5.5, h: 14, z: -7.5 },
    { x: -8.5, w: 4.8, h: 11, z: -7.2 },
    { x: -4, w: 4.0, h: 16, z: -8.0 },
    { x: 1.5, w: 5.2, h: 13, z: -7.4 },
    { x: 7.2, w: 4.6, h: 17, z: -8.2 },
    { x: 12.5, w: 5.8, h: 12, z: -7.6 },
    { x: 18, w: 6.0, h: 15, z: -8.5 }
  ];

  buildings.forEach(b => {
    const tower = new THREE.Mesh(new THREE.BoxGeometry(b.w, b.h, 2.0), bldgMat);
    tower.position.set(b.x, b.h / 2, b.z);
    skylineGroup.add(tower);

    // Architectural micro-window grid on building face
    const cols = Math.floor(b.w / 0.45);
    const rows = Math.floor(b.h / 0.55);
    for (let r = 2; r < rows - 1; r++) {
      for (let c = 0; c < cols; c++) {
        // Randomly lit office windows (35% lit rate)
        if (Math.random() < 0.35) {
          const wx = b.x - b.w / 2 + 0.3 + c * 0.45;
          const wy = 0.5 + r * 0.55;
          const col = winColors[Math.floor(Math.random() * winColors.length)];
          const winMesh = new THREE.Mesh(
            new THREE.PlaneGeometry(0.12, 0.16),
            new THREE.MeshBasicMaterial({
              color: col,
              transparent: true,
              opacity: 0.25 + Math.random() * 0.55
            })
          );
          winMesh.position.set(wx, wy, b.z + 1.01);
          skylineGroup.add(winMesh);
        }
      }
    }
  });
  g.add(skylineGroup);

  // 5. Solid Walnut Developer Desk (Spanning z = -0.10 to +0.60)
  const deskMat = new THREE.MeshStandardMaterial({
    color: '#3B2314', // Rich dark walnut
    roughness: 0.42,
    metalness: 0.08
  });
  const deskTop = new THREE.Mesh(new THREE.BoxGeometry(4.2, 0.08, 0.70), deskMat);
  deskTop.position.set(0, 0.74, 0.25);
  deskTop.receiveShadow = true;
  deskTop.castShadow = true;
  g.add(deskTop);

  // Desk Legs
  const legMat = new THREE.MeshStandardMaterial({ color: '#0F172A', metalness: 0.7, roughness: 0.3 });
  const legL = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.74, 0.65), legMat);
  const legR = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.74, 0.65), legMat);
  legL.position.set(-1.95, 0.37, 0.25);
  legR.position.set(1.95, 0.37, 0.25);
  g.add(legL);
  g.add(legR);

  // 6. Desk Atmosphere: Ultrawide Laptop / Monitor + Mug (Offset to DevGuy's left so body is visible)
  const laptopGroup = new THREE.Group();
  laptopGroup.position.set(-1.18, 0.79, 0.18);
  laptopGroup.rotation.y = 0.32; // Angled naturally toward developer

  const laptopBase = new THREE.Mesh(
    new THREE.BoxGeometry(0.70, 0.016, 0.44),
    new THREE.MeshStandardMaterial({ color: '#64748B', metalness: 0.8, roughness: 0.25 })
  );
  laptopGroup.add(laptopBase);

  const screenGroup = new THREE.Group();
  screenGroup.position.set(0, 0.01, 0.20);
  const screenLid = new THREE.Mesh(
    new THREE.BoxGeometry(0.70, 0.40, 0.014),
    new THREE.MeshStandardMaterial({ color: '#334155', metalness: 0.7 })
  );
  screenLid.position.y = 0.20;
  screenGroup.add(screenLid);

  // Glowing Screen Texture (Facing DevGuy)
  const scrCanvas = document.createElement('canvas');
  scrCanvas.width = 512; scrCanvas.height = 320;
  const sctx = scrCanvas.getContext('2d');
  sctx.fillStyle = '#090D16'; sctx.fillRect(0, 0, 512, 320);
  sctx.fillStyle = '#00F0FF'; sctx.font = 'bold 18px monospace';
  sctx.fillText('$ git clone https://github.com/repo', 24, 40);
  sctx.fillStyle = '#34D399';
  sctx.fillText('✓ Connecting to local neural engine...', 24, 75);
  sctx.fillStyle = '#94A3B8';
  for (let y = 110; y < 300; y += 26) {
    sctx.fillText(`> loading model weights layer_${(y-110)/26} [100%]`, 24, y);
  }
  const scrTex = new THREE.CanvasTexture(scrCanvas);
  const scrFace = new THREE.Mesh(new THREE.PlaneGeometry(0.67, 0.37), new THREE.MeshBasicMaterial({ map: scrTex }));
  scrFace.position.set(0, 0.20, -0.008);
  screenGroup.add(scrFace);
  laptopGroup.add(screenGroup);
  g.add(laptopGroup);

  // Minimalist Coffee Mug
  const mug = new THREE.Mesh(
    new THREE.CylinderGeometry(0.065, 0.055, 0.12, 16),
    new THREE.MeshStandardMaterial({ color: '#F1F5F9', roughness: 0.3 })
  );
  mug.position.set(1.4, 0.85, 0.35);
  g.add(mug);

  // Soft floating ambient dust particles
  const pCount = 50;
  const posArr = new Float32Array(pCount * 3);
  for (let i = 0; i < pCount * 3; i += 3) {
    posArr[i] = (Math.random() - 0.5) * 8;
    posArr[i + 1] = 0.8 + Math.random() * 3.5;
    posArr[i + 2] = (Math.random() - 0.5) * 4;
  }
  const pGeo = new THREE.BufferGeometry();
  pGeo.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
  const pMat = new THREE.PointsMaterial({ color: '#38BDF8', size: 0.035, transparent: true, opacity: 0.5 });
  g.add(new THREE.Points(pGeo, pMat));

  return g;
}

/** 2. Dynamic Showcase Props Engine */
export function createDynamicTopicProp(lineOrType, scriptContext = {}, idx = 0, isLast = false) {
  const g = new THREE.Group();

  let propType = typeof lineOrType === 'string' ? lineOrType : (lineOrType.prop || '');
  const lineText = typeof lineOrType === 'object' ? ((lineOrType.text || '') + ' ' + (lineOrType.header || '')).toLowerCase() : '';
  const toolName = scriptContext.tool_name || scriptContext.title || 'AI Studio';
  const ctaKw = scriptContext.cta_keyword || 'STUDIO';

  if (!propType) {
    if (isLast || lineText.includes('comment') || lineText.includes('send') || lineText.includes('follow')) {
      propType = 'cta_pill';
    } else if (lineText.includes('$') || lineText.includes('month') || lineText.includes('paying') || lineText.includes('bill') || idx === 0) {
      propType = 'subscription_card';
    } else if (lineText.includes('star') || lineText.includes('github') || lineText.includes('open source') || lineText.includes('repo')) {
      propType = 'github_stars';
    } else if (lineText.includes('image') || lineText.includes('video') || lineText.includes('models') || lineText.includes('feature')) {
      propType = 'feature_badges';
    } else if (lineText.includes('local') || lineText.includes('computer') || lineText.includes('credit') || lineText.includes('filter')) {
      propType = 'pc_rig';
    } else {
      propType = 'github_stars';
    }
  }

  if (propType === 'subscription_card' || propType === 'bill' || propType === 'saas' || propType === 'alert_card' || propType === 'bill_card') {
    // Dynamic Pain / Alert Card (Pricing, Rate Limits, Overload, or Cloud Paywall)
    const c = document.createElement('canvas');
    c.width = 512; c.height = 200;
    const ctx = c.getContext('2d');
    ctx.fillStyle = '#0F172A';
    ctx.roundRect(10, 10, 492, 180, 24);
    ctx.fill();
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 4;
    ctx.stroke();

    // Determine dynamic alert headline & details from line text/header
    let topLabel = 'ALERT DETECTED';
    let mainMetric = '$49.00 / month';
    let subtext = 'Renewed automatically';
    let metricColor = '#F59E0B'; // Amber default

    const combined = lineText.toLowerCase();

    // 1. Specific Dollar Amounts
    const priceMatch = combined.match(/\$(\d+)/) || combined.match(/(\d+)\s*dollars?/);
    if (priceMatch) {
      const amt = priceMatch[1];
      topLabel = `${toolName.toUpperCase()} SUBSCRIPTION`;
      mainMetric = `$${amt}.00 / month`;
      subtext = 'Recurring monthly fee';
      metricColor = '#EF4444'; // Red
    } else if (combined.includes('rate limit') || combined.includes('quota') || combined.includes('429')) {
      topLabel = 'API USAGE NOTICE';
      mainMetric = 'RATE LIMIT HIT';
      subtext = 'Quota depleted · 429 Error';
      metricColor = '#EF4444';
    } else if (combined.includes('busy') || combined.includes('overload') || combined.includes('503') || combined.includes('down')) {
      topLabel = 'CLOUD SERVER ALERT';
      mainMetric = 'MODEL OVERLOADED';
      subtext = 'Service unavailable · 503';
      metricColor = '#F59E0B';
    } else if (combined.includes('censor') || combined.includes('blocked') || combined.includes('ban')) {
      topLabel = 'PROMPT RESTRICTION';
      mainMetric = 'CONTENT BLOCKED';
      subtext = 'Cloud safety filter triggered';
      metricColor = '#EF4444';
    } else if (combined.includes('queue') || combined.includes('waiting')) {
      topLabel = 'GPU QUEUE ESTIMATE';
      mainMetric = 'QUEUE #458';
      subtext = 'Estimated wait: 42 minutes';
      metricColor = '#F59E0B';
    } else {
      topLabel = `${toolName.toUpperCase()} CHARGE`;
      mainMetric = '$29.00 / month';
      subtext = 'Monthly recurring paywall';
    }

    // Header badge
    ctx.fillStyle = '#94A3B8';
    ctx.font = 'bold 24px Inter, sans-serif';
    ctx.fillText(topLabel.slice(0, 28), 40, 64);

    // Main metric
    ctx.fillStyle = metricColor;
    ctx.font = '900 44px Inter, sans-serif';
    ctx.fillText(mainMetric, 40, 124);

    // Context subtext
    ctx.fillStyle = '#64748B';
    ctx.font = '22px Inter, sans-serif';
    ctx.fillText(subtext, 40, 164);

    const tex = new THREE.CanvasTexture(c);
    const cardMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(1.08, 0.46),
      new THREE.MeshBasicMaterial({ map: tex, transparent: true })
    );
    cardMesh.position.set(0.0, 1.62, 0.25);
    g.add(cardMesh);
    return g;
  }

  if (propType === 'github_stars' || propType === 'repo' || propType === 'stars' || propType === 'star_plaque') {
    // Dynamic 3D GitHub Star Plaque with real-time extracted star metrics
    const c = document.createElement('canvas');
    c.width = 512; c.height = 240;
    const ctx = c.getContext('2d');
    ctx.fillStyle = '#0F172A';
    ctx.roundRect(10, 10, 492, 220, 28);
    ctx.fill();
    ctx.strokeStyle = '#38BDF8';
    ctx.lineWidth = 6;
    ctx.stroke();

    ctx.fillStyle = '#38BDF8';
    ctx.font = 'bold 28px Inter, sans-serif';
    ctx.fillText('OPEN SOURCE REPOSITORY', 40, 58);

    ctx.fillStyle = '#FFFFFF';
    ctx.font = '900 42px Inter, sans-serif';
    ctx.fillText((toolName || 'AI Studio').slice(0, 20), 40, 118);

    // Extract dynamic star count or fallback gracefully
    let starLabel = '★ 32.2k stars';
    const starMatch = lineText.match(/(\d+[\.,]?\d*k?)\s*stars?/) || lineText.match(/(\d+)\s*thousand/);
    if (starMatch) {
      const num = starMatch[1];
      starLabel = `★ ${num}${num.includes('k') ? '' : 'k'} stars`;
    }

    // Star Pill
    ctx.fillStyle = '#FEF08A';
    ctx.beginPath();
    ctx.roundRect(40, 146, 260, 60, 30);
    ctx.fill();
    ctx.fillStyle = '#854D0E';
    ctx.font = '900 34px Inter, sans-serif';
    ctx.fillText(starLabel, 60, 189);

    const tex = new THREE.CanvasTexture(c);
    const mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(1.08, 0.52),
      new THREE.MeshBasicMaterial({ map: tex, transparent: true })
    );
    mesh.position.set(0.0, 1.62, 0.25);
    g.add(mesh);
    return g;
  }

  if (propType === 'feature_badges' || propType === 'badges' || propType === 'features') {
    // Floating Glossy Feature Badges ([Image], [Video], [Local])
    const features = ['Image', 'Video', 'Uncensored', 'Local 0$'];
    const colOffsets = [-0.9, -0.3, 0.3, 0.9];
    features.forEach((feat, i) => {
      const c = document.createElement('canvas');
      c.width = 256; c.height = 140;
      const ctx = c.getContext('2d');
      ctx.fillStyle = '#1E293B';
      ctx.roundRect(8, 8, 240, 124, 20);
      ctx.fill();
      ctx.strokeStyle = i % 2 === 0 ? '#38BDF8' : '#F59E0B';
      ctx.lineWidth = 6;
      ctx.stroke();

      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 36px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(feat, 128, 80);

      const tex = new THREE.CanvasTexture(c);
      const bMesh = new THREE.Mesh(
        new THREE.PlaneGeometry(0.75, 0.42),
        new THREE.MeshBasicMaterial({ map: tex, transparent: true })
      );
      bMesh.position.set(colOffsets[i], 1.6 + (i % 2 === 0 ? 0.2 : -0.1), 0);
      g.add(bMesh);
    });
    return g;
  }

  if (propType === 'pc_rig' || propType === 'local' || propType === 'hardware') {
    // 3D Glass Desktop Gaming/Local PC Tower with rotating illuminated RGB fans
    const towerGeo = new THREE.BoxGeometry(0.8, 1.2, 0.8);
    const towerMat = new THREE.MeshStandardMaterial({ color: '#0F172A', metalness: 0.8, roughness: 0.2 });
    const tower = new THREE.Mesh(towerGeo, towerMat);
    tower.position.y = 1.35;
    g.add(tower);

    // Glass Front/Side Panel
    const glassMat = new THREE.MeshPhysicalMaterial({
      color: '#00F0FF',
      transparent: true,
      opacity: 0.35,
      roughness: 0.05,
      metalness: 0.1
    });
    const glass = new THREE.Mesh(new THREE.PlaneGeometry(0.76, 1.14), glassMat);
    glass.position.set(0, 1.35, 0.41);
    g.add(glass);

    // 2 Illuminated Glowing Cooling Fans
    const fanMat = new THREE.MeshBasicMaterial({ color: CYAN_GLOW });
    const fan1 = new THREE.Mesh(new THREE.TorusGeometry(0.22, 0.03, 16, 24), fanMat);
    const fan2 = new THREE.Mesh(new THREE.TorusGeometry(0.22, 0.03, 16, 24), fanMat);
    fan1.position.set(0, 1.65, 0.32);
    fan2.position.set(0, 1.05, 0.32);
    g.add(fan1);
    g.add(fan2);

    return g;
  }

  if (propType === 'cta_pill' || propType === 'comment_pill' || propType === 'cta') {
    // Floating Interactive Comment Bar: "[ STUDIO  ⬆ ]"
    const kw = (toolName || 'STUDIO').toUpperCase();
    const c = document.createElement('canvas');
    c.width = 512; c.height = 140;
    const ctx = c.getContext('2d');
    ctx.fillStyle = '#0F172A';
    ctx.roundRect(10, 10, 492, 120, 30);
    ctx.fill();
    ctx.strokeStyle = '#F59E0B';
    ctx.lineWidth = 5;
    ctx.stroke();

    ctx.fillStyle = '#FFFFFF';
    ctx.font = '900 48px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`Comment "${kw}" 🚀`, 256, 82);

    const tex = new THREE.CanvasTexture(c);
    const mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(1.9, 0.52),
      new THREE.MeshBasicMaterial({ map: tex, transparent: true })
    );
    mesh.position.set(0, 1.45, 0);
    g.add(mesh);
    return g;
  }

  // Default clean floating card fallback
  const c = document.createElement('canvas');
  c.width = 512; c.height = 200;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#0F172A';
  ctx.roundRect(10, 10, 492, 180, 24);
  ctx.fill();
  ctx.fillStyle = '#FFFFFF';
  ctx.font = 'bold 42px Inter, sans-serif';
  ctx.fillText(toolName || 'Open Source', 40, 110);
  const tex = new THREE.CanvasTexture(c);
  const dMesh = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 0.65), new THREE.MeshBasicMaterial({ map: tex, transparent: true }));
  dMesh.position.set(0, 1.45, 0);
  g.add(dMesh);
  return g;
}
