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

  // 4. Glowing City Bokeh Lights (Skyline orbs through glass)
  const bokehColors = ['#FCD34D', '#F59E0B', '#38BDF8', '#818CF8', '#FB7185', '#34D399'];
  const bokehGroup = new THREE.Group();
  for (let i = 0; i < 48; i++) {
    const col = bokehColors[Math.floor(Math.random() * bokehColors.length)];
    const r = 0.12 + Math.random() * 0.28;
    const orb = new THREE.Mesh(
      new THREE.SphereGeometry(r, 16, 16),
      new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.45 + Math.random() * 0.35 })
    );
    orb.position.set(
      (Math.random() - 0.5) * 32,
      2.5 + Math.random() * 9.5,
      -6.2 + Math.random() * 0.3
    );
    bokehGroup.add(orb);
  }
  g.add(bokehGroup);

  // 5. Solid Walnut Developer Desk
  const deskMat = new THREE.MeshStandardMaterial({
    color: '#3B2314', // Rich dark walnut
    roughness: 0.42,
    metalness: 0.08
  });
  const deskTop = new THREE.Mesh(new THREE.BoxGeometry(4.8, 0.14, 1.8), deskMat);
  deskTop.position.set(0, 0.72, 0.1);
  deskTop.receiveShadow = true;
  deskTop.castShadow = true;
  g.add(deskTop);

  // Desk Legs
  const legMat = new THREE.MeshStandardMaterial({ color: '#0F172A', metalness: 0.7, roughness: 0.3 });
  const legL = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.72, 1.6), legMat);
  const legR = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.72, 1.6), legMat);
  legL.position.set(-2.15, 0.36, 0.1);
  legR.position.set(2.15, 0.36, 0.1);
  g.add(legL);
  g.add(legR);

  // 6. Desk Atmosphere: Ultrawide Laptop / Monitor + Mug
  const laptopBase = new THREE.Mesh(
    new THREE.BoxGeometry(0.85, 0.018, 0.55),
    new THREE.MeshStandardMaterial({ color: '#64748B', metalness: 0.8, roughness: 0.25 })
  );
  laptopBase.position.set(-0.7, 0.8, 0.25);
  g.add(laptopBase);

  const screenGroup = new THREE.Group();
  screenGroup.position.set(-0.7, 0.81, 0.0);
  const screenLid = new THREE.Mesh(
    new THREE.BoxGeometry(0.85, 0.52, 0.015),
    new THREE.MeshStandardMaterial({ color: '#334155', metalness: 0.7 })
  );
  screenLid.position.y = 0.26;
  screenGroup.add(screenLid);

  // Glowing Screen Texture (Cyber code lines)
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
  const scrFace = new THREE.Mesh(new THREE.PlaneGeometry(0.81, 0.48), new THREE.MeshBasicMaterial({ map: scrTex }));
  scrFace.position.set(0, 0.26, 0.009);
  screenGroup.add(scrFace);
  g.add(screenGroup);

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

  if (propType === 'subscription_card' || propType === 'bill' || propType === 'saas') {
    // Floating SaaS Bill Card: "$49.00 / month - Renewed today"
    const c = document.createElement('canvas');
    c.width = 512; c.height = 200;
    const ctx = c.getContext('2d');
    ctx.fillStyle = '#0F172A';
    ctx.roundRect(10, 10, 492, 180, 24);
    ctx.fill();
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 4;
    ctx.stroke();

    // App name & price
    ctx.fillStyle = '#F8FAFC';
    ctx.font = 'bold 36px Inter, sans-serif';
    ctx.fillText(toolName || 'Subscription', 40, 72);
    ctx.fillStyle = '#F59E0B'; // Amber alert
    ctx.font = '900 44px Inter, sans-serif';
    ctx.fillText('$49.00 / month', 40, 130);
    ctx.fillStyle = '#94A3B8';
    ctx.font = '24px Inter, sans-serif';
    ctx.fillText('Renewed today', 40, 168);

    const tex = new THREE.CanvasTexture(c);
    const cardMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(1.6, 0.65),
      new THREE.MeshBasicMaterial({ map: tex, transparent: true })
    );
    cardMesh.position.set(0, 1.45, 0);
    g.add(cardMesh);
    return g;
  }

  if (propType === 'github_stars' || propType === 'repo' || propType === 'stars') {
    // Floating 3D GitHub Star Plaque: "★ 32.2k Stars"
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
    ctx.font = 'bold 30px Inter, sans-serif';
    ctx.fillText('OPEN SOURCE REPOSITORY', 40, 60);

    ctx.fillStyle = '#FFFFFF';
    ctx.font = '900 46px Inter, sans-serif';
    ctx.fillText(toolName || 'AI Studio', 40, 120);

    // Star Pill
    ctx.fillStyle = '#FEF08A';
    ctx.beginPath();
    ctx.roundRect(40, 150, 240, 60, 30);
    ctx.fill();
    ctx.fillStyle = '#854D0E';
    ctx.font = '900 36px Inter, sans-serif';
    ctx.fillText('★ 32.2k stars', 62, 194);

    const tex = new THREE.CanvasTexture(c);
    const mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(1.8, 0.85),
      new THREE.MeshBasicMaterial({ map: tex, transparent: true })
    );
    mesh.position.set(0, 1.5, 0);
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
