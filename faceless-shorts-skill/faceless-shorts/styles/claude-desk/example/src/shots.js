// Claude-Desk Cinematic Camera Director & 3D Scene Orchestrator
import * as THREE from 'three';
import { L, T } from './core/timing.js';
import { camera } from './core/engine.js';
import { ClaudeBot, SkepticBot } from './core/toon.js';
import * as PR from './core/props.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);

export function buildShots(E) {
  const S = [];
  const CUES = [];
  const add = (o) => { S.push(o); return o; };

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#0A0B10');
  scene.fog = new THREE.FogExp2('#0A0B10', 0.04);

  // Studio Lighting Rig
  const ambientLight = new THREE.AmbientLight('#2E344A', 1.8);
  scene.add(ambientLight);

  const keyLight = new THREE.DirectionalLight('#FFF3E8', 2.8);
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

  const fillLight = new THREE.PointLight('#FF5E3A', 1.2, 10);
  fillLight.position.set(0, 3, 2);
  scene.add(fillLight);

  // Studio Desk and Base Environment
  const desk = PR.studioDesk();
  scene.add(desk);

  // Characters
  const claude = new ClaudeBot();
  claude.group.position.set(-1.8, 0.9, 0.1);
  claude.group.rotation.y = 0.32;
  scene.add(claude.group);

  const skeptic = new SkepticBot();
  skeptic.group.position.set(1.8, 0.9, 0.1);
  skeptic.group.rotation.y = -0.32;
  scene.add(skeptic.group);

  // Procedural 3D Props
  const props = {
    sword_cut: PR.swordCutProp(),
    glowing_orb: PR.glowingOrbProp(),
    terminal_desk: PR.terminalDeskProp(),
    falling_letters: PR.fallingLettersProp(),
    scanner_beam: PR.scannerBeamProp(),
    waveform_audio: PR.waveformAudioProp(),
    server_tower: PR.serverTowerProp(),
    comment_ui: PR.commentUiProp(E.cta_keyword || 'JARVIS')
  };

  Object.values(props).forEach((p) => {
    p.visible = false;
    scene.add(p);
  });

  const cam = camera(42);
  const scriptLines = (T.lines && T.lines.length) ? T.lines : [{ s: 0, end: T.dur }];

  scriptLines.forEach((ln, idx) => {
    const isFirst = idx === 0;
    const isLast = idx === scriptLines.length - 1;
    const lineStart = isFirst ? 0 : ln.s - 0.04;
    const nextLn = scriptLines[idx + 1];
    const lineEnd = nextLn ? nextLn.s - 0.04 : T.dur;

    // Determine speaker and prop
    const rawLine = (OP?.script?.lines && OP.script.lines[idx]) || {};
    const speaker = (rawLine.speaker || (idx % 2 === 0 ? 'guide' : 'skeptic')).toLowerCase();
    const propKey = rawLine.prop || (isLast ? 'comment_ui' : 'glowing_orb');

    add({
      id: `shot_${idx}`,
      at: lineStart,
      draw: (lt, d, t, blit) => {
        // Toggle active prop
        Object.entries(props).forEach(([k, p]) => {
          const active = (k === propKey) || (isLast && k === 'comment_ui');
          p.visible = active;
          if (active && p.update) {
            p.update(lt);
          }
        });

        // Animate Characters talking & facial moods
        const isSpeakingGuide = speaker === 'guide';
        const isSpeakingSkeptic = speaker === 'skeptic';
        const talkWave = Math.abs(Math.sin(lt * 16));

        claude.set({
          talk: isSpeakingGuide ? talkWave : 0,
          blink: Math.sin(t * 1.5) > 0.94 ? 1 : 0,
          mood: isSpeakingGuide ? 'excited' : 'neutral',
          look: isSpeakingGuide ? [0.2, 0] : [0.5, 0]
        });

        skeptic.set({
          talk: isSpeakingSkeptic ? talkWave : 0,
          blink: Math.sin(t * 1.8 + 1) > 0.93 ? 1 : 0,
          mood: isSpeakingSkeptic ? 'skeptic' : (idx > 4 ? 'shock' : 'skeptic'),
          look: isSpeakingSkeptic ? [-0.2, 0] : [-0.5, 0]
        });

        // Camera Choreography
        if (isLast) {
          // Final CTA Shot: Centered hero shot of comment UI
          cam.position.set(0, 2.3, 3.8);
          cam.lookAt(V3(0, 1.4, 0.4));
        } else if (isSpeakingGuide) {
          // Camera snaps / pushes in toward Claude
          const progress = Math.min(1, lt / Math.max(1, d));
          const camX = -1.2 + Math.sin(progress * 0.4) * 0.2;
          cam.position.set(camX, 2.2, 3.6);
          cam.lookAt(V3(-0.9, 1.8, 0.2));
        } else {
          // Camera cuts to Skeptic Avatar
          const progress = Math.min(1, lt / Math.max(1, d));
          const camX = 1.2 - Math.sin(progress * 0.4) * 0.2;
          cam.position.set(camX, 2.1, 3.5);
          cam.lookAt(V3(0.9, 1.7, 0.2));
        }

        // Render 3D WebGL scene and blit to 2D canvas
        E.render(scene, cam, { bloom: 0.25, aperture: 0.001, focus: 3.5 });
        blit();
      }
    });
  });

  return { shots: S, cues: CUES };
}
