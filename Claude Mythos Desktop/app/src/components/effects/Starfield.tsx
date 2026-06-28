import { useEffect, useRef } from "react";
import * as THREE from "three";

const vertexShader = `
varying vec3 vWorldPosition;
varying float vVertexId;
attribute float vertexIndex;
uniform float uTime;
uniform float uRotationSpeed;

void main() {
  vWorldPosition = (modelMatrix * vec4(position, 1.0)).xyz;
  vVertexId = vertexIndex;
  vec3 pos = position;
  float angle = uTime * uRotationSpeed;
  float cosA = cos(angle);
  float sinA = sin(angle);
  pos.x = position.x * cosA + position.z * sinA;
  pos.z = -position.x * sinA + position.z * cosA;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
  gl_PointSize = 1.0;
}
`;

const fragmentShader = `
uniform vec3 uBackgroundColor;
uniform float uStarBrightness;
uniform float uStarBloom;
uniform float uStarStretch;
varying vec3 vWorldPosition;
varying float vVertexId;

float rand(vec2 co) {
  return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

float hexDist(vec2 p) {
  p = abs(p);
  return max(p.x + p.y * 0.577350269, p.y * 1.154700538);
}

vec2 hexTile(vec2 p) {
  vec2 s = vec2(1.0, 1.732050808);
  vec2 h = s * 0.5;
  vec2 a = mod(p, s) - h;
  vec2 b = mod(p - h, s) - h;
  return dot(a, a) < dot(b, b) ? a : b;
}

void main() {
  vec2 fragCoord = (vWorldPosition.xz * 0.5 + 0.5) * vec2(800.0, 600.0);
  vec2 uv = fragCoord / vec2(800.0, 600.0) * 2.0 - 1.0;
  uv.x *= 800.0 / 600.0;
  float vignette = 1.0 - smoothstep(0.5, 1.5, length(uv * vec2(0.8, 1.0)));
  vec3 color = mix(uBackgroundColor, uBackgroundColor * 1.2, vignette * 0.3);

  vec2 cellId = floor(fragCoord / 8.0);
  vec2 starUv = hexTile(fragCoord / 8.0);

  float rnd = rand(cellId * 0.01);
  float rnd2 = rand(cellId * 0.03);
  float rnd3 = rand(cellId * 0.07);

  if (rnd > 0.985) {
    float pulse = sin(uStarStretch * 2.0 + rnd3 * 6.28) * 0.5 + 0.5;
    float intensity = (0.5 + 0.5 * pulse) * uStarBrightness * (0.1 + rnd2 * 0.9);

    float stretchAngle = rnd * 6.28;
    float cosA = cos(stretchAngle);
    float sinA = sin(stretchAngle);
    vec2 rotUv = vec2(starUv.x * cosA - starUv.y * sinA, starUv.x * sinA + starUv.y * cosA);

    float stretchFactor = 1.0 + uStarStretch * 4.0;
    rotUv.y *= stretchFactor;

    float d = max(hexDist(rotUv), hexDist(rotUv * 0.7) * 0.6);
    d = mix(d, length(rotUv), 0.3);

    float glow = exp(-d * d * 20.0) * intensity;
    float bloom = exp(-length(starUv) * length(starUv) * 5.0) * intensity * uStarBloom * 0.5;

    vec3 starColor = mix(vec3(0.9, 0.95, 1.0), vec3(1.0, 0.95, 0.8), rnd2);

    color += starColor * glow * 0.8;
    color += starColor * bloom * 0.15;
  }

  gl_FragColor = vec4(color, 1.0);
}
`;

export default function Starfield() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      2000
    );
    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    const starMaterial = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      transparent: true,
      uniforms: {
        uTime: { value: 0 },
        uRotationSpeed: { value: 0.005 },
        uBackgroundColor: { value: new THREE.Color("#FFF8E7") },
        uStarBrightness: { value: 0.8 },
        uStarBloom: { value: 1.0 },
        uStarStretch: { value: 0.0 },
      },
    });

    const starCount = 5000;
    const starGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(starCount * 3);
    const indices = new Float32Array(starCount);

    for (let i = 0; i < starCount; i++) {
      const r = Math.cbrt(Math.random()) * 500;
      const theta = Math.random() * 2 * Math.PI;
      const phi = Math.acos(2 * Math.random() - 1);

      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);
      indices[i] = i;
    }

    starGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    starGeometry.setAttribute("vertexIndex", new THREE.BufferAttribute(indices, 1));

    const starField = new THREE.Points(starGeometry, starMaterial);
    scene.add(starField);

    camera.position.set(0, 80, 0);
    camera.lookAt(0, 0, 0);

    function handleScroll() {
      const scrollY = window.scrollY;
      const maxScroll = document.body.scrollHeight - window.innerHeight;
      const scrollProgress = Math.min(maxScroll > 0 ? scrollY / maxScroll : 0, 1);

      const timeOfDay = 1.0 - scrollProgress;
      const starStretch = scrollProgress * 0.5;
      const starBloom = 1.0 + scrollProgress * 2.0;

      starMaterial.uniforms.uStarStretch.value = starStretch;
      starMaterial.uniforms.uStarBloom.value = starBloom;

      if (timeOfDay > 0.5) {
        starMaterial.uniforms.uBackgroundColor.value = new THREE.Color("#FFF8E7");
      } else {
        starMaterial.uniforms.uBackgroundColor.value = new THREE.Color("#0B0C10");
      }
    }

    window.addEventListener("scroll", handleScroll, { passive: true });

    const clock = new THREE.Clock();
    let animId: number;

    function animate() {
      const elapsedTime = clock.getElapsedTime();
      starMaterial.uniforms.uTime.value = elapsedTime;
      renderer.render(scene, camera);
      animId = requestAnimationFrame(animate);
    }
    animate();

    function handleResize() {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animId);
      starGeometry.dispose();
      starMaterial.dispose();
      renderer.dispose();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        zIndex: 1,
      }}
    />
  );
}
