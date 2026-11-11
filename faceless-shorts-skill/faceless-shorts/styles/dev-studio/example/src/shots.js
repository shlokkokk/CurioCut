// CurioCut Cinematic Camera Director & 3D Scene Orchestrator for Claude-Desk
// Movie-quality direction: Grand cyber world with expansive depth, proper character spacing,
// dynamic presenter performances (zero sword swinging), and floating holographic topic props.
import * as THREE from 'three';
import { L, T } from './core/timing.js';
import { camera } from './core/engine.js';
import { ClaudeBot, SkepticBot } from './core/toon.js';
import { buildCyberWorld } from './core/world.js';
import { createDynamicTopicProp } from './core/props.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const clamp = (v, min = 0, max = 1) => Math.max(min, Math.min(max, v));
const lerp = (a, b, t) => a + (b - a) * t;
const eo = (t) => 1 - Math.pow(1 - t, 3);
const eio = (t) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

export function buildShots(E) {
  const S = [];
  const CUES = [];
  const add = (o) => { S.push(o); return o; };

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#0A0E17');
  scene.fog = new THREE.FogExp2('#0A0E17', 0.016);

  // Cinematic Studio Light Rig (Warm presenter key, vibrant cyan cyber rim, soft ambient)
  const ambientLight = new THREE.AmbientLight('#1E2A3A', 1.8);
  scene.add(ambientLight);

  const keyLight = new THREE.DirectionalLight('#FFF5EB', 3.0);
  keyLight.position.set(3.5, 9, 6.5);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.width = 1024;
  keyLight.shadow.mapSize.height = 1024;
  keyLight.shadow.camera.near = 0.5;
  keyLight.shadow.camera.far = 25;
  keyLight.shadow.bias = -0.001;
  scene.add(keyLight);

  const rimLightL = new THREE.DirectionalLight('#00F0FF', 2.8);
  rimLightL.position.set(-7, 8, -3);
  scene.add(rimLightL);

  const rimLightR = new THREE.DirectionalLight('#FF2A85', 2.0);
  rimLightR.position.set(7, 7, -3);
  scene.add(rimLightR);

  const fillLight = new THREE.PointLight('#FFA726', 1.2, 14);
  fillLight.position.set(0, 3.5, 3.0);
  scene.add(fillLight);

  // Grand Cyber Studio World (Floor, hologram emitter, server monoliths, telemetry screens)
  const world = buildCyberWorld(scene);

  // Characters: Staged on left and right podiums with golden-ratio separation
  // (Left podium: x = -0.92, Right podium: x = +0.92) -> 100% fully inside 9:16 frame with zero clipping
  const claude = new ClaudeBot();
  claude.group.position.set(-0.92, 0, 0.35);
  claude.group.rotation.y = 0.28;
  scene.add(claude.group);

  const skeptic = new SkepticBot();
  skeptic.group.position.set(0.92, 0, 0.35);
  skeptic.group.rotation.y = -0.28;
  scene.add(skeptic.group);

  // Global Script Context
  const OP = (typeof window !== 'undefined' && (window.OP || window.__OPTIONS__)) || {};
  const scriptContext = E?.script || OP.script || OP.__OPTIONS__?.script || {};
  const rawLines = scriptContext.lines || [];
  const scriptLines = rawLines.length ? rawLines : [
    { speaker: 'guide', text: scriptContext.title || 'Breaking Tech Exploit', header: 'TECH INTEL', prop: 'neural_core' },
    { speaker: 'guide', text: `Comment ${scriptContext.cta_keyword || 'FAST'} for direct link`, header: 'COMMENT BELOW', prop: 'comment_ui' }
  ];

  // Build a dynamic procedural 3D topic prop for EACH cut in the script
  const shotProps = scriptLines.map((line, idx) => {
    const isLast = idx === scriptLines.length - 1;
    const propGroup = createDynamicTopicProp(line, scriptContext, idx, isLast);
    propGroup.visible = false;
    scene.add(propGroup);
    return propGroup;
  });

  const cam = camera(35); // 35 deg vertical FOV for natural movie optics (no wide-angle barrel distortion)

  scriptLines.forEach((ln, idx) => {
    const isFirst = idx === 0;
    const isLast = idx === scriptLines.length - 1;
    const startVal = ln.s ?? ln.start ?? L(idx);
    const lineStart = isFirst ? 0 : Math.max(0, startVal - 0.04);
    const nextLn = scriptLines[idx + 1];
    const nextStartVal = nextLn ? (nextLn.s ?? nextLn.start ?? L(idx + 1)) : T.dur;
    const lineEnd = Math.max(lineStart + 0.1, nextStartVal - 0.04);

    const isSpeakingGuide = (ln.speaker || 'guide').toLowerCase() === 'guide';
    const lineText = (ln.text || '').toUpperCase();
    const lineHeader = (ln.header || '').toUpperCase();
    const lineComb = lineText + ' ' + lineHeader;

    // Semantic Presenter Choreography (Strictly NO random swords!)
    let claudeAction = 'idle';
    if (lineComb.includes('CODE') || lineComb.includes('PASTE') || lineComb.includes('INSTALL') || lineComb.includes('CLONE') || lineComb.includes('TERMINAL') || lineComb.includes('AGENT')) {
      claudeAction = 'code';
    } else if (isSpeakingGuide) {
      claudeAction = 'point';
    }

    let skepticMood = 'neutral';
    if (isFirst || lineComb.includes('ACTUAL') || lineComb.includes('WHAT') || lineComb.includes('CAPPING') || lineComb.includes('IMPOSSIBLE')) {
      skepticMood = 'shock';
    } else if (lineComb.includes('COST') || lineComb.includes('MONTH') || lineComb.includes('$') || lineComb.includes('FREE') || lineComb.includes('PAY')) {
      skepticMood = 'money';
    } else if (lineComb.includes('NOT A') || lineComb.includes('HOW') || lineComb.includes('WHY') || lineComb.includes('WAIT')) {
      skepticMood = 'skeptic';
    } else {
      skepticMood = isSpeakingGuide ? 'skeptic' : 'smug';
    }

    add({
      id: `shot_${idx}`,
      at: lineStart,
      note: `${ln.speaker || 'guide'}: ${ln.header || 'EXPLOIT'}`,
      draw(lt, d, t, blit) {
        world.update(t, scriptContext);

        // Dynamic 3D Topic Prop for the active narrative cut
        shotProps.forEach((p, pIdx) => {
          if (pIdx === idx) {
            p.visible = true;
            if (p.update) p.update(t);
          } else {
            p.visible = false;
          }
        });

        // Natural audio-synced lip sync & speech cycles
        const isShowcase = isFirst || isLast;
        const talkVal = Math.abs(Math.sin(t * 14)) * 0.82 + 0.18;
        const blinkVal = ((t + idx * 0.85) % 3.2 < 0.14) ? 1 : 0;

        // Dynamic looking: Characters look at the active speaker or up at the floating hologram prop
        let claudeLook = { lookX: 0.25, lookY: isShowcase ? -0.2 : 0 };
        let skepticLook = { lookX: -0.25, lookY: isShowcase ? -0.2 : 0 };

        if (isSpeakingGuide) {
          claude.set({ mood: 'smug', talk: talkVal, blink: blinkVal, action: claudeAction, ...claudeLook }, t);
          skeptic.set({ mood: skepticMood, talk: 0, blink: blinkVal, ...skepticLook }, t);
          // Subtle body orientation
          claude.group.rotation.y = 0.28;
          skeptic.group.rotation.y = -0.38;
        } else {
          claude.set({ mood: 'neutral', talk: 0, blink: blinkVal, action: 'idle', ...claudeLook }, t);
          skeptic.set({ mood: skepticMood, talk: talkVal, blink: blinkVal, ...skepticLook }, t);
          claude.group.rotation.y = 0.38;
          skeptic.group.rotation.y = -0.26;
        }

        // ==========================================
        // CINEMATIC MOVIE CAMERA DIRECTOR (Glide Panning)
        // ==========================================
        const progress = Math.min(1, lt / Math.max(1, d));

        if (isLast) {
          // Final CTA: Wide balanced establishing shot framing both presenters and glowing CTA card
          const push = progress * 0.15;
          cam.position.set(0, 1.80, 7.6 - push);
          cam.lookAt(V3(0, 1.25, 0.2));
        } else if (isFirst) {
          // Opening Hook: Wide grand cyber establishing shot showing BOTH presenters fully visible
          const push = progress * 0.25;
          cam.position.set(0, 1.82, 7.8 - push);
          cam.lookAt(V3(0, 1.25, 0.2));
        } else if (isSpeakingGuide) {
          // Male Presenter Hero Zoom Shot on Claude: Centered squarely at x = -0.92 (Matching female framing!)
          // Camera smoothly glides from female presenter over to Claude over first 0.6s
          const glideProgress = eio(clamp(lt / 0.6));
          const camX = lerp(0.92, -0.92, glideProgress);
          cam.position.set(camX, 1.42, 4.25);
          cam.lookAt(V3(lerp(0.92, -0.92, glideProgress), 1.05, 0.35));
        } else {
          // Female Presenter Hero Zoom Shot on Skeptic: Centered squarely at x = 0.92 (Perfect framing!)
          // Camera smoothly glides from Claude over to female presenter over first 0.6s
          const glideProgress = eio(clamp(lt / 0.6));
          const camX = lerp(-0.92, 0.92, glideProgress);
          cam.position.set(camX, 1.40, 4.25);
          cam.lookAt(V3(lerp(-0.92, 0.92, glideProgress), 1.02, 0.35));
        }

        // Render WebGL frame with cinematic bloom and subtle depth-of-field
        E.render(scene, cam, { bloom: 0.28, aperture: 0.0007, focus: 4.8 });
        blit();
      }
    });
  });

  return { shots: S, cues: CUES };
}
