import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export default function WebGLCanvas() {
  const mountRef = useRef(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, window.innerWidth / Math.max(1, window.innerHeight), 0.1, 100);
    camera.position.set(0, 2.4, 7.2);
    camera.lookAt(0, -0.4, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    container.appendChild(renderer.domElement);

    // Subtle architectural 3D dot-matrix wave field (clean, zero clutter behind text)
    const cols = 42;
    const rows = 28;
    const total = cols * rows;
    const positions = new Float32Array(total * 3);
    const colors = new Float32Array(total * 3);

    const baseCol = new THREE.Color(0xf2efe9);
    const accentCol = new THREE.Color(0xd4ff3e);

    let idx = 0;
    for (let x = 0; x < cols; x++) {
      for (let z = 0; z < rows; z++) {
        const px = (x - cols / 2) * 0.42;
        const pz = (z - rows / 2) * 0.42;
        positions[idx * 3] = px;
        positions[idx * 3 + 1] = 0;
        positions[idx * 3 + 2] = pz;

        const mix = Math.exp(-((px * px + pz * pz) * 0.04));
        const c = baseCol.clone().lerp(accentCol, mix * 0.35);
        colors[idx * 3] = c.r;
        colors[idx * 3 + 1] = c.g;
        colors[idx * 3 + 2] = c.b;
        idx++;
      }
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const mat = new THREE.PointsMaterial({
      size: 0.032,
      vertexColors: true,
      transparent: true,
      opacity: 0.28,
      depthWrite: false,
    });

    const field = new THREE.Points(geo, mat);
    field.position.set(0, -1.35, -1.2);
    scene.add(field);

    const pointer = { x: 0, y: 0 };
    const smooth = { x: 0, y: 0 };
    let scrollY = window.scrollY;

    const onPointerMove = (e) => {
      pointer.x = (e.clientX / window.innerWidth - 0.5) * 2;
      pointer.y = (e.clientY / window.innerHeight - 0.5) * 2;
    };
    const onScroll = () => {
      scrollY = window.scrollY;
    };
    const onResize = () => {
      camera.aspect = window.innerWidth / Math.max(1, window.innerHeight);
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    };

    window.addEventListener('pointermove', onPointerMove, { passive: true });
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onResize);

    let rafId = 0;
    const clock = new THREE.Clock();

    const animate = () => {
      rafId = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();

      smooth.x += (pointer.x - smooth.x) * 0.04;
      smooth.y += (pointer.y - smooth.y) * 0.04;

      const posAttr = geo.attributes.position;
      let i = 0;
      for (let x = 0; x < cols; x++) {
        for (let z = 0; z < rows; z++) {
          const px = posAttr.getX(i);
          const pz = posAttr.getZ(i);
          const wave = Math.sin(px * 0.55 + t * 0.7) * Math.cos(pz * 0.55 + t * 0.55) * 0.24;
          const tilt = (px * smooth.x + pz * smooth.y) * 0.06;
          posAttr.setY(i, wave + tilt);
          i++;
        }
      }
      posAttr.needsUpdate = true;

      field.rotation.y = smooth.x * 0.06;
      field.position.y = -1.35 - Math.min(scrollY * 0.0008, 0.8);

      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onResize);
      geo.dispose();
      mat.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return <div ref={mountRef} className="webgl-bg" aria-hidden="true" />;
}
