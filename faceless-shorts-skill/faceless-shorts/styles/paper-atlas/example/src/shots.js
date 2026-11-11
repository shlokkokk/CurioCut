// Dynamic Cut-Paper History Director for Paper Atlas (9:16)
import { ctx, W, H, TAU, clamp, lerp, seg, eo, eio, eob, rnd, rr, circle, ell, line } from './core/lib.js';
import { L, Wd, T } from './core/timing.js';
import * as K from './core/kit.js';
const { P, cut, P_rr, P_poly, P_circ } = K;

// ═════════════════════════ CUT-PAPER SET PIECES ═════════════════════════
const NIGHT = '#2F3550';

function nightPage(seed) {
  K.parchment(seed);
  ctx.save();
  ctx.globalAlpha = 0.86;
  ctx.fillStyle = NIGHT;
  ctx.fillRect(-300, -300, W + 600, H + 600);
  ctx.restore();
  for (let i = 0; i < 30; i++) {
    circle(rnd(i + seed) * W, rnd(i + 40 + seed) * 900, 3 + rnd(i) * 3, '#E9DCBC');
  }
}

/** A timber house with paper edge and drop shadow */
function house(x, y, w, h, wall = '#B68A5C', roof = '#7A4B33', win = 0) {
  cut(P_rr(x - w / 2, y - h, w, h, 4), wall, { shadow: 0.7, edge: 5 });
  cut(P_poly([[x - w / 2 - 18, y - h + 4], [x, y - h - w * 0.55], [x + w / 2 + 18, y - h + 4]]), roof, { shadow: 0.6, edge: 5 });
  ctx.strokeStyle = 'rgba(62,44,30,0.55)';
  ctx.lineWidth = 6;
  ctx.beginPath();
  ctx.moveTo(x - w / 2, y - h * 0.5);
  ctx.lineTo(x + w / 2, y - h * 0.5);
  ctx.moveTo(x, y - h);
  ctx.lineTo(x, y);
  ctx.stroke();
  for (const dx of [-0.25, 0.25]) {
    rr(x + dx * w - 22, y - h * 0.82, 44, 54, 4);
    ctx.fillStyle = win ? `rgba(242,190,90,${0.4 + 0.6 * win})` : '#3E2C1E';
    ctx.fill();
  }
}

/** Paper flame: layered crimson / orange / gold, flickering */
function flame(x, y, s, t, seed = 0) {
  if (s <= 0) return;
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(s, s * (1 + 0.08 * Math.sin(t * 9 + seed)));
  const f = (w, h, c) => cut(() => {
    ctx.beginPath();
    ctx.moveTo(-w, 0);
    ctx.quadraticCurveTo(-w * 1.1, -h * 0.5, -w * 0.2 + Math.sin(t * 6 + seed) * 8, -h);
    ctx.quadraticCurveTo(w * 0.2, -h * 0.55, w * 0.5, -h * 0.75 + Math.sin(t * 7 + seed) * 6);
    ctx.quadraticCurveTo(w * 1.1, -h * 0.4, w, 0);
    ctx.closePath();
  }, c, { shadow: 0.4, edge: 3 });
  f(70, 190, P.crimson);
  f(50, 140, '#E0782E');
  f(28, 90, '#F2C14E');
  ctx.restore();
}

/** Cut-paper smoke cloud */
function smoke(x, y, s, a = 1) {
  ctx.save();
  ctx.globalAlpha = a;
  ctx.translate(x, y);
  ctx.scale(s, s);
  cut(() => {
    ctx.beginPath();
    for (const [dx, dy, r] of [[-60, 0, 60], [0, -30, 75], [60, 0, 58], [0, 25, 60]]) {
      ctx.moveTo(dx + r, dy);
      ctx.arc(dx, dy, r, 0, TAU);
    }
  }, '#8F8578', { shadow: 0.4, edge: 4 });
  ctx.restore();
}

/** Cut-paper wind currents */
function wind(t, y, a = 1) {
  ctx.save();
  ctx.globalAlpha = a;
  ctx.strokeStyle = P.edge;
  ctx.lineWidth = 9;
  ctx.lineCap = 'round';
  for (let i = 0; i < 4; i++) {
    const x = ((t * 420 + i * 300) % 1500) - 300, yy = y + i * 70;
    ctx.beginPath();
    ctx.moveTo(x, yy);
    ctx.bezierCurveTo(x + 120, yy - 30, x + 200, yy + 30, x + 300, yy);
    ctx.arc(x + 300, yy - 26, 26, Math.PI / 2, -Math.PI * 0.9, true);
    ctx.stroke();
  }
  ctx.restore();
}

/** Historical stone monument / cathedral */
function monument(x, y, s) {
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(s, s);
  cut(P_rr(-200, -260, 400, 260, 4), P.stone);
  cut(P_rr(-90, -380, 180, 130, 4), P.stone);
  cut(() => {
    ctx.beginPath();
    ctx.arc(0, -380, 110, Math.PI, TAU);
    ctx.closePath();
  }, P.stoneDark);
  cut(P_rr(-12, -560, 24, 90, 4), P.stoneDark);
  for (let i = 0; i < 4; i++) {
    rr(-150 + i * 90, -200, 40, 120, 18);
    ctx.fillStyle = P.ink;
    ctx.fill();
  }
  ctx.restore();
}

/** Cut-paper sailing galleon on water */
function ship(x, y, s, rot = 0) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(rot);
  ctx.scale(s, s);
  cut(() => {
    ctx.beginPath();
    ctx.moveTo(-160, 0);
    ctx.lineTo(-120, 80);
    ctx.lineTo(130, 80);
    ctx.lineTo(180, 0);
    ctx.closePath();
  }, '#7A4B33', { shadow: 0.6, edge: 4 });
  // Sails
  cut(P_poly([[-90, -10], [-80, -180], [0, -10]]), '#EAE3D2', { shadow: 0.4, edge: 3 });
  cut(P_poly([[10, -10], [20, -160], [90, -10]]), '#EAE3D2', { shadow: 0.4, edge: 3 });
  ctx.restore();
}

export function buildShots(script) {
  const S = [], CUES = [], add = (o) => (S.push(o), o), cue = (t, type, o = {}) => CUES.push({ t: +t.toFixed(3), type, ...o });
  const cut_ = (i) => (i === 0 ? 0 : L(i) - 0.08);

  // ═════════════════════════ DYNAMIC SCRIPT PARSING ═════════════════════════
  const OP = (typeof window !== 'undefined' && window.OP) || {};
  const scriptContext = script || OP.script || {};
  const rawLines = (scriptContext.lines && scriptContext.lines.length) ? scriptContext.lines : (T.lines || []);
  const title = (scriptContext.title || 'EPIC HISTORY').toUpperCase();

  const lines = rawLines.length ? rawLines : [
    { text: 'An ancient event completely altered the course of history.' },
    { text: 'Centuries later, the consequences are still felt today.' }
  ];

  const totalLines = lines.length;

  // Extract year / date / century
  const extractYearOrDate = (txt, idx) => {
    let m = txt.match(/\b(1\d\d\d|20\d\d)\b/) ||
            txt.match(/\b\d+(?:TH|ST|RD|ND)?\s+CENTURY\b/i) ||
            txt.match(/\b\d+\s+B\.?C\.?\b/i) ||
            txt.match(/\b(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+\d{1,2}\b/i);
    if (!m && idx === 0) {
      m = title.match(/\b(1\d\d\d|20\d\d)\b/) || title.match(/\b\d+(?:TH|ST|RD|ND)?\s+CENTURY\b/i);
    }
    if (m) return m[0].toUpperCase();
    return idx === 0 ? 'HISTORIC ERA' : `CHAPTER ${idx + 1}`;
  };

  const extractMetric = (txt) => {
    if (txt.includes('GOLD') || txt.includes('TREASURE')) return 'ROYAL TREASURE';
    if (txt.includes('FLEET') || txt.includes('ARMADA')) return 'THE ARMADA';
    if (txt.includes('FIRE') || txt.includes('FLAME')) return 'GREAT FIRE';
    const m = txt.match(/[\d,]+\s*(?:HOUSES|CHURCHES|SOLDIERS|SHIPS|DAYS|YEARS|PEOPLE|MILES|MEN|KILLED|LOST)\b/i) ||
              txt.match(/\$[\d,]+(?:\s*(?:MILLION|BILLION))?/i);
    return m ? m[0].toUpperCase() : null;
  };

  const extractHeadline = (txt, idx) => {
    if (idx === 0) return title.slice(0, 38);
    if (idx === totalLines - 1) return 'HISTORICAL RECORD';
    const words = txt.replace(/[^A-Z0-9 ]/g, '').split(/\s+/).filter((w) => w.length > 2);
    return words.slice(0, 3).join(' ') || `EPOCH ${idx + 1}`;
  };

  lines.forEach((ln, idx) => {
    const isFirst = idx === 0;
    const isLast = idx === totalLines - 1;
    const startVal = ln.s ?? ln.start ?? L(idx);
    const lineStart = isFirst ? 0 : Math.max(0, startVal - 0.08);
    const nextLn = lines[idx + 1];
    const nextStartVal = nextLn ? (nextLn.s ?? nextLn.start ?? L(idx + 1)) : T.dur;
    const lineEnd = Math.max(lineStart + 0.1, nextStartVal - 0.08);

    const lineText = (ln.text || '').toUpperCase();
    const yearText = extractYearOrDate(lineText, idx);
    const metricText = extractMetric(lineText);
    const headline = extractHeadline(lineText, idx);

    // Scene Environment Selector
    let sceneType = 'map_route';
    if (isFirst) {
      sceneType = 'opening_ribbon';
    } else if (isLast) {
      sceneType = 'seal_verdict';
    } else if (lineText.includes('FIRE') || lineText.includes('BURN') || lineText.includes('FLAME') || lineText.includes('STORM') || lineText.includes('WIND') || lineText.includes('WAR')) {
      sceneType = 'crisis_flame';
    } else if (lineText.includes('CITY') || lineText.includes('STREET') || lineText.includes('HOUSE') || lineText.includes('TOWN') || lineText.includes('LONDON') || lineText.includes('PEOPLE')) {
      sceneType = 'kingdom_street';
    } else if (lineText.includes('CHURCH') || lineText.includes('CASTLE') || lineText.includes('KING') || lineText.includes('MAYOR') || lineText.includes('PALACE') || lineText.includes('TEMPLE')) {
      sceneType = 'monument_palace';
    } else if (lineText.includes('SEA') || lineText.includes('SHIP') || lineText.includes('OCEAN') || lineText.includes('MAP') || lineText.includes('ISLAND')) {
      sceneType = 'map_route';
    } else {
      const cycle = idx % 4;
      const sets = ['map_route', 'kingdom_street', 'crisis_flame', 'monument_palace'];
      sceneType = sets[cycle];
    }

    // Sound cues
    cue(lineStart, 'whoosh', { gain: 0.5 });
    cue(lineStart + 0.15, 'pop', { gain: 0.6 });
    if (isLast) {
      cue(lineStart + 0.4, 'slam', { gain: 0.7 });
    }

    add({
      id: `shot_${idx}`,
      at: lineStart,
      cam: [540, 920],
      zoom: 0.08,
      note: `${headline}: ${lineText.slice(0, 30)}`,
      draw(lt, d, t) {
        const k = eio(clamp(lt / d));

        if (sceneType === 'opening_ribbon') {
          // Opening Map & Golden Date Ribbon
          K.map({ seed: 2, route: k });
          K.ribbon(yearText, 540, 380, eob(seg(lt, 0.1, 0.5)));
          K.slip(title.length > 38 ? title.slice(0, 35) + '...' : title, 540, 520, eob(seg(lt, 0.3, 0.7)), 0.02, 34);

        } else if (sceneType === 'map_route') {
          // Ocean and territory map with animated dashed routes and ship
          K.map({ seed: idx + 4, route: clamp(lt / (d * 0.8)) });
          ship(lerp(280, 720, k), 1260, 0.9, Math.sin(t * 3) * 0.04);
          K.slip(headline, 540, 320, eob(seg(lt, 0.1, 0.45)), -0.02, 32);
          if (metricText) {
            K.slip(metricText, 540, 440, eob(seg(lt, 0.35, 0.7)), 0.03, 30);
          }

        } else if (sceneType === 'kingdom_street') {
          // Street of timber houses on parchment with paper figures
          nightPage(idx + 1);
          const ROW = [[120, 0], [340, 1], [540, 0], [740, 1], [940, 0]];
          ROW.forEach(([x, variant], i) => {
            house(x, 1420, 200, 320 + variant * 70, variant ? '#8C6B4E' : '#A37A55', variant ? '#5E3B28' : '#6E4430', i === 2 ? 0.6 : 0);
          });
          cut(P_rr(-300, 1420, W + 600, 800, 0), '#4A3A2E', { shadow: 0, edge: 0 });

          // Paper figures walking along the street
          K.figure({ x: lerp(220, 380, k), y: 1420, h: 480, role: 'scholar', dir: 1, walk: t * 4 });
          K.figure({ x: 740, y: 1420, h: 500, role: 'guard', dir: -1 });

          K.slip(headline, 540, 300, eob(seg(lt, 0.1, 0.4)), 0.02, 34);
          if (yearText.match(/\d/)) {
            K.ribbon(yearText, 540, 440, eob(seg(lt, 0.25, 0.6)));
          }

        } else if (sceneType === 'crisis_flame') {
          // Dramatic crisis event: timber buildings engulfed in layered paper flames & smoke
          nightPage(idx + 2);
          house(540, 1480, 700, 700, '#8C6B4E', '#5E3B28', 1);
          flame(380, 1380, 1.4, t, 1);
          flame(680, 1340, 1.6, t, 2);
          smoke(540, 780, 1.8, 0.85);
          wind(t, 600, 0.9);

          K.slip('CRISIS EVENT', 540, 260, eob(seg(lt, 0.1, 0.35)), -0.03, 30);
          if (metricText) {
            K.slip(metricText, 540, 400, eob(seg(lt, 0.3, 0.65)), 0.04, 38);
          }

        } else if (sceneType === 'monument_palace') {
          // Grand stone monument / palace hall with monarch & royal seals
          K.parchment(idx + 5);
          monument(540, 1350, 1.15);
          K.figure({ x: 380, y: 1350, h: 520, role: 'king', dir: 1 });
          K.figure({ x: 700, y: 1350, h: 500, role: 'merchant', dir: -1 });

          K.slip(headline, 540, 280, eob(seg(lt, 0.1, 0.4)), 0.02, 34);
          if (metricText) {
            K.slip(metricText, 540, 420, eob(seg(lt, 0.3, 0.6)), -0.02, 32);
          }

        } else {
          // Climax: Royal wax seal stamps historical outcome on aged parchment
          K.parchment(1);
          const ROW = [[160, 1], [400, 0], [680, 1], [920, 0]];
          ROW.forEach(([x, variant]) => {
            house(x, 1480, 220, 360, '#9C8C70', '#7A2E3A', 0.2);
          });
          cut(P_rr(-300, 1480, W + 600, 800, 0), '#3E2C1E', { shadow: 0, edge: 0 });

          // Royal wax seal stamp
          const sealScale = eob(seg(lt, 0.2, 0.55));
          K.seal(540, 720, sealScale * 1.5, 'C');

          K.slip('HISTORICAL VERDICT', 540, 360, eob(seg(lt, 0.05, 0.35)), 0.03, 36);
          K.slip(title.length > 38 ? title.slice(0, 35) + '...' : title, 540, 1080, eob(seg(lt, 0.35, 0.7)), -0.02, 30);
        }
      }
    });
  });

  return { shots: S, cues: CUES };
}
