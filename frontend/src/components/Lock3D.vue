<template>
  <div class="lock-3d-container" ref="container"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const props = defineProps({
  modelPath: { type: String, default: "/lock.glb" },
  primaryColor: { type: String, default: "#673ee6" },
  secondaryColor: { type: String, default: "#00b090" },
  scale: { type: Number, default: 3 },
  autoRotate: { type: Boolean, default: false },
  rotationSpeed: { type: Number, default: 0.005 },
});

// ── Plain JS vars for scroll-driven rotation ───────────────────────────────
// Bypasses Vue reactivity entirely — no watcher overhead per scroll frame.
const ext = { y: 0, z: 0 }; // set by parent via setScrollRotation()

/** Call this from parent ScrollTrigger onUpdate instead of reactive props. */
function setScrollRotation(y, z = 0) {
  ext.y = y;
  ext.z = z;
}
defineExpose({ setScrollRotation });

// ── Three.js state ──────────────────────────────────────────────────────────
const container = ref(null);
let scene, camera, renderer, lockModel;
let animationId = null;

const maxRotation = Math.PI / 2;
const rotationDamping = 0.06; // slightly lower = less CPU per frame
const targetRotation = { x: 0, y: 0 };

// ── Pointer throttle ────────────────────────────────────────────────────────
let pointerPending = false;
let rawPointer = { x: 0, y: 0 };

function initScene() {
  if (!container.value) return;

  scene = new THREE.Scene();

  const w = container.value.clientWidth;
  const h = container.value.clientHeight;

  camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000);
  camera.position.set(0, 0, 5);

  renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
    powerPreference: "high-performance",
  });
  // Cap pixel ratio at 2 — retina beyond 2× gives negligible visual gain but doubles GPU work
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(w, h);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  // Hint renderer to reduce memory bandwidth
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  container.value.appendChild(renderer.domElement);

  // Lighting
  scene.add(new THREE.AmbientLight(0xffffff, 1.2));

  const dir = new THREE.DirectionalLight(0xffffff, 1.5);
  dir.position.set(5, 10, 7);
  dir.castShadow = true;
  scene.add(dir);

  const rim1 = new THREE.DirectionalLight(props.primaryColor, 0.9);
  rim1.position.set(-5, 3, -3);
  scene.add(rim1);

  const rim2 = new THREE.DirectionalLight(props.secondaryColor, 0.8);
  rim2.position.set(5, -2, -5);
  scene.add(rim2);

  const pt1 = new THREE.PointLight(0xffffff, 1.5, 25);
  pt1.position.set(0, 3, 3);
  scene.add(pt1);

  const fill = new THREE.PointLight(0xffffff, 0.5);
  fill.position.set(-2, -1, 4);
  scene.add(fill);

  loadModel();
}

function loadModel() {
  const loader = new GLTFLoader();
  loader.load(
    props.modelPath,
    (gltf) => {
      lockModel = gltf.scene;

      lockModel.traverse((child) => {
        if (child.isMesh) {
          child.castShadow = true;
          child.receiveShadow = true;
        }
      });

      const box = new THREE.Box3().setFromObject(lockModel);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      const sc = props.scale / maxDim;

      lockModel.scale.multiplyScalar(sc);
      lockModel.position.set(-center.x * sc, -center.y * sc, -center.z * sc);
      scene.add(lockModel);
    },
    undefined,
    (err) => console.error("Lock3D load error:", err),
  );
}

function animate() {
  animationId = requestAnimationFrame(animate);
  if (!lockModel) return; // skip until model is ready

  // Apply throttled pointer target
  if (pointerPending) {
    targetRotation.y = THREE.MathUtils.clamp(rawPointer.x, -1, 1) * maxRotation;
    targetRotation.x =
      THREE.MathUtils.clamp(-rawPointer.y, -1, 1) * maxRotation;
    pointerPending = false;
  }

  // ── Y rotation ────────────────────────────────────────────────────────────
  if (props.autoRotate) {
    lockModel.rotation.y += props.rotationSpeed;
    // Pointer damping on Y only in auto-rotate mode
    lockModel.rotation.y +=
      (targetRotation.y - lockModel.rotation.y) * rotationDamping;
  } else {
    // Scroll-driven — set directly from parent (no Vue proxy in hot path)
    lockModel.rotation.y = ext.y;
  }

  // ── X rotation (pointer tilt) ─────────────────────────────────────────────
  lockModel.rotation.x +=
    (targetRotation.x - lockModel.rotation.x) * rotationDamping;

  // ── Z tilt (per-panel, damped) ────────────────────────────────────────────
  lockModel.rotation.z += (ext.z - lockModel.rotation.z) * rotationDamping;

  renderer.render(scene, camera);
}

function handleResize() {
  if (!container.value || !camera || !renderer) return;
  const w = container.value.clientWidth;
  const h = container.value.clientHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}

// ── Pointer: throttle to one RAF per move burst ─────────────────────────────
function handlePointerMove(e) {
  if (!container.value) return;
  const rect = container.value.getBoundingClientRect();
  rawPointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  rawPointer.y = ((e.clientY - rect.top) / rect.height) * 2 - 1;
  pointerPending = true; // animate() will consume this next frame
}

function handlePointerLeave() {
  rawPointer = { x: 0, y: 0 };
  pointerPending = true;
}

onMounted(() => {
  initScene();
  container.value?.addEventListener("pointermove", handlePointerMove, {
    passive: true,
  });
  container.value?.addEventListener("pointerleave", handlePointerLeave, {
    passive: true,
  });
  window.addEventListener("resize", handleResize, { passive: true });
  animate();
});

onBeforeUnmount(() => {
  container.value?.removeEventListener("pointermove", handlePointerMove);
  container.value?.removeEventListener("pointerleave", handlePointerLeave);
  window.removeEventListener("resize", handleResize);
  if (animationId) cancelAnimationFrame(animationId);
  if (renderer) renderer.dispose();
  if (lockModel) {
    lockModel.traverse((child) => {
      if (child.isMesh) {
        child.geometry.dispose();
        (Array.isArray(child.material)
          ? child.material
          : [child.material]
        ).forEach((m) => m?.dispose());
      }
    });
  }
});
</script>

<style scoped>
.lock-3d-container {
  width: 100%;
  height: 100%;
  min-height: 500px;
  position: relative;
  /* GPU-composited layer so WebGL output doesn't trigger page repaints */
  will-change: transform;
  transform: translateZ(0);
}
</style>
