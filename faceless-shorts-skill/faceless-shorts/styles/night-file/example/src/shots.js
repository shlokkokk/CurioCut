// Dynamic 3D True Crime & Mystery Director for Night File 3D
import * as THREE from 'three';
import { ctx, setCtx, W, H, clamp, lerp, seg, eo, eio, eob, rr } from './core/lib.js';
import { L, Wd, T } from './core/timing.js';
import { camera } from './core/engine.js';
import { Human } from './core/human.js';
import * as SETS from './core/sets3d.js';
import * as K from './core/kit.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const lerpV = (a, b, k) => a.clone().lerp(b, k);
const NIGHT = { exposure: 1.25, bloom: 0.85, bloomThreshold: 0.55, vignette: 0.6, grain: 0.05, warm: 0 };

/** paper insert (ticket / note / file) drawn in 2D */
function paper(x, y, w, h, rot, lines, sc = 1) {
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(rot);
  ctx.scale(sc, sc);
  ctx.shadowColor = 'rgba(0,0,0,0.7)';
  ctx.shadowBlur = 40;
  rr(-w / 2, -h / 2, w, h, 6);
  ctx.fillStyle = K.P.paper;
  ctx.fill();
  ctx.shadowBlur = 0;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'alphabetic';
  lines.forEach(([txt, size, col, dy]) => {
    ctx.font = `700 ${size}px FreeMono`;
    ctx.fillStyle = col || K.P.ink;
    ctx.fillText(txt, -w / 2 + 40, -h / 2 + dy);
  });
  ctx.restore();
}

export function buildShots(E, script) {
  const S = [], CUES = [], add = (o) => (S.push(o), o), cue = (t, type, o = {}) => CUES.push({ t: +t.toFixed(3), type, ...o });
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.1);
  const cam = camera(34);

  // ═════════════════════════ 3D INVESTIGATIVE SETS ═════════════════════════
  const CR = SETS.corridor();
  const HN = SETS.houseNight();
  const CW = SETS.caseWall([0, 1, 2].map((k) => {
    const c = document.createElement('canvas');
    c.width = 360;
    c.height = 420;
    const g = c.getContext('2d'), prev = ctx;
    setCtx(g);
    g.fillStyle = '#D8CFBA';
    g.fillRect(0, 0, 360, 420);
    g.save();
    g.translate(180, 210);
    g.scale(1.5, 1.5);
    K.polaroid(0, 0, 1, 0, ['glow', 'house', 'dark'][k]);
    g.restore();
    setCtx(prev);
    return c;
  }));

  const person = (kind) => {
    const h = new Human({ face: false });
    h.setAllMaterial(kind === 'subject' ? SETS.subjectMat() : SETS.witnessMat());
    return h;
  };

  const subject = person('subject');
  const witness = person('witness');
  CR.scene.add(subject.group, witness.group);

  const render = (scene, focusP, extra = {}) => {
    if (cam.fov !== (extra.fov || 34)) {
      cam.fov = extra.fov || 34;
      cam.updateProjectionMatrix();
    }
    E.render(scene, cam, { ...NIGHT, focus: cam.position.distanceTo(focusP), aperture: 0.0012, ...extra });
  };

  // ═════════════════════════ DYNAMIC SCRIPT PARSING ═════════════════════════
  const OP = (typeof window !== 'undefined' && window.OP) || {};
  const scriptContext = script || OP.script || {};
  const rawLines = (scriptContext.lines && scriptContext.lines.length) ? scriptContext.lines : (T.lines || []);
  const title = (scriptContext.title || 'UNSOLVED MYSTERY').toUpperCase();

  const lines = rawLines.length ? rawLines : [
    { text: 'A classified event occurred in the dead of night.' },
    { text: 'Investigators still have not found the full truth.' }
  ];

  const totalLines = lines.length;

  // Extract dates, numbers or locations from script text
  const extractDate = (txt, idx) => {
    const m = txt.match(/\b(18\d\d|19\d\d|20\d\d)\b/) ||
              txt.match(/\b(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+\d{1,2}\b/i) ||
              txt.match(/\b\d{1,2}:\d{2}\s*(?:AM|PM|A\.M\.|P\.M\.)\b/i);
    if (m) return m[0].toUpperCase();
    return idx === 0 ? 'CLASSIFIED FILE' : `TIMELINE ${idx + 1}`;
  };

  const extractAmountOrMetric = (txt) => {
    const m = txt.match(/\$[\d,]+(?:\s*(?:MILLION|BILLION|K))?/i) ||
              txt.match(/\b\d+\s*(?:THOUSAND|MILLION|BILLION|DOLLARS|BUCKS|YEARS|MONTHS|DAYS|MILES|VICTIMS)\b/i);
    return m ? m[0].toUpperCase() : null;
  };

  const extractHeader = (txt, idx) => {
    if (idx === 0) return title.slice(0, 24);
    if (idx === totalLines - 1) return 'STATUS: UNSOLVED';
    const words = txt.replace(/[^A-Z0-9 ]/g, '').split(/\s+/).filter((w) => w.length > 2);
    return words.slice(0, 3).join(' ') || `EXHIBIT ${idx + 1}`;
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
    const dateText = extractDate(lineText, idx);
    const metricText = extractAmountOrMetric(lineText);
    const header = extractHeader(lineText, idx);

    // Dynamic scene type routing based on story keywords and pacing
    let sceneType = 'corridor_subject';
    if (isFirst) {
      sceneType = 'opening_date';
    } else if (isLast) {
      sceneType = 'case_file_slam';
    } else if (lineText.includes('HOUSE') || lineText.includes('NIGHT') || lineText.includes('OUTSIDE') || lineText.includes('STREET') || lineText.includes('DARK')) {
      sceneType = 'house_night';
    } else if (lineText.includes('FILE') || lineText.includes('WALL') || lineText.includes('PHOTO') || lineText.includes('FOUND') || lineText.includes('EVIDENCE') || lineText.includes('PROOF')) {
      sceneType = 'case_wall';
    } else if (lineText.includes('TICKET') || lineText.includes('NOTE') || lineText.includes('DEMAND') || lineText.includes('$') || lineText.includes('CASH') || lineText.includes('PAPER')) {
      sceneType = 'paper_evidence';
    } else if (lineText.includes('TAPE') || lineText.includes('CLOCK') || lineText.includes('TIME') || lineText.includes('HOUR') || lineText.includes('RECORD')) {
      sceneType = 'classified_tape';
    } else {
      const cycle = idx % 4;
      const sets = ['corridor_subject', 'house_night', 'case_wall', 'corridor_witness'];
      sceneType = sets[cycle];
    }

    // Sound cues
    cue(lineStart, 'whoosh', { gain: 0.5 });
    if (isFirst || dateText.match(/\d/)) cue(lineStart + 0.2, 'tock', { gain: 0.4 });
    if (isLast) {
      cue(lineStart + 0.35, 'thud', { gain: 0.5 });
      cue(lineStart + 0.7, 'slam', { gain: 0.7 });
    } else if (sceneType === 'paper_evidence') {
      cue(lineStart + 0.25, 'slide', { dur: 0.5, gain: 0.4 });
    }

    add({
      id: `shot_${idx}`,
      at: lineStart,
      note: `${header}: ${lineText.slice(0, 30)}`,
      draw(lt, d, t, blit) {
        const k = eio(clamp(lt / d));

        // ═════════════ 3D SCENE RENDERING ═════════════
        if (sceneType === 'opening_date') {
          // Corridor Establishing Shot: Slow push-in down dark corridor with overhead lamp
          subject.group.visible = false;
          witness.group.visible = false;
          CR.update(t);

          cam.position.copy(lerpV(V3(0.3, 1.55, 1.8), V3(0.15, 1.5, 0.6), k));
          cam.lookAt(0, 1.1, -10);
          render(CR.scene, V3(0, 1, -5));
          blit();

          // Typewriter date stamp
          K.dateStamp(dateText, title.slice(0, 20), clamp(lt / 1.5), 80, 320);

        } else if (sceneType === 'corridor_subject') {
          // Glowing red subject walking down the corridor under spotlight
          witness.group.visible = false;
          subject.group.visible = true;
          subject.group.rotation.y = 0;
          subject.group.position.set(0, 0, lerp(-7, -3.2, lt / d));
          subject.walk(lt * 5.2, 0.8);
          CR.update(t);

          cam.position.copy(lerpV(V3(0.25, 1.5, 0.4), V3(0.2, 1.45, -0.2), k));
          cam.lookAt(0, 1.2, -6);
          render(CR.scene, subject.group.position.clone().add(V3(0, 1.2, 0)));
          blit();

          if (metricText) {
            K.dateStamp(metricText, header, clamp(lt / 1.2), 80, 320);
          }

        } else if (sceneType === 'corridor_witness') {
          // Witness with red rim lighting standing near doorway
          subject.group.visible = false;
          witness.group.visible = true;
          witness.group.position.set(-0.8, 0, -5.5);
          witness.group.rotation.y = Math.PI * 0.4;
          CR.update(t);

          cam.position.copy(lerpV(V3(0.4, 1.55, -2.5), V3(0.2, 1.5, -3.8), k));
          cam.lookAt(-0.8, 1.2, -5.5);
          render(CR.scene, V3(-0.8, 1.2, -5.5));
          blit();

          // Redacted confidential bar
          K.redacted(140, 480, [420, 580, 320], clamp(lt / 0.8));

        } else if (sceneType === 'house_night') {
          // 3D House at Night: Streetlight cone, lit window, moonlit sky
          cam.position.copy(lerpV(V3(2.5, 2.2, 6.0), V3(1.8, 1.8, 4.2), k));
          cam.lookAt(1.3, 1.7, -3.98);
          render(HN.scene, V3(1.3, 1.7, -3.98));
          blit();

          K.dateStamp(dateText, header, clamp(lt / 1.4), 80, 320);

        } else if (sceneType === 'case_wall') {
          // 3D Cork Case Wall: Pinned polaroids with red connection strings
          cam.position.copy(lerpV(V3(0.4, 0.3, 9.5), V3(0.2, 0.2, 7.2), k));
          cam.lookAt(0, 0.2, 0);
          render(CW.scene, V3(0, 0.2, 0), { bloom: 0.4 });
          blit();

          K.dateStamp(dateText, metricText || 'KEY EVIDENCE', clamp(lt / 1.4), 80, 320);
          K.redCircle(540, 1000, 280, 200, seg(lt, 0.3, 0.9));

        } else if (sceneType === 'paper_evidence') {
          // 2D Paper Evidence insert over blurred 3D crime scene
          cam.position.set(0.1, 1.4, -6.5);
          cam.lookAt(0.5, 0.9, -10);
          render(CR.scene, V3(0, 1, -2), { aperture: 0.01, maxblur: 0.014 });
          blit();

          const popK = eo(clamp(lt / 0.45));
          const linesDraw = [
            ['CONFIDENTIAL EVIDENCE', 34, K.P.redDeep, 70],
            [header.slice(0, 24), 40, null, 140],
            ['EXHIBIT:', 34, '#6A6458', 230],
            [metricText || lineText.slice(0, 18), 64, null, 320],
            ['VERIFIED PRIMARY RECORD', 34, '#6A6458', 400]
          ];
          paper(540, lerp(1100, 860, popK), 820, 460, -0.04, linesDraw, popK);
          if (lt > 0.4) {
            K.redCircle(540, 860 + 60, 240, 80, seg(lt, 0.4, 0.9));
          }

        } else if (sceneType === 'classified_tape') {
          // Audio tape evidence / Clock ticking
          cam.position.set(0, 1.5, -2);
          cam.lookAt(0, 1.1, -12);
          render(CR.scene, V3(0, 1, 0), { aperture: 0.012, maxblur: 0.016, exposure: 0.9 });
          blit();

          K.cassette(540, 860, 1.35, t * 5);
          K.dateStamp(dateText, header, clamp(lt / 1.2), 80, 320);

        } else {
          // Case file slams down with UNSOLVED stamp
          cam.position.set(0.1, 0.1, 6.5);
          cam.lookAt(0, 0.1, 0);
          render(CW.scene, V3(0, 0.1, 0), { bloom: 0.4, aperture: 0.01, maxblur: 0.014, exposure: 0.9 });
          blit();

          const stampProgress = seg(lt, 0.35, 0.7);
          K.caseFile(540, lerp(1500, 860, eob(seg(lt, 0, 0.45))), 1.3, 'CASE NO. 94-CL', stampProgress, -0.04);
          K.dateStamp('FINAL RECORD', 'UNSOLVED', clamp(lt / 1.2), 80, 320);
        }

        // Apply film look & grain
        K.filmLook(t, 0.75);
      }
    });
  });

  return { shots: S, cues: CUES };
}
