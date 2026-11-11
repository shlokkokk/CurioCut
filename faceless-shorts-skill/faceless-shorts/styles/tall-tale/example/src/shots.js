// Tall Tale 3D Cinematic Director & Procedural Storytelling Engine
// 100% Dynamic: builds story-driven 3D cartoon worlds with Toon characters, 3D town streets, and executive offices.
import * as THREE from 'three';
import { ctx, clamp, lerp, seg, eo, eio, eob, rr, circle, line } from './core/lib.js';
import { L, Wd, T } from './core/timing.js';
import { camera } from './core/engine.js';
import * as WD from './core/world.js';
import * as PR from './core/props.js';
import { Toon, PROPS } from './core/toon.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const mix = (a, b, k) => a.clone().lerp(b, k);
const blink = (t, off = 0) => (((t + off) % 3.3) < 0.12 ? 1 : 0);

// Cast configuration
const LOOK = {
  hero: { body: '#3E5FA8', pattern: 'vest', patCol: '#2A3F70', hat: 'boater', hatCol: '#E8C77A', band: '#B5372E', neck: 'tie', neckCol: '#E2B33C' },
  clerk: { body: '#4FB3A9', hat: 'visor', hatCol: '#2F8F5B', neck: 'collar', pattern: 'vest', patCol: '#2B5E73', extra: ['pencil'] },
  mayor: { body: '#4A4560', hat: 'tophat', hatCol: '#2A2638', neck: 'bowtie', neckCol: '#D8343F', pattern: 'vest', patCol: '#2A2638', extra: ['mustache'] },
  citizen: { body: '#B98ACF', hat: 'bun', hatCol: '#7A4A2E', pattern: 'apron' },
  townfolk: { body: '#6FA35A', pattern: 'overalls', patCol: '#3E5FA8', hat: 'cap', hatCol: '#2E4E8A' }
};
const person = (k, opts) => new Toon({ ...LOOK[k], extra: [...(LOOK[k]?.extra || [])] }, opts);

// 2D Polish Overlays on top of 3D Canvas
function stepCard(n, label, x, y, sc = 1) {
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(sc, sc);
  ctx.font = '900 50px Inter, sans-serif';
  const tw = ctx.measureText(label).width;
  const w = Math.max(460, tw + 210);

  // Shadow
  ctx.fillStyle = 'rgba(0, 0, 0, 0.4)';
  rr(-w / 2 + 6, -64, w, 138, 28);
  ctx.fill();

  // Dark Navy Glass Card
  ctx.fillStyle = '#181928';
  rr(-w / 2, -70, w, 138, 28);
  ctx.fill();
  ctx.strokeStyle = '#F2B23E';
  ctx.lineWidth = 4;
  ctx.stroke();

  // Number Badge Disc (Gold)
  circle(-w / 2 + 75, 0, 46, '#F2B23E');
  ctx.fillStyle = '#181928';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.font = '900 62px Inter, sans-serif';
  ctx.fillText(String(n), -w / 2 + 75, 4);

  // Chapter Header Text
  ctx.fillStyle = '#FFFFFF';
  ctx.font = '900 48px Inter, sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText(label, -w / 2 + 144, 2);

  ctx.restore();
}

function counterPill(text, x, y, sc = 1, col = '#F2B23E') {
  if (sc <= 0) return;
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(sc, sc);
  ctx.font = '900 46px Inter, sans-serif';
  const w = ctx.measureText(text).width + 80;
  ctx.fillStyle = 'rgba(24, 25, 40, 0.92)';
  rr(-w / 2, -42, w, 84, 42);
  ctx.fill();
  ctx.strokeStyle = col;
  ctx.lineWidth = 4;
  ctx.stroke();
  ctx.fillStyle = col;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 0, 3);
  ctx.restore();
}

export function buildShots(E, script) {
  const S = [], CUES = [], add = (o) => (S.push(o), o), cue = (t, type, o = {}) => CUES.push({ t: +t.toFixed(3), type, ...o });
  const cam = camera(36);
  const LOOKS = {
    street: { bloom: 0.18, aperture: 0.0012, maxblur: 0.008, fov: 42 },
    room: { bloom: 0.28, aperture: 0.001, maxblur: 0.008, fov: 38 },
    field: { bloom: 0.22, aperture: 0.001, maxblur: 0.007, fov: 40 }
  };

  const shoot = (scene, people, from, to, at, at2, k, look, focus) => {
    if (cam.fov !== (look.fov || 36)) { cam.fov = look.fov || 36; cam.updateProjectionMatrix(); }
    cam.position.copy(mix(from, to, k));
    cam.lookAt(at2 ? mix(at, at2, k) : at);
    people.forEach((p) => p && p.face && p.face(cam));
    E.render(scene, cam, { ...look, focus: focus ?? cam.position.distanceTo(at2 ? mix(at, at2, k) : at) });
  };

  // ═════════════════════════ 3D SETS & ARCHITECTURE ═════════════════════════

  // 1. 3D Main Street (Town shops, sidewalks, utility poles, hills, sunlight)
  const SHOP_ORDER = [
    ['CITY HALL', '#C9603F', 'brick', '#D8343F'],
    ['GENERAL STORE', '#6FA3B8', 'wood', null],
    ['TOWN BANK', '#C7B79A', 'brick', '#2E4E8A'],
    ['AUCTION HOUSE', '#E3C16F', 'wood', '#3C6FB6'],
    ['TOWN CAFE', '#E58A6A', 'wood', '#2E4E3F'],
    ['POST OFFICE', '#7FA36A', 'brick', '#2E4E8A']
  ];
  const ST = WD.mainStreet(E, { shops: SHOP_ORDER });
  ST.sun.key.target.position.set(-4, 0, 0);
  ST.sun.key.position.set(5, 13, 6);

  const stHero = person('hero');
  const stCitizen = person('citizen');
  const stTownfolk = person('townfolk');
  [stHero, stCitizen, stTownfolk].forEach((p) => ST.scene.add(p.group));
  const streetPeople = () => [...ST.people, stHero, stCitizen, stTownfolk];

  const view = (scene, from, look, people = []) => {
    const c = new THREE.PerspectiveCamera(42, 4 / 3, 0.1, 800);
    c.position.copy(from);
    c.lookAt(look);
    people.forEach((p) => p && p.face && p.face(c));
    const t = WD.snapshot(E, scene, c);
    t.wrapS = THREE.RepeatWrapping;
    return t;
  };

  // 2. 3D Municipal / Auction Interior Room (Counter, scale, cubbies, window)
  const IN = WD.interior(E, {
    wall: '#2F6B5A',
    motif: '#3B7D69',
    ceiling: '#5A3A2A',
    signText: 'TOWN BANK',
    view: view(ST.scene, V3(2, 1.8, -12), V3(-3, 2.2, 10), ST.people),
    picture: false
  });
  const inScale = PR.platformScale();
  inScale.position.set(4.2, 1.18, -2.0);
  IN.scene.add(inScale);

  const inHero = person('hero');
  const inClerk = person('clerk');
  [inHero, inClerk].forEach((p) => IN.scene.add(p.group));
  const inPeople = [inHero, inClerk];

  // 3. 3D Executive Mayor Office (Mahogany desk, notice posters, window overlooking town)
  const OF = WD.interior(E, {
    w: 7,
    depth: 6,
    wall: '#2E4E8A',
    motif: '#3A5E9C',
    ceiling: '#2A2638',
    floor: '#7A3E24',
    signText: null,
    counterOn: false,
    litter: false,
    view: view(ST.scene, V3(0, 6, 6), V3(0, 3, -40))
  });
  const ofDesk = PR.desk(2.4);
  ofDesk.position.set(0.4, 0, -3.2);
  OF.scene.add(ofDesk);

  const ofNotice = PR.poster(['OFFICIAL', '!TOWN DECREE', 'MAYOR OFFICE', 'BRIDGEVILLE'], { w: 1.3, h: 1.7 });
  ofNotice.position.set(-2.4, 2.1, -5.87);
  OF.scene.add(ofNotice);

  const ofHero = person('hero');
  const ofMayor = person('mayor');
  [ofHero, ofMayor].forEach((p) => OF.scene.add(p.group));
  const ofPeople = [ofHero, ofMayor];

  // 4. 3D Countryside Meadow (Signpost, house, fences, trees, hills)
  const MD = WD.meadow(E, { fenceOn: true });
  MD.sun.key.position.set(9, 14, 8);
  MD.sun.key.target.position.set(5, 0, -6);

  const mdSignpost = PR.signpost([['BRIDGEVILLE 700 AC', 'r'], ['TOWN LIMITS', 'l']]);
  mdSignpost.position.set(3.0, 0, 1.8);
  MD.scene.add(mdSignpost);

  const mdHouse = PR.house({ wall: '#F2E6CF', roof: '#B5553C', door: '#3C6FB6' });
  mdHouse.position.set(0, 0, -6);
  MD.scene.add(mdHouse);

  const mdHero = person('hero');
  const mdCitizen = person('citizen');
  [mdHero, mdCitizen].forEach((p) => MD.scene.add(p.group));
  const mdPeople = [mdHero, mdCitizen];

  // ═════════════════════════ DYNAMIC SCRIPT PARSING ═════════════════════════

  const OP = (typeof window !== 'undefined' && window.OP) || {};
  const scriptContext = script || OP.script || OP.__OPTIONS__?.script || {};
  const rawLines = (scriptContext.lines && scriptContext.lines.length) ? scriptContext.lines : (T.lines || []);
  const title = scriptContext.title || 'Incredible Story';

  const lines = rawLines.length ? rawLines : [
    { text: 'An incredible story that completely defied belief.' },
    { text: 'Nobody ever expected this mistake to happen.' }
  ];

  // Helper to extract clean punchy headline from line text
  const extractHeader = (ln, idx) => {
    if (ln.header) return ln.header.toUpperCase();
    const t = (ln.text || '').toUpperCase();
    if (idx === 0) return title.toUpperCase().slice(0, 38);
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
    const lineStart = isFirst ? 0 : Math.max(0, startVal - 0.06);
    const nextLn = lines[idx + 1];
    const nextStartVal = nextLn ? (nextLn.s ?? nextLn.start ?? L(idx + 1)) : T.dur;
    const lineEnd = Math.max(lineStart + 0.1, nextStartVal - 0.06);

    const lineText = (ln.text || '').toUpperCase();
    const lineHeader = extractHeader(ln, idx);
    const comb = lineText + ' ' + lineHeader;

    // Scene Environment Selector: Intelligently rotate through 3D sets with story relevance
    let sceneType = 'street';
    const cycle = idx % 5;
    if (isFirst) {
      sceneType = 'street_wide';
    } else if (isLast) {
      sceneType = 'office_mayor';
    } else if (comb.includes('ERROR') || comb.includes('MISTAKE') || comb.includes('CONFESS') || comb.includes('CRIME') || comb.includes('GUILT') || comb.includes('SHOCK')) {
      sceneType = 'office_shock';
    } else if (comb.includes('ATM') || comb.includes('BANK') || comb.includes('COUNTER') || comb.includes('BID') || comb.includes('CLERK')) {
      sceneType = (idx % 2 === 0) ? 'interior' : 'interior_hero';
    } else if (comb.includes('OUT') || comb.includes('HOUSE') || comb.includes('LIMITS') || comb.includes('TRAVEL') || comb.includes('JET') || comb.includes('YACHT')) {
      sceneType = 'countryside';
    } else {
      const fallbackSets = ['street', 'interior', 'office_mayor', 'countryside', 'street_wide'];
      sceneType = fallbackSets[cycle];
    }

    // Audio cues
    cue(lineStart, 'whoosh', { gain: 0.5 });
    cue(lineStart + 0.1, 'pop', { gain: 0.5 });
    if (comb.includes('WIN') || comb.includes('MAYOR') || isLast) {
      cue(lineStart + 0.35, 'sparkle', { dur: 0.6 });
    } else if (comb.includes('ERROR') || comb.includes('CATCH') || comb.includes('SHOCK')) {
      cue(lineStart + 0.25, 'boing', { gain: 0.6 });
    }

    add({
      id: `shot_${idx}`,
      at: lineStart,
      note: `${lineHeader}: ${lineText.slice(0, 30)}`,
      draw(lt, d, t, blit) {
        const k = eio(clamp(lt / d));

        // ═════════════ 3D SCENE RENDERING ═════════════
        if (sceneType === 'street_wide') {
          // 3D Town Street Crane Establishing Shot: looking down Main Street
          stHero.at(-5.0, 0.18, -4.5 + k * 2.0);
          stHero.set({ legs: 'walk', phase: t * 7.5, mood: 'happy', armL: [35, 15], armR: [-25, 15], blink: blink(t) });
          stCitizen.at(-3.8, 0.18, -2.2);
          stCitizen.set({ mood: 'happy', armR: [45, -30], blink: blink(t, 1) });
          stTownfolk.at(-5.8, 0.18, -6.8);
          stTownfolk.set({ mood: 'neutral', blink: blink(t, 2) });

          shoot(
            ST.scene,
            streetPeople(),
            V3(-1.0, 5.2, -15.5),
            V3(-2.8, 2.2, -8.0),
            V3(-4.0, 2.0, 0),
            V3(-4.8, 1.35, -2.0),
            k,
            LOOKS.street
          );
        } else if (sceneType === 'street') {
          // 3D Town Street Sidewalk View: Hero walking past storefronts and streetlamp
          stHero.at(-5.0, 0.18, -3.5 + k * 1.5);
          stHero.set({ legs: 'walk', phase: t * 7.5, mood: 'proud', armL: [30, 20], armR: [-20, 20], blink: blink(t) });
          stCitizen.at(-3.6, 0.18, -1.8);
          stCitizen.set({ mood: 'happy', armR: [40, -25], blink: blink(t, 1) });

          shoot(
            ST.scene,
            streetPeople(),
            V3(-2.2, 1.85, 0.5),
            V3(-2.4, 1.75, -1.2),
            V3(-4.8, 1.35, -2.5),
            V3(-4.8, 1.35, -3.5),
            k,
            LOOKS.street
          );
        } else if (sceneType === 'interior') {
          // 3D Interior Bank/Store Room: Two-shot of hero and clerk across counter
          inHero.at(1.7, 0, -2.5);
          inHero.set({ mood: 'proud', armR: [50, -40], armL: [-10, 15], blink: blink(t) });
          inClerk.at(2.9, 0, -2.4);
          inClerk.set({ mood: 'happy', armL: [30, -20], armR: [20, -10], blink: blink(t, 0.8) });
          inScale.set(lerp(20, 50, eob(seg(lt, 0, 0.6))));

          shoot(
            IN.scene,
            inPeople,
            V3(2.3, 1.65, 2.2),
            V3(2.3, 1.55, 1.4),
            V3(2.3, 1.25, -2.5),
            V3(2.3, 1.25, -2.5),
            k,
            LOOKS.room
          );
        } else if (sceneType === 'interior_hero') {
          // 3D Interior Close-Up: Close focus on hero at the teller counter
          inHero.at(1.7, 0, -2.5);
          inHero.set({ mood: 'happy', armR: [60, -30], armL: [20, 15], blink: blink(t) });
          inClerk.at(2.9, 0, -2.4);

          shoot(
            IN.scene,
            inPeople,
            V3(1.7, 1.50, 0.2),
            V3(1.7, 1.40, -0.6),
            V3(1.7, 1.25, -2.5),
            V3(1.7, 1.25, -2.5),
            k,
            LOOKS.room
          );
        } else if (sceneType === 'office_shock') {
          // 3D Executive Office: Dramatic push-in on hero realization/shock
          ofHero.at(0.4, 0, -3.95);
          ofHero.set({ mood: 'shock', armL: [35, -25], armR: [45, -35], sweat: 1, blink: 0 });
          ofMayor.group.visible = false;

          shoot(
            OF.scene,
            ofPeople,
            V3(0.4, 1.75, -1.2),
            V3(0.4, 1.55, -2.2),
            V3(0.4, 1.30, -3.95),
            V3(0.4, 1.30, -3.95),
            k,
            LOOKS.room
          );
        } else if (sceneType === 'countryside') {
          // 3D Meadow / Countryside: Hero and citizen in countryside
          mdHero.at(4.8, 0, 1.8 + k * 0.4);
          mdHero.set({ mood: 'proud', armR: [65, 15], armL: [-10, 15], blink: blink(t) });
          mdCitizen.at(6.2, 0, 2.6);
          mdCitizen.set({ mood: 'happy', armL: [45, -20], blink: blink(t, 1.2) });

          shoot(
            MD.scene,
            mdPeople,
            V3(7.5, 2.2, 7.5),
            V3(6.5, 1.9, 5.8),
            V3(5.5, 1.25, 2.2),
            V3(5.5, 1.25, 2.2),
            k,
            LOOKS.field
          );
        } else {
          // 3D Mayor Office Climax: Hero celebrating as town mayor / boss
          ofHero.at(0.4, 0, -3.95);
          ofHero.set({ mood: 'proud', armL: [60, 60], armR: [60, 60], blink: blink(t) });
          ofMayor.at(-1.5, 0, -3.6);
          ofMayor.group.visible = true;
          ofMayor.set({ mood: 'happy', armR: [45, -45], blink: blink(t, 1) });

          shoot(
            OF.scene,
            ofPeople,
            V3(-0.5, 1.75, -1.0),
            V3(-0.3, 1.60, -1.8),
            V3(-0.5, 1.25, -3.8),
            V3(-0.5, 1.25, -3.8),
            k,
            LOOKS.room
          );
        }

        // Copy 3D WebGL buffer to 2D canvas
        blit();

        // ═════════════ 2D KINETIC OVERLAYS ═════════════
        const popScale = eob(seg(lt, 0.05, 0.35));
        stepCard(idx + 1, lineHeader.slice(0, 22), 540, 230, popScale);

        // Dynamic highlight badge for numbers, metrics, or punchy keywords
        const metricMatch = (ln.text || '').match(/(\$[\d,.]+(?:\s*(?:million|billion|k|m))?|\b\d+(?:\.\d+)?\s*(?:million|billion|dollars|bucks|acres|residents|months|years|hours|days|am|pm)\b)/i);
        if (metricMatch) {
          counterPill(metricMatch[0].toUpperCase(), 540, 360, eob(seg(lt, 0.2, 0.5)), '#FBBF24');
        }
      }
    });
  });

  return { shots: S, cues: CUES };
}
