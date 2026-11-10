// Claude-Desk Cinematic Camera Director & 3D Scene Orchestrator
// Fully dynamic: creates live topic-matched 3D props and context-aware character performances
import * as THREE from 'three';
import { L, T } from './core/timing.js';
import { camera } from './core/engine.js';
import { ClaudeBot, SkepticBot } from './core/toon.js';
import { techStudio, createDynamicTopicProp } from './core/props.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);

export function buildShots(E) {
  const S = [];
  const CUES = [];
  const add = (o) => { S.push(o); return o; };

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#D8CEBF');
  scene.fog = new THREE.FogExp2('#D8CEBF', 0.022);

  // Studio Lighting Rig (Warm key, cyan cyber rim, soft ambient)
  const ambientLight = new THREE.AmbientLight('#FFE8D6', 1.7);
  scene.add(ambientLight);

  const keyLight = new THREE.DirectionalLight('#FFF8F0', 2.8);
  keyLight.position.set(4, 9, 7);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.width = 1024;
  keyLight.shadow.mapSize.height = 1024;
  keyLight.shadow.camera.near = 0.5;
  keyLight.shadow.camera.far = 25;
  keyLight.shadow.bias = -0.001;
  scene.add(keyLight);

  const rimLight = new THREE.DirectionalLight('#00F0FF', 2.2);
  rimLight.position.set(-6, 7, -4);
  scene.add(rimLight);

  const fillLight = new THREE.PointLight('#FF8A50', 1.1, 12);
  fillLight.position.set(0, 3, 2);
  scene.add(fillLight);

  // Warm Tech Studio Architecture + Floating Particles
  const studio = techStudio();
  scene.add(studio);

  // Characters (Positioned with ample stage room, fully in frame)
  const claude = new ClaudeBot();
  claude.group.position.set(-1.15, 0, 0.4);
  claude.group.rotation.y = 0.26;
  scene.add(claude.group);

  const skeptic = new SkepticBot();
  skeptic.group.position.set(1.15, 0, 0.4);
  skeptic.group.rotation.y = -0.26;
  scene.add(skeptic.group);

  // Global Script Context
  const OP = (typeof window !== 'undefined' && (window.OP || window.__OPTIONS__)) || {};
  const scriptContext = E?.script || OP.script || OP.__OPTIONS__?.script || {};
  const rawLines = scriptContext.lines || [];
  const scriptLines = rawLines.length ? rawLines : [
    { speaker: 'guide', text: scriptContext.title || 'Breaking Tech Exploit', header: 'TECH INTEL', prop: 'neural_core' },
    { speaker: 'guide', text: `Comment ${scriptContext.cta_keyword || 'FAST'} for direct link`, header: 'COMMENT BELOW', prop: 'comment_ui' }
  ];

  // Build a dynamic procedural 3D prop for EACH line in the script
  const shotProps = scriptLines.map((line, idx) => {
    const isLast = idx === scriptLines.length - 1;
    const propGroup = createDynamicTopicProp(line, scriptContext, idx, isLast);
    propGroup.visible = false;
    scene.add(propGroup);
    return propGroup;
  });

  const cam = camera(38);

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

    // Semantic character performance analyzer
    let claudeAction = 'idle';
    if (lineComb.includes('KILL') || lineComb.includes('CUT') || lineComb.includes('SWORD') || lineComb.includes('STOP PAYING')) {
      claudeAction = 'slash';
    } else if (lineComb.includes('CODE') || lineComb.includes('PASTE') || lineComb.includes('INSTALL') || lineComb.includes('CLONE')) {
      claudeAction = 'code';
    } else if (isSpeakingGuide) {
      claudeAction = 'point';
    }

    let skepticMood = 'skeptic';
    if (isFirst || lineComb.includes('ACTUAL') || lineComb.includes('WHAT') || lineComb.includes('CAPPING')) {
      skepticMood = 'shock';
    } else if (lineComb.includes('COST') || lineComb.includes('MONTH') || lineComb.includes('$') || lineComb.includes('FREE')) {
      skepticMood = 'money';
    } else if (lineComb.includes('NOT A') || lineComb.includes('HOW')) {
      skepticMood = 'doubt';
    }

    add({
      id: `shot_${idx}`,
      at: lineStart,
      note: `${ln.speaker || 'guide'}: ${ln.header || 'EXPLOIT'}`,
      draw(lt, d, t, blit) {
        studio.update(t);

        // Show only the dynamic prop matching this active shot
        shotProps.forEach((p, pIdx) => {
          if (pIdx === idx) {
            p.visible = true;
            if (p.update) p.update(t);
          } else {
            p.visible = false;
          }
        });

        // Speech and natural facial cycles
        const talkVal = Math.abs(Math.sin(t * 14)) * 0.8 + 0.2;
        const blinkVal = ((t + idx * 0.75) % 3.5 < 0.14) ? 1 : 0;

        if (isSpeakingGuide) {
          claude.set({ mood: 'smug', talk: talkVal, blink: blinkVal, action: claudeAction }, t);
          skeptic.set({ mood: skepticMood, talk: 0, blink: blinkVal }, t);
        } else {
          claude.set({ mood: 'neutral', talk: 0, blink: blinkVal, action: 'idle' }, t);
          skeptic.set({ mood: skepticMood, talk: talkVal, blink: blinkVal }, t);
        }

        // Camera Choreography (Both characters remain in-frame with balanced composition)
        const progress = Math.min(1, lt / Math.max(1, d));

        if (isLast) {
          // Final CTA: Wide centered shot showing both toons + floating comment UI + flying airplane
          cam.position.set(0, 1.82, 4.45 - progress * 0.18);
          cam.lookAt(V3(0, 1.25, 0.2));
        } else if (isFirst) {
          // Opening hook: Dramatic push-in from wide establishing shot
          cam.position.set(0, 1.78, 4.75 - progress * 0.35);
          cam.lookAt(V3(0, 1.18, 0.2));
        } else if (isSpeakingGuide) {
          // Medium two-shot biased slightly toward Claude
          const camX = -0.45 + Math.sin(progress * 0.3) * 0.08;
          cam.position.set(camX, 1.74, 4.15);
          cam.lookAt(V3(-0.55, 1.15, 0.35));
        } else {
          // Medium two-shot biased slightly toward Skeptic
          const camX = 0.45 - Math.sin(progress * 0.3) * 0.08;
          cam.position.set(camX, 1.72, 4.15);
          cam.lookAt(V3(0.55, 1.15, 0.35));
        }

        // Render WebGL frame
        E.render(scene, cam, { bloom: 0.22, aperture: 0.0006, focus: 4.1 });
        blit();
      }
    });
  });

  return { shots: S, cues: CUES };
}
