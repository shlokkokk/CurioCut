// Dynamic 3D Science & Anatomy Director for Deep Dive (9:16)
import * as THREE from 'three';
import { ctx, W, H, clamp, lerp, seg, eo, eio, eob } from './core/lib.js';
import { L, Wd, T } from './core/timing.js';
import { camera } from './core/engine.js';
import { Human } from './core/human.js';
import * as SETS from './core/sets.js';
import { label, pill, warning, blackout } from './core/look2d.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const lerpV = (a, b, k) => a.clone().lerp(b, k);

function screen(p, cam) {
  const v = p.clone().project(cam);
  return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H];
}

export function buildShots(E, script) {
  const S = [], CUES = [], add = (o) => (S.push(o), o), cue = (t, type, o = {}) => CUES.push({ t: +t.toFixed(3), type, ...o });
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.08);
  const cam = camera(30);

  const KLOOK = { aperture: 0.003, maxblur: 0.01, bloom: 0.2 };
  const XLOOK = { aperture: 0.0015, bloom: 0.55, bloomThreshold: 0.4, vignette: 0.45 };
  const VLOOK = { aperture: 0.005, maxblur: 0.012, bloom: 0.6, bloomThreshold: 0.5, focus: 3.2 };

  // ═════════════════════════ 3D WORLDS ═════════════════════════
  // 1. Real-world warm sunlit room
  const K = SETS.kitchen(E);
  const hero = new Human({});
  hero.group.position.set(0.1, 0, -0.6);
  K.scene.add(hero.group);

  // 2. Cyan glass X-Ray stage with glowing internal organs
  const X = SETS.xrayStage(E);
  const xh = new Human({});
  const xmat = SETS.xrayMaterial();
  xh.setBodyMaterial(xmat);
  const I = SETS.insides();
  xh.spine.add(I.group);
  X.scene.add(xh.group);

  // 3. Microscopic blood vessel
  const VS = SETS.vessel(E);

  const CYAN = new THREE.Color('#4FD1E8');
  const RED = new THREE.Color('#FF3B3B');
  const FACE = V3(0.1, 1.68, -0.6);

  const chest = (h, k) => h.parts[0].scale.set(1 + 0.03 * k, 1 + 0.012 * k, 1 + 0.08 * k);
  const lungs = (k) => I.lungs.forEach((l) => l.scale.set(1 + 0.12 * k, 1 + 0.1 * k, 1 + 0.12 * k));
  const reset = () => {
    hero.pose({});
    chest(hero, 0);
    xh.pose({});
    chest(xh, 0);
    lungs(0);
    I.heart.scale.setScalar(1);
    xmat.uniforms.uCol.value.copy(CYAN);
  };
  const kitchenRender = (focus, extra = {}) => E.render(K.scene, cam, { ...KLOOK, focus, ...extra });

  // ═════════════════════════ DYNAMIC SCRIPT PARSING ═════════════════════════
  const OP = (typeof window !== 'undefined' && window.OP) || {};
  const scriptContext = script || OP.script || {};
  const rawLines = (scriptContext.lines && scriptContext.lines.length) ? scriptContext.lines : (T.lines || []);
  const title = (scriptContext.title || 'WHAT HAPPENS IF?').toUpperCase();

  const lines = rawLines.length ? rawLines : [
    { text: 'What happens to your body during an extreme scientific event?' },
    { text: 'The biological reaction inside you is almost unbelievable.' }
  ];

  const totalLines = lines.length;

  // Extract medical/scientific terms or metrics
  const extractMedicalPill = (txt, idx) => {
    if (txt.includes('OXYGEN')) return 'OXYGEN ✓';
    if (txt.includes('CARBON') || txt.includes('CO2') || txt.includes('DIOXIDE')) return 'CO₂ ↑';
    if (txt.includes('HEART') || txt.includes('PULSE') || txt.includes('BPM')) return 'HEART RATE';
    if (txt.includes('BRAIN') || txt.includes('SYNAPSE')) return 'BRAIN ACTIVITY';
    if (txt.includes('STOMACH') || txt.includes('ACID')) return 'STOMACH ACID';
    if (txt.includes('BLOOD') || txt.includes('CELL')) return 'BLOODSTREAM';
    const m = txt.match(/[\d,.]+\s*(?:SECONDS?|MINUTES?|HOURS?|PERCENT|%|BPM|LITERS?)\b/i);
    if (m) return m[0].toUpperCase();
    return idx === 0 ? (title.length > 40 ? title.slice(0, 37) + '...' : title) : null;
  };

  const extractHeadline = (txt, idx) => {
    if (idx === 0) return title.slice(0, 24);
    if (idx === totalLines - 1) return 'FINAL VERDICT';
    const words = txt.replace(/[^A-Z0-9 ]/g, '').split(/\s+/).filter((w) => w.length > 2);
    return words.slice(0, 3).join(' ') || `STAGE ${idx + 1}`;
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
    const pillText = extractMedicalPill(lineText, idx);
    const headline = extractHeadline(lineText, idx);

    // Scene Environment Selector
    let sceneType = 'real_orbit';
    if (isFirst) {
      sceneType = 'real_closeup';
    } else if (isLast) {
      sceneType = 'real_warning';
    } else if (lineText.includes('BLOOD') || lineText.includes('VESSEL') || lineText.includes('CELL') || lineText.includes('DIOXIDE') || lineText.includes('CARBON')) {
      sceneType = 'vessel_macro';
    } else if (lineText.includes('LUNG') || lineText.includes('HEART') || lineText.includes('STOMACH') || lineText.includes('INSIDE') || lineText.includes('ORGAN') || lineText.includes('CHEST') || lineText.includes('BRAIN')) {
      sceneType = 'xray_organ';
    } else if (lineText.includes('DANGER') || lineText.includes('ALARM') || lineText.includes('STOP') || lineText.includes('SPASM') || lineText.includes('TWITCH')) {
      sceneType = 'xray_alarm';
    } else {
      const cycle = idx % 4;
      const sets = ['real_orbit', 'xray_organ', 'vessel_macro', 'xray_alarm'];
      sceneType = sets[cycle];
    }

    // Sound cues
    cue(lineStart, 'whoosh', { gain: 0.5 });
    cue(lineStart + 0.15, 'pop', { gain: 0.5 });
    if (sceneType === 'vessel_macro') {
      cue(lineStart + 0.2, 'bubbles', { dur: Math.min(2.0, lineEnd - lineStart) });
    }

    add({
      id: `shot_${idx}`,
      at: lineStart,
      note: `${headline}: ${lineText.slice(0, 30)}`,
      draw(lt, d, t, blit) {
        const k = eio(clamp(lt / d));

        // ═════════════ 3D SCENE RENDERING ═════════════
        if (sceneType === 'real_closeup') {
          // Face close-up in warm sunlit room, subtle reaction
          reset();
          const p = eo(seg(lt, 0.1, 1.2));
          hero.pose({ head: [-6 * p, 4, 0], spine: [-2 * p, 0, 0], lid: lerp(0, -0.3, p), look: [0, -3 * p] });
          chest(hero, p);

          cam.position.copy(lerpV(V3(0.42, 1.72, 0.45), V3(0.3, 1.7, 0.15), k));
          cam.lookAt(FACE);
          kitchenRender(cam.position.distanceTo(FACE));
          blit();

          if (pillText) {
            // Place clean header pill at top (y=260) instead of mouth (y=1180)
            const sz = Math.max(28, Math.min(50, Math.floor(750 / (pillText.length * 0.58))));
            pill(pillText, 540, 260, eob(seg(lt, 0.15, 0.4)), '#FFD43B', 'rgba(12,14,20,0.88)', sz);
          }

        } else if (sceneType === 'real_orbit') {
          // Medium shot orbit around human hero in sunlit room
          reset();
          hero.pose({ head: [2, -6 + Math.sin(lt * 2) * 3, 0], lid: -0.15, look: [6, 0] });
          chest(hero, 1);
          hero.group.position.y = Math.sin(lt * 3) * 0.003;

          const a = lerp(0.55, 0.2, k);
          cam.position.set(0.1 + Math.sin(a) * 2.1, 1.45, -0.6 + Math.cos(a) * 2.1);
          cam.lookAt(0.1, 1.25, -0.6);
          kitchenRender(2.1);
          blit();

          if (pillText) {
            // Upper screen zone (y=340) well above torso
            pill(pillText, 540, 340, eob(seg(lt, 0.1, 0.35)), '#FFD43B', 'rgba(12,14,20,0.85)', 60);
          }

        } else if (sceneType === 'xray_organ') {
          // Cyan glass X-Ray human body with glowing internal organs & screen label
          reset();
          lungs(1 + Math.sin(lt * 3) * 0.05);
          chest(xh, 1);
          xh.pose({ head: [4, -6, 0] });

          cam.position.copy(lerpV(V3(0.55, 1.5, 1.6), V3(0.3, 1.42, 1.1), k));
          cam.lookAt(0, 1.33, 0);
          E.render(X.scene, cam, { ...XLOOK, focus: cam.position.distanceTo(V3(0, 1.33, 0)) });
          blit();

          const [lx, ly] = screen(V3(0.1, 1.42, 0.05), cam);
          label(pillText || 'INTERNAL ORGANS', 760, 520, lx, ly, eob(seg(lt, 0.15, 0.45)));

        } else if (sceneType === 'vessel_macro') {
          // Microscopic blood vessel journey: red blood cells & chemical particles
          VS.update(t, -lt * 1.5, 0.2 + 0.8 * k, 0.35 * k);
          cam.position.set(Math.sin(lt) * 0.08, 0, -lt * 1.5);
          cam.lookAt(0.12, -0.06, -lt * 1.5 - 5);
          E.render(VS.scene, cam, VLOOK);
          blit();

          if (pillText) {
            pill(pillText, 540, 340, eob(seg(lt, 0.12, 0.38)) * (1 + 0.05 * Math.sin(lt * 8)), '#7CF29A');
          }

        } else if (sceneType === 'xray_alarm') {
          // X-Ray Body Alarm: Glass body pulses vivid danger red
          reset();
          const alarmPulse = Math.abs(Math.sin(lt * 6));
          xmat.uniforms.uCol.value.copy(lerpV(CYAN, RED, alarmPulse));
          I.heart.scale.setScalar(1 + 0.15 * Math.sin(lt * 10));
          chest(xh, 1);

          cam.position.copy(lerpV(V3(0.65, 1.45, 1.7), V3(0.35, 1.38, 1.2), k));
          cam.lookAt(0, 1.3, 0);
          E.render(X.scene, cam, { ...XLOOK, focus: cam.position.distanceTo(V3(0, 1.3, 0)) });
          blit();

          const [lx, ly] = screen(V3(0.0, 1.32, 0.05), cam);
          label('CRITICAL ALARM', 760, 520, lx, ly, eob(seg(lt, 0.15, 0.45)));

        } else {
          // Final Takeaway & Warning in Real World Room
          reset();
          hero.pose({ head: [0, 0, 0], lid: 0 });
          cam.position.copy(lerpV(V3(0.1, 1.62, 0.9), V3(0.1, 1.62, 0.65), k));
          cam.lookAt(FACE);
          kitchenRender(cam.position.distanceTo(FACE));
          blit();

          // Big bold warning triangle
          warning(540, 360, eob(seg(lt, 0.2, 0.65)) * 1.25);
          if (pillText) {
            pill(pillText, 540, 1260, eob(seg(lt, 0.35, 0.65)), '#FF4D4D', 'rgba(12,14,20,0.85)', 64);
          }
        }
      }
    });
  });

  return { shots: S, cues: CUES };
}
