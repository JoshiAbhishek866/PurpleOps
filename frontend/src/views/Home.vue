<template>
  <div class="home-page">
    <DynamicSEO page="home" />

    <!-- ═══ Floating Lock — position:fixed, GSAP-driven ═══ -->
    <div class="lock-float" ref="lockFloat">
      <Lock3D
        ref="lockRef"
        :modelPath="animationSettings.modelPath"
        :primaryColor="animationSettings.primaryColor"
        :secondaryColor="animationSettings.secondaryColor"
        :scale="animationSettings.scale"
        :autoRotate="false"
        :rotationSpeed="animationSettings.rotationSpeed"
      />
    </div>

    <!-- ═══ PHASE 1: Hero (split heading, lock between lines) ═══ -->
    <section class="hero-section" ref="heroRef" data-testid="hero-section">
      <!-- "Engineered to Protect." — above the lock arch -->
      <div class="hero-line-top hero-animate">
        <span class="hero-top-text">Built to Break</span>
      </div>

      <!-- "Built to Break." — overlapping the lock body below the U-arch -->
      <div class="hero-line-bottom hero-animate">
        <span class="hero-bottom-text">Engineered to Protect</span>
      </div>
    </section>

    <!-- ═══ PHASE 2: Marquee (black glassmorphism, z-index above lock) ═══ -->
    <div class="marquee-wrap" ref="marqueeWrapRef">
      <MarqueeStrip />
    </div>

    <!-- ═══ PHASE 3: Achievement Scroll Story ═══ -->
    <!-- Outer div is tall enough (4×100vh) to create scroll space -->
    <div class="achieve-story" ref="achieveStoryRef">
      <!-- Sticky viewport — lock centers here -->
      <div class="achieve-sticky">
        <!-- Scroll-animated heading: sweeps right → left on scroll -->
        <div class="achieve-headline-wrap" ref="headlineEl">
          <span class="achieve-headline">Trusted by Industry Leaders</span>
        </div>
        <!-- Achievement panels (shown after heading exits) -->
        <div
          v-for="(a, i) in storyAchievements"
          :key="a.id"
          class="achieve-panel"
          :ref="
            (el) => {
              if (el) panelEls[i] = el;
            }
          "
        >
          <div
            class="stat-wrap"
            :class="i % 2 === 0 ? 'stat-left' : 'stat-right'"
          >
            <component :is="a.icon" class="stat-svg" />
            <div class="stat-num">{{ a.display }}</div>
            <div class="stat-label">{{ a.label }}</div>
            <p class="stat-desc">{{ a.desc }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ PHASE 4: Features — CRFTD-style sticky scroll story ═══ -->
    <div
      class="feat-story"
      ref="featuresSection"
      data-testid="features-section"
      :style="{ height: `calc((${displayFeatures.length} + 1) * 100vh)` }"
    >
      <div class="feat-sticky">
        <!-- Scroll-animated heading: sweeps right → left on scroll -->
        <div class="feat-headline-wrap" ref="featHeadlineEl">
          <span class="feat-headline">Advanced Security Features</span>
        </div>

        <div class="feat-content" ref="featContentRef">
          <!-- LEFT: stacked feature names -->
          <div class="feat-left">
            <ul class="feat-list">
              <li
                v-for="(feature, i) in displayFeatures"
                :key="i"
                class="feat-list-item"
                :class="{ 'is-active': featActiveIdx === i }"
              >
                {{ feature.title }}
              </li>
            </ul>
            <div class="feat-counter">
              <span>{{ featActiveIdx + 1 }}</span>
              <span class="feat-counter-sep">&nbsp;—&nbsp;</span>
              <span>{{ displayFeatures.length }}</span>
            </div>
          </div>

          <!-- RIGHT: active feature detail -->
          <div class="feat-right">
            <div
              v-for="(feature, i) in displayFeatures"
              :key="i"
              class="feat-detail"
              :class="{ 'is-active': featActiveIdx === i }"
            >
              <div class="feat-detail-icon">
                <component :is="getFeatureIcon(i)" class="feat-icon-svg" />
              </div>
              <h3 class="feat-detail-title">{{ feature.title }}</h3>
              <p class="feat-detail-desc">{{ feature.description }}</p>
              <div v-if="feature.benefit" class="feat-detail-benefit">
                {{ feature.benefit }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Demo CTA -->
    <section class="demo-section glass" data-testid="demo-section">
      <div class="container">
        <div class="demo-content">
          <div class="demo-text">
            <h2 class="demo-title">{{ demoTitle }}</h2>
            <h2 class="demo-title2">{{ demoTitle2 }}</h2>
            <p class="demo-description">{{ demoDescription }}</p>
            <LuxuryButton
              @click="$router.push(demoButtonLink)"
              size="xl"
              data-testid="demo-cta-button"
              >{{ demoButtonText }}</LuxuryButton
            >
          </div>
          <div class="demo-image">
            <img
              src="https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600&h=400&fit=crop"
              alt="Security Operations Center"
            />
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import LuxuryButton from "@/components/LuxuryButton.vue";
import Lock3D from "@/components/Lock3D.vue";
import MarqueeStrip from "@/components/MarqueeStrip.vue";
import DynamicSEO from "@/components/DynamicSEO.vue";
import { useContentStore } from "@/stores/content";
import { pageLoaded } from "@/composables/usePageLoader";
import {
  ShieldCheckIcon,
  EyeIcon,
  BoltIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  ClockIcon,
} from "@heroicons/vue/24/outline";

gsap.registerPlugin(ScrollTrigger);

const store = useContentStore();

// ── Template refs ──────────────────────────────────────────────────────────
const lockFloat = ref(null);
const lockRef = ref(null); // imperative handle to Lock3D
const heroRef = ref(null);
const marqueeWrapRef = ref(null);
const achieveStoryRef = ref(null);
const featuresSection = ref(null);
const featHeadlineEl = ref(null);
const featContentRef = ref(null);
const panelEls = ref([]);
const headlineEl = ref(null);
const featActiveIdx = ref(0);
// helper: update lock rotation without any Vue reactivity overhead
const setLockRot = (y, z = 0) => lockRef.value?.setScrollRotation(y, z);

// ── Story achievements ─────────────────────────────────────────────────────
const storyAchievements = [
  {
    id: "threats",
    display: "50M+",
    label: "Threats Blocked Daily",
    desc: "AI-powered detection blocks millions of attacks across every vector, every day.",
    icon: ShieldCheckIcon,
  },
  {
    id: "uptime",
    display: "99.9%",
    label: "Uptime Guarantee",
    desc: "Enterprise-grade availability so your security coverage never has a gap.",
    icon: ClockIcon,
  },
  {
    id: "clients",
    display: "500+",
    label: "Enterprise Clients",
    desc: "Trusted by organisations across finance, healthcare, government and tech.",
    icon: ChartBarIcon,
  },
  {
    id: "monitoring",
    display: "24/7",
    label: "Security Monitoring",
    desc: "Our SOC team monitors your infrastructure around the clock—zero blind spots.",
    icon: EyeIcon,
  },
];

// ── Content store computed ─────────────────────────────────────────────────
const heroTitle = computed(() => {
  const t = store.hero?.title || "Secure Your Digital Assets with";
  return t.replace(/\s*(PurpleOps|with PurpleOps)\s*$/i, "").trim() + " ";
});
const heroSubtitle = computed(
  () =>
    store.hero?.subtitle ||
    "Advanced cybersecurity analytics and threat detection platform designed for modern organizations.",
);
const animationSettings = computed(() => ({
  modelPath: store.hero?.animation?.modelPath || "/lock.glb",
  primaryColor: store.hero?.animation?.primaryColor || "#673ee6",
  secondaryColor: store.hero?.animation?.secondaryColor || "#00b090",
  scale: store.hero?.animation?.scale || 3,
  autoRotate: true,
  rotationSpeed: store.hero?.animation?.rotationSpeed || 0.005,
}));
const featuresTitle = computed(
  () => store.features?.title || "Advanced Security Features",
);
const displayFeatures = computed(() =>
  store.features?.items?.length
    ? store.features.items
    : [
        {
          title: "Real-Time Threat Detection",
          description:
            "AI-powered detection identifies attacks in milliseconds.",
          benefit: "Stay ahead of emerging threats",
        },
        {
          title: "Advanced Monitoring",
          description:
            "Comprehensive visibility across your entire digital infrastructure.",
          benefit: "Complete oversight of your security landscape",
        },
        {
          title: "Automated Response",
          description: "Instant automated responses to security threats.",
          benefit: "Minimize damage immediately",
        },
        {
          title: "Analytics Dashboard",
          description: "Rich analytics and reporting for security insights.",
          benefit: "Data-driven security decisions",
        },
      ],
);
const demoTitle = computed(
  () => store.hero?.demoTitle || "Ready to Protect Your",
);
const demoTitle2 = computed(() => store.hero?.demoTitle2 || "Organization?");
const demoDescription = computed(
  () =>
    store.hero?.demoDescription ||
    "Get a personalized demonstration of PurpleOps.",
);
const demoButtonText = computed(
  () => store.hero?.demoButtonText || "Schedule Your Demo Today",
);
const demoButtonLink = computed(
  () => store.hero?.demoButtonLink || "/book-demo",
);

const featureIcons = [
  ShieldCheckIcon,
  EyeIcon,
  BoltIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  ClockIcon,
];
function getFeatureIcon(i) {
  return featureIcons[i % featureIcons.length];
}
function scrollDown() {
  window.scrollBy({ top: window.innerHeight, behavior: "smooth" });
}

// ── Hero entry animation ───────────────────────────────────────────────────
function runHeroEntry() {
  const tl = gsap.timeline({ defaults: { ease: "power3.out" } });
  tl.fromTo(
    ".hero-line-top",
    { y: -50, opacity: 0 },
    { y: 0, opacity: 1, duration: 1.3 },
  )
    .fromTo(
      ".hero-line-bottom",
      { y: 50, opacity: 0 },
      { y: 0, opacity: 1, duration: 1.3 },
      "-=1.0",
    )
    .to(lockFloat.value, { opacity: 1, duration: 0.9 }, "-=0.9");
}

// ── Scroll story animations ────────────────────────────────────────────────
function initScrollAnimations() {
  // Lock starts: centered horizontally, slightly above center (overlaps title)
  gsap.set(lockFloat.value, { xPercent: -50, yPercent: -65 });

  // Phase 1→2: drift to true center as marquee crosses
  ScrollTrigger.create({
    trigger: marqueeWrapRef.value,
    start: "top 80%",
    end: "bottom 20%",
    scrub: true,
    onUpdate(self) {
      gsap.set(lockFloat.value, { yPercent: -65 + self.progress * 15 });
    },
  });

  // ── HERO → ACHIEVEMENTS: 1st full rotation (0 → 2π)
  ScrollTrigger.create({
    trigger: heroRef.value,
    start: "top top",
    endTrigger: achieveStoryRef.value,
    end: "top top",
    scrub: 1,
    onUpdate(self) {
      setLockRot(self.progress * Math.PI * 2);
    },
  });

  // ── HEADING SWEEP: 2nd full rotation (2π → 4π)
  // Runs for the first 20% of achieve-story scroll (= 1×100vh of scroll space)
  // so the lock spins once MORE as the heading text crosses the screen.
  const HEADING_PHASE = 0.2;
  ScrollTrigger.create({
    trigger: achieveStoryRef.value,
    start: "top top",
    end: "20% top", // 20% of achieve-story height = 1×100vh
    scrub: 1,
    onUpdate(self) {
      setLockRot(Math.PI * 2 + self.progress * Math.PI * 2);
    },
  });

  ScrollTrigger.create({
    trigger: achieveStoryRef.value,
    start: "top top",
    end: "bottom bottom",
    scrub: 1.2,
    onUpdate(self) {
      const p = self.progress;
      const hl = headlineEl.value?.querySelector(".achieve-headline");

      if (p < HEADING_PHASE) {
        // ── Heading phase: sweep right → left ───────────────────────────
        const hp = p / HEADING_PHASE; // 0 → 1
        // Text is ~160vw wide at 9vw font size.
        // Start: +100vw  (right edge → "Trusted" just entering)
        // End:   -210vw  (well past full text width → "Leaders" has exited)
        // Total travel: 310vw  ensures every word is seen.
        const xVW = 100 - hp * 310;
        if (hl) {
          gsap.set(hl, { x: `${xVW}vw`, opacity: 1 });
        }
        // Keep all panels hidden
        panelEls.value.forEach(
          (el) => el && gsap.set(el, { opacity: 0, y: 40 }),
        );
      } else {
        // ── Panels phase: heading is gone, panels cycle ──────────────────
        if (hl) gsap.set(hl, { x: "-120vw", opacity: 0 });

        const pp = (p - HEADING_PHASE) / (1 - HEADING_PHASE); // 0 → 1
        const num = storyAchievements.length;

        panelEls.value.forEach((el, i) => {
          if (!el) return;
          const s0 = i / num,
            s1 = (i + 1) / num;
          let op = 0,
            y = 40;
          if (pp >= s0 && pp < s1) {
            const loc = (pp - s0) / (s1 - s0);
            if (loc < 0.2) {
              op = loc / 0.2;
              y = 40 * (1 - op);
            } else if (loc > 0.8) {
              op = (1 - loc) / 0.2;
              y = 0;
            } else {
              op = 1;
              y = 0;
            }
          }
          gsap.set(el, { opacity: op, y });
        });

        // Z-axis tilt per panel — imperative, no Vue proxy overhead
        const tiltsRad = [0, 0.21, -0.14, 0.24];
        const idx = Math.min(Math.floor(pp * num), num - 1);
        setLockRot(Math.PI * 4, tiltsRad[idx]); // Y stays at 4π, just update Z
      }
    },
  });

  // Phase 3→4: lock exits downward as features story enters
  ScrollTrigger.create({
    trigger: featuresSection.value,
    start: "top 90%",
    end: "top top",
    scrub: true,
    onUpdate(self) {
      gsap.set(lockFloat.value, { yPercent: -50 + self.progress * 160 });
    },
  });

  // Phase 4: CRFTD-style feature scroll story with Heading Phase
  ScrollTrigger.create({
    trigger: featuresSection.value,
    start: "top top",
    end: "bottom bottom",
    scrub: 1.2,
    onUpdate(self) {
      const p = self.progress;
      const totalFeatures = displayFeatures.value.length;
      const headingPhase = 1 / (totalFeatures + 1);
      const hl = featHeadlineEl.value?.querySelector(".feat-headline");
      const contentGrid = featContentRef.value;

      if (p < headingPhase) {
        // Heading sweep phase: sweep right → left
        const hp = p / headingPhase;
        const xVW = 100 - hp * 310;
        if (hl) gsap.set(hl, { x: `${xVW}vw`, opacity: 1 });
        if (contentGrid) gsap.set(contentGrid, { opacity: 0, y: 150 });
      } else {
        // Features cycling phase
        if (hl) gsap.set(hl, { x: "-120vw", opacity: 0 });

        const pp = (p - headingPhase) / (1 - headingPhase);

        // First 8% of remaining scroll is dedicated to a smooth slide-in
        const entryFraction = 0.08;
        if (pp < entryFraction) {
          const entryP = pp / entryFraction;
          if (contentGrid) {
            gsap.set(contentGrid, {
              opacity: Math.pow(entryP, 1.5), // Smooth ease-in curve
              y: 150 * (1 - entryP),
            });
          }
        } else {
          if (contentGrid) gsap.set(contentGrid, { opacity: 1, y: 0 });
        }

        const idx = Math.min(Math.floor(pp * totalFeatures), totalFeatures - 1);
        featActiveIdx.value = idx;
      }
    },
  });
}

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(() => {
  store.fetchHero();
  store.fetchFeatures();

  // Start hidden
  gsap.set([".hero-line-top", ".hero-line-bottom"], { opacity: 0 });
  gsap.set(lockFloat.value, { opacity: 0 });

  if (pageLoaded.value) {
    runHeroEntry();
  } else {
    const stop = watch(pageLoaded, (ready) => {
      if (ready) {
        runHeroEntry();
        stop();
      }
    });
  }

  initScrollAnimations();
});

onUnmounted(() => {
  ScrollTrigger.getAll().forEach((t) => t.kill());
});
</script>

<style scoped>
/* ── Floating Lock ──────────────────────────────────────────────────────── */
.lock-float {
  position: fixed;
  top: 50%;
  left: 50%;
  width: 420px;
  height: 420px;
  z-index: 10;
  pointer-events: none;
  opacity: 0; /* GSAP reveals it */
  will-change: transform, opacity;
  transform: translateZ(0); /* promote to own compositing layer */
}

/* ── Home page wrapper ──────────────────────────────────────────────────── */
.home-page {
  min-height: 100vh;
  /* NO transform/filter here — keeps fixed lock in root stacking context */
}

/* ── PHASE 1: Hero ──────────────────────────────────────────────────────── */
.hero-section {
  height: 100vh;
  position: relative;
  z-index: 5;
  overflow: hidden;
}

/* "Engineered to Protect." — above the lock arch */
.hero-line-top {
  position: absolute;
  top: 16%;
  left: 0;
  width: 100%;
  text-align: center;
  z-index: 5;
  pointer-events: none;
}

/* "Built to Break." — at the lock body (below U-arch) */
.hero-line-bottom {
  position: absolute;
  top: 66%;
  left: 0;
  width: 100%;
  text-align: center;
  z-index: 5;
  pointer-events: none;
}

.hero-top-text {
  font-family: var(--font-heading) !important;
  font-size: clamp(1.2rem, 2.8vw, 2.5rem);
  line-height: 1.5;
  color: #1a202c;
  white-space: nowrap;
}

.hero-bottom-text {
  font-family: var(--font-heading) !important;
  font-size: clamp(1.6rem, 4.2vw, 3.8rem);
  line-height: 1.5;
  color: #1a202c;
  white-space: nowrap;
}

.hero-center {
  max-width: 820px;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.hero-title {
  font-size: clamp(1.1rem, 2.2vw, 1.75rem);
  font-weight: 400;
  line-height: 1.9;
  color: #1a202c;
}

.hero-description {
  font-family: var(--font-body);
  font-size: 1.1rem;
  color: #4b5563;
  max-width: 56ch;
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
  justify-content: center;
}

.scroll-hint {
  font-family: var(--font-body);
  font-size: 0.85rem;
  color: #9ca3af;
  background: none;
  border: none;
  cursor: pointer;
  letter-spacing: 0.05em;
  transition: color 0.2s;
}
.scroll-hint:hover {
  color: #673ee6;
}

/* ── PHASE 2: Marquee wrapper (z-index ABOVE lock) ──────────────────────── */
.marquee-wrap {
  position: relative;
  z-index: 25; /* lock is 10 — marquee covers it */
}

/* ── PHASE 3: Achievement Scroll Story ──────────────────────────────────── */
.achieve-story {
  height: calc(5 * 100vh + 120px); /* 1 for heading sweep + 4 for panels */
  background: #0a0a0a;
  position: relative;
  z-index: 5; /* behind lock (z:10) — lock floats on top */
}

.achieve-sticky {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  contain: layout style; /* isolate repaint to this element */
}

/* Heading sweep — starts off-screen right, exits left */
.achieve-headline-wrap {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  overflow: hidden;
  pointer-events: none;
}

.achieve-headline {
  font-family: var(--font-heading) !important;
  font-size: clamp(2.5rem, 9vw, 8rem);
  color: #ffffff;
  white-space: nowrap;
  line-height: 1;
  will-change: transform;
  transform: translateX(80vw); /* GSAP overrides this */
  letter-spacing: 0.03em;
}

.achieve-panel {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  opacity: 0; /* GSAP controls visibility */
  pointer-events: none;
}

.stat-wrap {
  max-width: 360px;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  padding: 2rem;
  position: relative;

  /* Cyber glassmorphism */
  background-color: rgba(10, 10, 15, 0.65);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);

  /* Main border */
  border: 1px solid rgba(0, 176, 144, 0.3);

  /* 4 corner squares using gradients layered exactly to the border edge */
  background-image:
    linear-gradient(#00b090, #00b090), linear-gradient(#00b090, #00b090),
    linear-gradient(#00b090, #00b090), linear-gradient(#00b090, #00b090);
  background-size: 6px 6px;
  background-repeat: no-repeat;
  background-origin: border-box;
  background-position:
    top 0 left 0,
    top 0 right 0,
    bottom 0 left 0,
    bottom 0 right 0;

  /* Subtle inner glow */
  box-shadow: inset 0 0 30px rgba(0, 176, 144, 0.05);
  border-radius: 2px;
}

/* Left panels: 8–35% from left edge */
.stat-left {
  margin-left: 8%;
  margin-right: auto;
  text-align: left;
}
/* Right panels: 8–35% from right edge */
.stat-right {
  margin-left: auto;
  margin-right: 8%;
  text-align: right;
}

.stat-svg {
  width: 2rem;
  height: 2rem;
  color: #00b090;
}
.stat-right .stat-svg {
  margin-left: auto;
}

.stat-num {
  font-family: var(--font-heading);
  font-size: clamp(1.8rem, 4vw, 3.2rem);
  color: #ffffff;
  line-height: 1.2;
}

.stat-label {
  font-family: var(--font-body);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #a78bfa;
}

.stat-desc {
  font-family: var(--font-body);
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.55);
  line-height: 1.6;
  max-width: 26ch;
}

/* ── PHASE 4: CRFTD Features Scroll Story ───────────────────────────────── */

/* Outer tall container — N features × 100vh creates the scroll space */
.feat-story {
  position: relative;
  z-index: 20; /* sits above the lock */
  /* Solid background — matched exactly to achieve-story black */
  background: #0a0a0a;
  border-top: 1px solid rgba(139, 92, 246, 0.18);
}

/* Sticky viewport — always fills the screen */
.feat-sticky {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  contain: layout style; /* isolate repaint */
}

/* Heading sweep — starts off-screen right, exits left */
.feat-headline-wrap {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  overflow: hidden;
  pointer-events: none;
}

.feat-headline {
  font-family: var(--font-heading) !important;
  font-size: clamp(2.5rem, 9vw, 8rem);
  color: #ffffff;
  white-space: nowrap;
  line-height: 1;
  will-change: transform;
  transform: translateX(80vw); /* GSAP overrides this */
  letter-spacing: 0.03em;
}

.feat-content {
  display: grid;
  grid-template-columns: 42% 58%;
  width: 100%;
  height: 100%;
  opacity: 0; /* JS handles this */
}

/* LEFT column */
.feat-left {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 4rem 3rem 4rem 5rem;
  border-right: 1px solid rgba(255, 255, 255, 0.07);
}

.feat-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.feat-list-item {
  font-family: var(--font-heading);
  font-size: clamp(0.55rem, 1.4vw, 1rem);
  line-height: 2;
  color: rgba(255, 255, 255, 0.2);
  transition:
    color 0.35s,
    font-size 0.35s;
  white-space: nowrap;
  cursor: default;
}

.feat-list-item.is-active {
  color: #ffffff;
  font-size: clamp(0.7rem, 1.7vw, 1.25rem);
}

.feat-counter {
  margin-top: 3rem;
  font-family: var(--font-body);
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
}
.feat-counter-sep {
  color: #a78bfa;
}

/* RIGHT column */
.feat-right {
  position: relative;
  display: flex;
  align-items: center;
  padding: 4rem 4rem 4rem 3rem;
}

.feat-detail {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 4rem 4rem 4rem 3rem;
  opacity: 0;
  transform: translateY(30px);
  transition:
    opacity 0.4s ease,
    transform 0.4s ease;
  pointer-events: none;
}

.feat-detail.is-active {
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}

.feat-detail-icon {
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 0.75rem;
  background: rgba(103, 62, 230, 0.15);
  border: 1px solid rgba(103, 62, 230, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 2rem;
  color: #a78bfa;
}

.feat-icon-svg {
  width: 1.75rem;
  height: 1.75rem;
}

.feat-detail-title {
  font-family: var(--font-heading);
  font-size: clamp(0.8rem, 2vw, 1.6rem);
  font-weight: 400;
  line-height: 1.8;
  color: #ffffff;
  margin-bottom: 1.25rem;
}

.feat-detail-desc {
  font-family: var(--font-body);
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.75;
  max-width: 48ch;
  margin-bottom: 1.5rem;
}

.feat-detail-benefit {
  font-family: var(--font-body);
  font-size: 0.82rem;
  color: #a78bfa;
  padding: 0.6rem 1rem;
  border-radius: 0.5rem;
  background: rgba(103, 62, 230, 0.1);
  border: 1px solid rgba(103, 62, 230, 0.2);
  width: fit-content;
}

/* ── Demo Section ───────────────────────────────────────────────────────── */
.demo-section {
  padding: 6rem 0;
}
.demo-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
  align-items: center;
}
.demo-text {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.demo-title,
.demo-title2 {
  font-size: clamp(0.85rem, 1.6vw, 1.25rem);
  font-weight: 400;
  line-height: 1.9;
  color: #1a202c;
}
.demo-description {
  font-family: var(--font-body);
  font-size: 1rem;
  color: #4b5563;
  line-height: 1.7;
}
.demo-image img {
  width: 100%;
  border-radius: 1rem;
  object-fit: cover;
}

/* ── Common ─────────────────────────────────────────────────────────────── */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}
.text-gradient {
  color: #673ee6;
}
.section-title {
  text-align: center;
  margin-bottom: 1rem;
}

@media (max-width: 768px) {
  .lock-float {
    width: 280px;
    height: 280px;
  }
  .stat-left {
    margin-left: 4%;
  }
  .stat-right {
    margin-right: 4%;
  }
  .demo-content {
    grid-template-columns: 1fr;
  }
  .stat-num {
    font-size: clamp(1.4rem, 8vw, 2rem);
  }
}
</style>
