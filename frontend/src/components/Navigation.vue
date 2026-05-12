<template>
  <header
    ref="headerRef"
    class="site-header"
    :class="{ 'is-reduced': isReduced, 'is-scrolled': isScrolled }"
  >
    <nav class="site-nav" :class="isReduced ? 'nav-centered' : 'nav-spread'">
      <!-- Left Side - Logo + Name -->
      <div class="nav-brand">
        <router-link to="/" class="brand-link">
          <img src="/logo1.png" alt="Sentinel AI Logo" class="brand-logo" />
          <span class="brand-name">Sentinel AI</span>
        </router-link>
      </div>

      <!-- Center - Navigation Links -->
      <div v-if="!isReduced" class="nav-links">
        <router-link
          v-for="link in navLinks"
          :key="link.name"
          :to="link.path"
          class="nav-link"
          :data-testid="`nav-${link.name.toLowerCase()}`"
        >
          <span v-scramble>{{ link.name }}</span>
        </router-link>
      </div>

      <!-- Right Side -->
      <div class="nav-actions" :class="isReduced ? 'nav-actions-reduced' : ''">
        <!-- Book Demo -->
        <router-link
          v-if="!isReduced"
          to="/book-demo"
          class="nav-link"
          data-testid="book-demo-button"
        >
          <span v-scramble>Book Demo</span>
        </router-link>

        <!-- Auth Section -->
        <div v-if="!isReduced" class="nav-auth">
          <div v-if="!isAuthenticated" class="nav-auth-guest">
            <router-link
              to="/auth/login"
              class="nav-login"
              data-testid="login-button"
            >
              <span v-scramble>Login</span>
            </router-link>
          </div>

          <div v-else class="nav-user">
            <!-- Notifications -->
            <NotificationsDropdown v-if="isAuthenticated" />

            <div class="user-menu-wrap" ref="userMenuRef">
              <button
                @click="toggleUserMenu"
                class="user-avatar-btn"
                data-testid="user-menu-button"
              >
                <span>{{ userInitials }}</span>
              </button>

              <div v-if="showUserMenu" class="user-dropdown">
                <div class="user-dropdown-info">
                  <p class="user-name">
                    {{ user?.firstName }} {{ user?.lastName }}
                  </p>
                  <p class="user-role">{{ user?.role }}</p>
                </div>
                <div class="dropdown-divider"></div>
                <router-link
                  to="/dashboard"
                  class="dropdown-item"
                  @click="showUserMenu = false"
                  data-testid="dashboard-link"
                  >Dashboard</router-link
                >
                <router-link
                  to="/dashboard/settings"
                  class="dropdown-item"
                  @click="showUserMenu = false"
                  data-testid="settings-link"
                  >Settings</router-link
                >
                <div class="dropdown-divider"></div>
                <button
                  @click="handleLogout"
                  class="dropdown-item dropdown-item-danger"
                  data-testid="logout-button"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useContentStore } from "@/stores/content";
import NotificationsDropdown from "@/components/NotificationsDropdown.vue";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { pageLoaded } from "@/composables/usePageLoader";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

// ── Scramble-text directive ────────────────────────────────────────────────
// Characters used during the scramble phase — binary aesthetic
const SCRAMBLE_CHARS = "01";

const vScramble = {
  mounted(el) {
    const original = el.textContent.trim();
    let rafId = null;
    let startTime = null;
    const DURATION = 600; // ms total scramble duration

    function scrambleFrame(ts) {
      if (!startTime) startTime = ts;
      const elapsed = ts - startTime;
      const progress = Math.min(elapsed / DURATION, 1);
      // Reveal characters left-to-right as progress increases
      const revealedCount = Math.floor(progress * original.length);

      el.textContent = original
        .split("")
        .map((char, i) => {
          if (char === " ") return " ";
          if (i < revealedCount) return original[i];
          return SCRAMBLE_CHARS[
            Math.floor(Math.random() * SCRAMBLE_CHARS.length)
          ];
        })
        .join("");

      if (progress < 1) {
        rafId = requestAnimationFrame(scrambleFrame);
      } else {
        el.textContent = original; // guarantee final text is exact
      }
    }

    function startScramble() {
      if (rafId) cancelAnimationFrame(rafId);
      startTime = null;
      rafId = requestAnimationFrame(scrambleFrame);
    }

    function stopScramble() {
      if (rafId) cancelAnimationFrame(rafId);
      rafId = null;
      el.textContent = original;
    }

    el._scrambleStart = startScramble;
    el._scrambleStop = stopScramble;
    el.addEventListener("mouseenter", startScramble);
    el.addEventListener("mouseleave", stopScramble);
  },
  beforeUnmount(el) {
    if (el._scrambleStart)
      el.removeEventListener("mouseenter", el._scrambleStart);
    if (el._scrambleStop)
      el.removeEventListener("mouseleave", el._scrambleStop);
  },
};

const router = useRouter();
const authStore = useAuthStore();
const contentStore = useContentStore();

const headerRef = ref(null);
const userMenuRef = ref(null);
const isScrolled = ref(false);
const isReduced = ref(false);
const showUserMenu = ref(false);

const isAuthenticated = computed(() => authStore.isAuthenticated());
const user = computed(() => authStore.user);

const userInitials = computed(() => {
  if (!user.value) return "U";
  return `${user.value.firstName?.[0] || ""}${user.value.lastName?.[0] || ""}`.toUpperCase();
});

const navLinks = computed(() => {
  let links = [];
  if (contentStore.header?.navLinks) {
    links = [...contentStore.header.navLinks];
  } else {
    links = [
      { name: "About", path: "/about" },
      { name: "Blog", path: "/blog" },
    ];
  }
  const hasPricing = links.some((l) => l.path === "/pricing");
  if (!hasPricing) {
    const aboutIdx = links.findIndex((l) => l.path === "/about");
    if (aboutIdx !== -1)
      links.splice(aboutIdx + 1, 0, { name: "Pricing", path: "/pricing" });
    else links.push({ name: "Pricing", path: "/pricing" });
  }
  return links;
});

function handleScroll() {
  const scrollY = window.scrollY;
  isScrolled.value = scrollY > 50;
  // Snap to fully reduced state once they scroll past 200px
  isReduced.value = scrollY > 200;
}

function toggleUserMenu() {
  showUserMenu.value = !showUserMenu.value;
}

async function handleLogout() {
  authStore.logout();
  showUserMenu.value = false;
  await router.push("/");
}

function handleClickOutside(event) {
  if (userMenuRef.value && !userMenuRef.value.contains(event.target)) {
    showUserMenu.value = false;
  }
}

// initScrollTrigger removed - we use pure CSS states for smoother exact-fit pill morphing

onMounted(() => {
  contentStore.fetchHeader();
  window.addEventListener("scroll", handleScroll, { passive: true });
  document.addEventListener("click", handleClickOutside);
  handleScroll();

  gsap.set(headerRef.value, { y: -120, opacity: 0 });

  function animateNavIn() {
    gsap.to(headerRef.value, {
      y: 0,
      opacity: 1,
      duration: 1.3,
      ease: "power3.out",
      delay: 0.25,
    });
  }

  if (pageLoaded.value) {
    animateNavIn();
  } else {
    const stop = watch(pageLoaded, (ready) => {
      if (ready) {
        animateNavIn();
        stop();
      }
    });
  }
});

onUnmounted(() => {
  window.removeEventListener("scroll", handleScroll);
  document.removeEventListener("click", handleClickOutside);
  if (typeof ScrollTrigger !== "undefined") {
    ScrollTrigger.getAll().forEach((t) => t.kill());
  }
});
</script>

<style scoped>
/* ─── Header shell ───────────────────────────────────────────────────────── */
.site-header {
  position: fixed;
  top: 1.25rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  height: 5rem;

  /* Baseline unreduced width */
  width: 90%;
  max-width: 1200px;

  /* ── Glassmorphism ── */
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(16px) saturate(140%);
  -webkit-backdrop-filter: blur(16px) saturate(140%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.35),
    inset 0 0 0 1px rgba(255, 255, 255, 0.06);

  /* Smooth CSS transition instead of JS scrub */
  transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
}

/* Reduced (scrolled) state — snaps to just the brand logo/text */
.site-header.is-reduced {
  width: 250px;
  max-width: 100%;
  border-radius: 1rem; /* same rectangular radius as main header */
  padding: 0;
  /* Slightly darker/less opaque when pinned */
  background: rgba(10, 10, 15, 0.2);
  border-color: rgba(255, 255, 255, 0.05);
}

/* ─── Nav inner ──────────────────────────────────────────────────────────── */
.site-nav {
  position: relative;
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 1rem;
}
.nav-spread {
  justify-content: space-between;
}
.nav-centered {
  justify-content: center;
}

/* ─── Brand ──────────────────────────────────────────────────────────────── */
.nav-brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.brand-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 700;
}
.brand-logo {
  width: 5rem;
  height: 3.125rem;
  object-fit: contain;
  display: block;
}
.brand-name {
  font-size: 1.875rem;
  color: #1a202c;
}

/* ─── Links ──────────────────────────────────────────────────────────────── */
.nav-links {
  display: flex;
  gap: 2rem;
  flex: 1;
  justify-content: center;
}

.nav-link {
  color: #1a202c;
  font-weight: 500;
  text-decoration: none;
  border-radius: 0.5rem;
  transition: color 0.3s;
  display: inline-flex;
  align-items: center;
}
.nav-link:hover,
.router-link-active.nav-link {
  color: #a78bfa;
}

/* ─── Scramble text span ──────────────────────────────────────────────────── */
/* Uses monospace during scramble so random chars don't shift layout */
span[v-scramble] {
  display: inline-block;
  font-variant-numeric: tabular-nums;
  /* Basic fix: min-width and text alignment */
  min-width: 1ch;
  letter-spacing: 0.02em;
}

/* ─── Right actions ──────────────────────────────────────────────────────── */
.nav-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.nav-actions-reduced {
  position: absolute;
  right: 2rem;
}

/* ─── Login link ─────────────────────────────────────────────────────────── */
.nav-auth {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.nav-auth-guest {
  display: flex;
  gap: 0.5rem;
}
.nav-login {
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-weight: 500;
  color: #a78bfa;
  text-decoration: none;
  transition: opacity 0.3s;
}
.nav-login:hover {
  opacity: 0.75;
}

/* ─── User section ───────────────────────────────────────────────────────── */
.nav-user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.user-menu-wrap {
  position: relative;
}

.user-avatar-btn {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background: linear-gradient(135deg, #673ee6, #22c55e);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition:
    transform 0.3s,
    box-shadow 0.3s;
}
.user-avatar-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 20px rgba(103, 62, 230, 0.3);
}

/* ─── Dropdown ───────────────────────────────────────────────────────────── */
.user-dropdown {
  position: absolute;
  top: 3.4375rem;
  right: 0;
  min-width: 12.5rem;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(103, 62, 230, 0.2);
  border-radius: 0.75rem;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  padding: 0.5rem;
  z-index: 1001;
}

.user-dropdown-info {
  padding: 0.75rem;
}
.user-name {
  font-weight: 600;
  color: #1a202c;
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
}
.user-role {
  font-size: 0.8rem;
  color: #6b7280;
}

.dropdown-divider {
  height: 1px;
  background: rgba(103, 62, 230, 0.1);
  margin: 0.5rem 0;
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 0.75rem;
  text-align: left;
  color: #374151;
  text-decoration: none;
  border-radius: 0.5rem;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 0.875rem;
  transition:
    background 0.2s,
    color 0.2s;
}
.dropdown-item:hover {
  background: rgba(103, 62, 230, 0.08);
  color: #673ee6;
}

.dropdown-item-danger {
  color: #ef4444;
}
.dropdown-item-danger:hover {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
}

/* ─── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .site-header {
    width: 95% !important;
  }
}
</style>
