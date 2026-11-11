// Dynamic Stick Story Narrative Director & Autonomous 2D Cinematic Stage
// 100% Dynamic: builds story-driven illustrated scenes, character acting, and kinetic props for any script.
import { ctx, W, H, clamp, lerp, seg, eo, eio, eob, rnd, rr, circle, ell, line } from './core/lib.js';
import { L, Le, Wd, T } from './core/timing.js';
import * as K from './core/kit.js';

const { P, GROUND, FLOOR } = K;

// ═════════════════════════ PROCEDURAL SCENERY & ROOMS ═════════════════════════

function drawTownHall(lt, d, t, night = false) {
  // Marble / neoclassical council room with wooden wainscoting and pillars
  ctx.fillStyle = night ? '#252B3D' : '#EFEAE1';
  ctx.fillRect(-300, -300, W + 600, FLOOR + 300);

  // Polished mahogany wainscoting
  ctx.fillStyle = night ? '#3A2820' : '#6A432D';
  ctx.fillRect(-300, FLOOR - 320, W + 600, 320);
  ctx.fillStyle = night ? '#2A1B15' : '#523321';
  ctx.fillRect(-300, FLOOR - 340, W + 600, 24);

  // Classical stone pillars
  for (const px of [140, 940]) {
    ctx.fillStyle = night ? '#373F54' : '#DFD7C8';
    ctx.fillRect(px - 45, -300, 90, FLOOR + 300);
    ctx.fillStyle = night ? '#4A546E' : '#EDE6D8';
    ctx.fillRect(px - 58, FLOOR - 350, 116, 30);
    ctx.fillRect(px - 58, 120, 116, 26);
  }

  // Parquet / oak floor
  ctx.fillStyle = night ? '#322521' : '#8B5A36';
  ctx.fillRect(-300, FLOOR, W + 600, H - FLOOR + 300);
  ctx.strokeStyle = night ? '#251A17' : '#724829';
  ctx.lineWidth = 6;
  for (let y = FLOOR + 80; y < H + 300; y += 100) {
    ctx.beginPath(); ctx.moveTo(-300, y); ctx.lineTo(W + 300, y); ctx.stroke();
  }

  // Official municipal podium in center
  ctx.fillStyle = night ? '#442C20' : '#5C3822';
  rr(420, FLOOR - 260, 240, 270, 16); ctx.fill();
  ctx.fillStyle = night ? '#2E1D15' : '#452918';
  rr(400, FLOOR - 280, 280, 32, 10); ctx.fill();

  // Dual microphones
  line([[490, FLOOR - 280], [510, FLOOR - 330]], P.ink, 6);
  circle(510, FLOOR - 335, 12, '#4A5568');
  line([[590, FLOOR - 280], [570, FLOOR - 330]], P.ink, 6);
  circle(570, FLOOR - 335, 12, '#4A5568');

  // American / Municipal Flag on right
  const poleX = 860;
  line([[poleX, FLOOR - 560], [poleX, FLOOR]], '#D4AF37', 10);
  circle(poleX, FLOOR - 565, 16, '#F6E05E');
  // Flag cloth
  ctx.fillStyle = '#C53030';
  ctx.beginPath();
  ctx.moveTo(poleX, FLOOR - 550);
  ctx.quadraticCurveTo(poleX - 80, FLOOR - 530 + Math.sin(t * 3) * 12, poleX - 160, FLOOR - 540);
  ctx.lineTo(poleX - 160, FLOOR - 380);
  ctx.quadraticCurveTo(poleX - 80, FLOOR - 370 + Math.sin(t * 3) * 12, poleX, FLOOR - 390);
  ctx.closePath();
  ctx.fill();

  // Background Citizen Spectators
  for (let i = 0; i < 2; i++) {
    const cx = i === 0 ? 250 : 830;
    K.person({
      x: cx, y: GROUND - 10, h: 480,
      dir: i === 0 ? 1 : -1,
      mood: 'calm',
      blink: (t % 3 < 0.12 ? 1 : 0),
      arms: { L: [10, 10], R: [10, 10] }
    });
  }
}

function drawCityStreet(lt, d, t, night = false) {
  // Sky
  ctx.fillStyle = night ? '#111827' : '#93C5FD';
  ctx.fillRect(-300, -300, W + 600, FLOOR + 300);

  // Distant City Skyline
  ctx.fillStyle = night ? '#1F2937' : '#CBD5E1';
  const bldgs = [[60, 420, 220], [290, 560, 190], [490, 380, 240], [740, 510, 200], [950, 440, 210]];
  for (const [bx, bh, bw] of bldgs) {
    ctx.fillRect(bx, FLOOR - bh, bw, bh);
    // Glowing windows
    ctx.fillStyle = night ? '#FDE047' : '#FFFFFF';
    for (let wy = FLOOR - bh + 40; wy < FLOOR - 40; wy += 55) {
      for (let wx = bx + 25; wx < bx + bw - 30; wx += 45) {
        if ((wx + wy) % 3 === 0) ctx.fillRect(wx, wy, 20, 30);
      }
    }
    ctx.fillStyle = night ? '#1F2937' : '#CBD5E1';
  }

  // Sidewalk & Asphalt Street
  ctx.fillStyle = night ? '#374151' : '#94A3B8';
  ctx.fillRect(-300, FLOOR, W + 600, 110);
  ctx.fillStyle = night ? '#1E293B' : '#475569';
  ctx.fillRect(-300, FLOOR + 110, W + 600, H - FLOOR - 110 + 300);

  // Street Curb & Road Dashes
  ctx.strokeStyle = '#FACC15';
  ctx.lineWidth = 14;
  ctx.setLineDash([80, 60]);
  ctx.beginPath(); ctx.moveTo(-300, FLOOR + 260); ctx.lineTo(W + 300, FLOOR + 260); ctx.stroke();
  ctx.setLineDash([]);

  // Streetlamp with warm light cone
  const lx = 200;
  line([[lx, FLOOR - 620], [lx, FLOOR]], P.ink, 16);
  ctx.beginPath(); ctx.arc(lx, FLOOR - 620, 28, 0, Math.PI * 2); ctx.fillStyle = '#F59E0B'; ctx.fill();
  const glow = ctx.createRadialGradient(lx, FLOOR - 580, 20, lx, FLOOR - 580, 380);
  glow.addColorStop(0, 'rgba(253, 224, 71, 0.35)');
  glow.addColorStop(1, 'rgba(253, 224, 71, 0)');
  ctx.fillStyle = glow;
  ctx.fillRect(lx - 380, FLOOR - 600, 760, 700);
}

function drawCourtroom(lt, d, t) {
  // High oak courtroom wall
  ctx.fillStyle = '#451A03';
  ctx.fillRect(-300, -300, W + 600, FLOOR + 300);

  // Wood Wall Framing Lines
  ctx.strokeStyle = '#78350F';
  ctx.lineWidth = 8;
  for (let x = 120; x < W; x += 220) {
    ctx.strokeRect(x, 150, 180, FLOOR - 220);
  }

  // Polished Floor
  ctx.fillStyle = '#78350F';
  ctx.fillRect(-300, FLOOR, W + 600, H - FLOOR + 300);

  // Elevated Judge's Bench
  ctx.fillStyle = '#291003';
  rr(240, FLOOR - 320, 600, 330, 16); ctx.fill();
  ctx.fillStyle = '#451A03';
  rr(220, FLOOR - 340, 640, 32, 10); ctx.fill();

  // Scales of Justice Emblem
  circle(540, FLOOR - 200, 52, '#D97706');
  circle(540, FLOOR - 200, 44, '#FDE68A');
  ctx.fillStyle = '#92400E';
  ctx.font = 'bold 36px Inter, sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText('⚖', 540, FLOOR - 200);

  // Wooden Balustrade / Railing in foreground
  ctx.fillStyle = '#552309';
  ctx.fillRect(-300, FLOOR + 90, W + 600, 24);
  for (let rx = -200; rx < W + 200; rx += 90) {
    ctx.fillRect(rx, FLOOR + 90, 16, 150);
  }
}

function drawAuctionDesk(lt, d, t, night = false) {
  // Indoor study room
  ctx.fillStyle = night ? '#1E293B' : '#E2E8F0';
  ctx.fillRect(-300, -300, W + 600, FLOOR + 300);

  // Wall window showing outdoor sky
  K.windowPane(660, 420, 320, 440, night);

  // Wooden Desk
  ctx.fillStyle = night ? '#334155' : '#854D0E';
  ctx.fillRect(180, FLOOR - 140, 720, 150);
  ctx.fillStyle = night ? '#1E293B' : '#713F12';
  ctx.fillRect(200, FLOOR + 10, 40, 260);
  ctx.fillRect(860, FLOOR + 10, 40, 260);

  // Glowing Laptop on desk
  const lx = 480, ly = FLOOR - 140;
  ctx.fillStyle = '#0F172A';
  ctx.fillRect(lx - 90, ly - 12, 180, 14); // base
  rr(lx - 85, ly - 140, 170, 130, 8); // screen
  ctx.fillStyle = '#0284C7';
  ctx.fillRect(lx - 78, ly - 132, 156, 114);

  // Screen auction UI glow
  ctx.fillStyle = '#FFFFFF';
  ctx.font = 'bold 16px monospace';
  ctx.fillText('BID: $5,000', lx - 60, ly - 90);
  ctx.fillStyle = '#22C55E';
  ctx.fillText('WINNER!', lx - 50, ly - 50);

  // Soft glow cast by laptop on the room
  const lapGlow = ctx.createRadialGradient(lx, ly - 70, 20, lx, ly - 70, 260);
  lapGlow.addColorStop(0, 'rgba(56, 189, 248, 0.28)');
  lapGlow.addColorStop(1, 'rgba(56, 189, 248, 0)');
  ctx.fillStyle = lapGlow;
  ctx.fillRect(lx - 260, ly - 330, 520, 400);
}

function drawDramaticStage(lt, d, t) {
  // Deep cinematic gradient
  const bg = ctx.createLinearGradient(0, 0, 0, H);
  bg.addColorStop(0, '#020617');
  bg.addColorStop(0.7, '#0F172A');
  bg.addColorStop(1, '#020617');
  ctx.fillStyle = bg;
  ctx.fillRect(-300, -300, W + 600, H + 600);

  // Overhead dramatic spotlight
  const spotX = 540 + Math.sin(t * 1.5) * 40;
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(spotX, -200);
  ctx.lineTo(spotX - 380, GROUND + 100);
  ctx.lineTo(spotX + 380, GROUND + 100);
  ctx.closePath();
  const spotGlow = ctx.createRadialGradient(spotX, 900, 80, spotX, 900, 600);
  spotGlow.addColorStop(0, 'rgba(255, 237, 213, 0.28)');
  spotGlow.addColorStop(1, 'rgba(255, 237, 213, 0)');
  ctx.fillStyle = spotGlow;
  ctx.fill();
  ctx.restore();

  // Floating ambient dust particles
  for (let i = 0; i < 18; i++) {
    const px = (Math.sin(i * 99 + t * 0.4) * 0.5 + 0.5) * W;
    const py = (Math.cos(i * 33 + t * 0.6) * 0.5 + 0.5) * H;
    circle(px, py, 2.5 + (i % 3), 'rgba(255, 255, 255, 0.45)');
  }
}

// ═════════════════════════ PROCEDURAL STORY PROPS ═════════════════════════

function drawNewspaper(x, y, headline, sc = 1, t = 0) {
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(sc, sc);
  ctx.rotate(Math.sin(t * 2) * 0.05);

  // Paper sheet
  rr(-240, -150, 480, 300, 12);
  ctx.fillStyle = '#F8FAFC';
  ctx.fill();
  ctx.strokeStyle = '#CBD5E1';
  ctx.lineWidth = 6;
  ctx.stroke();

  // Header banner: "THE DAILY CHRONICLE"
  ctx.fillStyle = '#0F172A';
  ctx.font = '900 28px Inter, serif';
  ctx.textAlign = 'center';
  ctx.fillText('THE DAILY CHRONICLE', 0, -105);
  line([[-210, -85], [210, -85]], '#0F172A', 4);

  // Big Bold Headline Text
  ctx.fillStyle = '#DC2626';
  ctx.font = '900 38px Inter, sans-serif';
  ctx.fillText(headline.slice(0, 20), 0, -35);

  // Dummy article paragraphs
  ctx.fillStyle = '#64748B';
  for (let r = 0; r < 4; r++) {
    const ly = 15 + r * 22;
    line([[-210, ly], [210, ly]], '#94A3B8', 8);
  }

  // Stamp: "OFFICIAL"
  ctx.save();
  ctx.translate(120, 60);
  ctx.rotate(-0.25);
  ctx.strokeStyle = '#DC2626';
  ctx.lineWidth = 6;
  rr(-80, -28, 160, 56, 8);
  ctx.stroke();
  ctx.fillStyle = '#DC2626';
  ctx.font = '900 24px Inter, sans-serif';
  ctx.fillText('BREAKING', 0, 8);
  ctx.restore();

  ctx.restore();
}

function drawBallotBox(x, y, sc = 1, t = 0) {
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(sc, sc);

  // Wooden Box
  rr(-120, -110, 240, 220, 16);
  ctx.fillStyle = '#1E293B';
  ctx.fill();
  ctx.strokeStyle = '#F59E0B';
  ctx.lineWidth = 6;
  ctx.stroke();

  // Front Seal
  circle(0, 10, 50, '#F59E0B');
  circle(0, 10, 42, '#1E293B');
  ctx.fillStyle = '#FFFFFF';
  ctx.font = '900 24px Inter, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('VOTE', 0, 18);

  // Paper dropping in
  const dropY = -110 + Math.sin(t * 3) * 20;
  rr(-50, dropY - 60, 100, 60, 6);
  ctx.fillStyle = '#F8FAFC';
  ctx.fill();
  ctx.strokeStyle = P.ink;
  ctx.lineWidth = 3;
  ctx.stroke();

  ctx.restore();
}

function drawCashStack(x, y, sc = 1, t = 0) {
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(sc, sc);

  for (let i = 0; i < 4; i++) {
    const ox = i * 6, oy = -i * 18;
    rr(-130 + ox, -40 + oy, 260, 90, 8);
    ctx.fillStyle = '#15803D';
    ctx.fill();
    ctx.strokeStyle = '#86EFAC';
    ctx.lineWidth = 4;
    ctx.stroke();
    // Currency badge
    circle(ox, 5 + oy, 28, '#86EFAC');
    ctx.fillStyle = '#15803D';
    ctx.font = '900 32px Inter, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('$', ox, 5 + oy);
  }

  ctx.restore();
}

function drawTownSign(x, y, name = 'BRIDGEVILLE', pop = '82', sc = 1) {
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(sc, sc);

  // Wooden Posts
  ctx.fillStyle = '#78350F';
  ctx.fillRect(-170, 0, 24, 180);
  ctx.fillRect(146, 0, 24, 180);

  // Green Road Signboard
  rr(-220, -120, 440, 150, 18);
  ctx.fillStyle = '#15803D';
  ctx.fill();
  ctx.strokeStyle = '#FFFFFF';
  ctx.lineWidth = 6;
  ctx.stroke();

  ctx.fillStyle = '#FFFFFF';
  ctx.font = '900 36px Inter, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(`WELCOME TO ${name.slice(0, 14)}`, 0, -60);

  ctx.font = 'bold 24px Inter, sans-serif';
  ctx.fillStyle = '#FDE047';
  ctx.fillText(`POPULATION: ${pop}`, 0, -10);

  ctx.restore();
}

// ═════════════════════════ SHOT BUILDER ═════════════════════════

export function buildShots(script) {
  const S = [];
  const CUES = [];
  const add = (o) => { S.push(o); return o; };
  const cue = (t, type, o = {}) => CUES.push({ t: +t.toFixed(3), type, ...o });

  const OP = (typeof window !== 'undefined' && window.OP) || {};
  const scriptContext = script || OP.script || OP.__OPTIONS__?.script || {};
  const title = scriptContext.title || 'Incredible True Story';
  const rawLines = (scriptContext.lines && scriptContext.lines.length) ? scriptContext.lines : (T.lines || []);

  const lines = rawLines.length ? rawLines : [
    { text: 'An incredible story that completely defied belief.' },
    { text: 'Nobody ever expected this mistake to happen.' }
  ];

  // Helper to extract clean punchy headline from line text
  const extractHeader = (ln, idx) => {
    if (ln.header) return ln.header.toUpperCase();
    const t = (ln.text || '').toUpperCase();
    if (idx === 0) return title.toUpperCase().slice(0, 28);
    if (t.includes('BID') || t.includes('AUCTION') || t.includes('$') || t.includes('DOLLAR')) {
      const m = t.match(/\$[\d,]+/) || t.match(/\b\d+\s*DOLLARS?\b/);
      return m ? m[0] : 'AUCTION BID';
    }
    if (t.includes('ERROR') || t.includes('MISTAKE') || t.includes('CATCH') || t.includes('DIGIT')) return 'CLERICAL ERROR';
    if (t.includes('OWNER') || t.includes('MAYOR') || t.includes('LANDLORD')) return 'ACCIDENTAL MAYOR';
    if (t.includes('ACRE') || t.includes('LAND') || t.includes('TOWN')) return '700 ACRES WON';
    if (t.includes('RENT') || t.includes('RESIDENT') || t.includes('PEOPLE')) return '82 RESIDENTS';
    if (t.includes('FIRE') || t.includes('BUILDING') || t.includes('HOUSE')) return 'THE OLD FIREHOUSE';
    if (t.includes('WOKE UP') || t.includes('MORNING') || t.includes('SLEEP')) return 'THE MORNING AFTER';
    const words = t.replace(/[^A-Z0-9 ]/g, '').split(/\s+/).filter((w) => w.length > 2);
    return words.slice(0, 3).join(' ') || `CHAPTER ${idx + 1}`;
  };

  lines.forEach((ln, idx) => {
    const isFirst = idx === 0;
    const isLast = idx === lines.length - 1;
    const startVal = ln.s ?? ln.start ?? L(idx);
    const lineStart = isFirst ? 0 : Math.max(0, startVal - 0.05);
    const nextLn = lines[idx + 1];
    const nextStartVal = nextLn ? (nextLn.s ?? nextLn.start ?? L(idx + 1)) : T.dur;
    const lineEnd = Math.max(lineStart + 0.1, nextStartVal - 0.05);

    const lineText = (ln.text || '').toUpperCase();
    const lineHeader = extractHeader(ln, idx);
    const comb = lineText + ' ' + lineHeader;

    // Semantic scene classification
    let sceneType = 'hall';
    if (comb.includes('AUCTION') || comb.includes('ONLINE') || comb.includes('BID') || comb.includes('SCROLL')) {
      sceneType = 'auction';
    } else if (comb.includes('STREET') || comb.includes('ROAD') || comb.includes('TOWN') || comb.includes('ACRE') || comb.includes('BRIDGEVILLE')) {
      sceneType = 'street';
    } else if (comb.includes('COURT') || comb.includes('LEGAL') || comb.includes('ERROR') || comb.includes('PAPERWORK')) {
      sceneType = 'court';
    } else if (comb.includes('SHOCK') || comb.includes('SUDDEN') || comb.includes('CRAZY') || comb.includes('DIGIT') || comb.includes('CATCH')) {
      sceneType = 'dramatic';
    } else {
      sceneType = idx % 2 === 0 ? 'hall' : 'street';
    }

    // Hero Character Acting Configuration
    let mood = 'calm';
    let heroDir = 1;
    let heroPose = {};

    if (comb.includes('SHOCK') || comb.includes('ERROR') || comb.includes('ACCIDENTAL') || comb.includes('WHAT') || comb.includes('WOKE UP')) {
      mood = 'scared';
      heroPose = { lean: -8, blink: 0, arms: { L: [-30, 40], R: [-30, 40] } };
    } else if (comb.includes('MAYOR') || comb.includes('WIN') || comb.includes('PROUD') || comb.includes('OWNER') || comb.includes('RENT')) {
      mood = 'happy';
      heroPose = { lean: 0, arms: { L: [60, 60], R: [60, 60] } };
    } else if (comb.includes('DECIDED') || comb.includes('PAPERWORK') || comb.includes('RULE') || comb.includes('BID')) {
      mood = 'determined';
      heroPose = { lean: 4, arms: { L: [-10, 15], R: [75, 10] } };
    } else {
      mood = 'calm';
      heroPose = { lean: 0, arms: { L: [-6, 14], R: [20, 20] } };
    }

    // Audio cues per shot
    cue(lineStart, 'whoosh', { gain: 0.45 });
    cue(lineStart + 0.12, 'pop', { gain: 0.5 });
    if (comb.includes('WIN') || comb.includes('MAYOR') || isLast) {
      cue(lineStart + 0.35, 'sparkle', { dur: 0.6 });
    } else if (comb.includes('ERROR') || comb.includes('CATCH')) {
      cue(lineStart + 0.3, 'thud', { gain: 0.6 });
    }

    add({
      id: `shot_${idx}`,
      at: lineStart,
      note: `${lineHeader}: ${lineText.slice(0, 30)}`,
      draw(lt, d, t) {
        // 1. Draw procedural environment
        if (sceneType === 'auction') {
          drawAuctionDesk(lt, d, t, false);
        } else if (sceneType === 'street') {
          drawCityStreet(lt, d, t, false);
        } else if (sceneType === 'court') {
          drawCourtroom(lt, d, t);
        } else if (sceneType === 'dramatic') {
          drawDramaticStage(lt, d, t);
        } else {
          drawTownHall(lt, d, t, false);
        }

        // 2. Animated Hero Character Performance
        const walkCycle = lt < 1.2 ? (t * 12) : null;
        const heroX = lerp(440, 520, Math.min(1, lt / 0.8));
        const blinkVal = (t % 3.2 < 0.14) ? 1 : 0;

        K.person({
          x: heroX,
          y: GROUND,
          h: 820,
          dir: heroDir,
          mood: mood,
          blink: blinkVal,
          walk: walkCycle,
          ...heroPose
        });

        // 3. Dynamic Narrative Focal Props
        const popScale = eob(seg(lt, 0.15, 0.45));
        if (comb.includes('AUCTION') || comb.includes('BID') || comb.includes('$')) {
          drawCashStack(820, 920, popScale * 0.9, t);
        } else if (comb.includes('MAYOR') || comb.includes('TOWN') || comb.includes('ACRE')) {
          drawTownSign(780, 840, 'BRIDGEVILLE', '82', popScale * 0.9);
        } else if (comb.includes('PAPERWORK') || comb.includes('ERROR') || comb.includes('CLERICAL')) {
          drawNewspaper(780, 840, lineHeader, popScale * 0.9, t);
        } else if (comb.includes('VOTE') || comb.includes('ELECTION')) {
          drawBallotBox(800, 920, popScale * 0.9, t);
        }

        // 4. Punchy Golden Chapter Plaque at Top (Smooth spring entrance)
        const plaqueScale = eob(seg(lt, 0.05, 0.35));
        K.stepCard(idx + 1, lineHeader.slice(0, 22), 540, 280, plaqueScale);

        // 5. Cinematic bars for dramatic twists or final hook
        if (comb.includes('ERROR') || comb.includes('CATCH') || isLast) {
          K.cinemaBars(eo(seg(lt, 0, 0.3)));
        }
      }
    });
  });

  return { shots: S, cues: CUES };
}
