<template>
  <!-- Outer shell gives the page a light grey underlay so the card "floats" -->
  <footer class="footer-shell">
    <div class="footer-card">
      <!-- ── Top Row: Logo col + link columns + newsletter ── -->
      <div class="footer-top">
        <!-- Brand column -->
        <div class="footer-brand">
          <div class="footer-logo">
            <img src="/logo1.png" alt="PurpleOps" class="logo-img" />
            <span class="logo-name">PurpleOps</span>
          </div>
          <p class="footer-tagline">
            Advanced cybersecurity analytics and threat-detection platform
            designed for modern organisations. Protecting your digital assets
            with AI-powered security solutions.
          </p>
        </div>

        <!-- Dynamic link columns -->
        <div
          v-for="section in footerSections"
          :key="section.title"
          class="footer-col"
        >
          <h4 class="col-heading">{{ section.title }}</h4>
          <ul class="col-links">
            <li v-for="link in section.links" :key="link.name">
              <router-link
                v-if="link.path.startsWith('/')"
                :to="link.path"
                class="col-link"
                >{{ link.name }}</router-link
              >
              <a v-else :href="link.path" class="col-link">{{ link.name }}</a>
            </li>
          </ul>
        </div>

        <!-- Newsletter column -->
        <div class="footer-col newsletter-col">
          <h4 class="col-heading">Newsletter</h4>
          <p class="newsletter-copy">
            Get the latest security insights, threat reports and product updates
            delivered to your inbox.
          </p>
          <form class="newsletter-form" @submit.prevent>
            <input
              type="email"
              placeholder="your@email.com"
              class="newsletter-input"
            />
            <button type="submit" class="newsletter-btn" aria-label="Subscribe">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                class="btn-arrow"
              >
                <path
                  fill-rule="evenodd"
                  d="M3 10a.75.75 0 01.75-.75h10.638L10.23 5.29a.75.75 0 111.04-1.08l5.5 5.25a.75.75 0 010 1.08l-5.5 5.25a.75.75 0 11-1.04-1.08l4.158-3.96H3.75A.75.75 0 013 10z"
                  clip-rule="evenodd"
                />
              </svg>
            </button>
          </form>
        </div>
      </div>

      <!-- ── Divider ── -->
      <div class="footer-divider" />

      <!-- ── Bottom Row: socials left, badges right ── -->
      <div class="footer-bottom">
        <div class="social-row">
          <a
            href="#"
            class="social-btn"
            aria-label="LinkedIn"
            data-testid="linkedin-link"
          >
            <svg class="social-icon" fill="currentColor" viewBox="0 0 24 24">
              <path
                d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"
              />
            </svg>
          </a>
          <a
            href="#"
            class="social-btn"
            aria-label="Twitter / X"
            data-testid="twitter-link"
          >
            <svg class="social-icon" fill="currentColor" viewBox="0 0 24 24">
              <path
                d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"
              />
            </svg>
          </a>
          <a
            href="#"
            class="social-btn"
            aria-label="GitHub"
            data-testid="github-link"
          >
            <svg class="social-icon" fill="currentColor" viewBox="0 0 24 24">
              <path
                d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"
              />
            </svg>
          </a>
        </div>

        <!-- Security badges (right side) -->
        <div class="badges-row">
          <div class="badge" v-for="b in badges" :key="b.title">
            <component :is="b.icon" class="badge-icon" />
            <div class="badge-text">
              <span class="badge-title">{{ b.title }}</span>
              <span class="badge-sub">{{ b.sub }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Copyright bar ── -->
      <div class="footer-copy">
        <span>© {{ currentYear }} PurpleOps. All rights reserved.</span>
        <div class="legal-links">
          <a href="#" class="legal-link">Privacy Policy</a>
          <span class="sep">·</span>
          <a href="#" class="legal-link">Terms of Service</a>
          <span class="sep">·</span>
          <a href="#" class="legal-link">Cookie Policy</a>
          <span class="sep">·</span>
          <a href="#" class="legal-link">Security</a>
        </div>
      </div>
    </div>
    <!-- /footer-card -->
  </footer>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useContentStore } from "@/stores/content";
import {
  ShieldCheckIcon,
  LockClosedIcon,
  EyeIcon,
  KeyIcon,
} from "@heroicons/vue/24/outline";

const contentStore = useContentStore();
const currentYear = computed(() => new Date().getFullYear());

const badges = [
  { icon: ShieldCheckIcon, title: "SOC 2 Type II", sub: "Certified" },
  { icon: LockClosedIcon, title: "ISO 27001", sub: "Compliant" },
  { icon: EyeIcon, title: "GDPR", sub: "Ready" },
  { icon: KeyIcon, title: "256-bit", sub: "Encryption" },
];

const footerSections = computed(() => {
  if (contentStore.footer?.sections) return contentStore.footer.sections;
  return [
    {
      title: "Product",
      links: [
        { name: "Features", path: "/" },
        { name: "Security", path: "/about" },
        { name: "Integrations", path: "#" },
        { name: "Pricing", path: "#" },
        { name: "API", path: "#" },
      ],
    },
    {
      title: "Solutions",
      links: [
        { name: "Enterprise", path: "#" },
        { name: "Small Business", path: "#" },
        { name: "Government", path: "#" },
        { name: "Healthcare", path: "#" },
        { name: "Finance", path: "#" },
      ],
    },
    {
      title: "Resources",
      links: [
        { name: "Blog", path: "/blog" },
        { name: "Documentation", path: "#" },
        { name: "Help Center", path: "#" },
        { name: "Case Studies", path: "#" },
        { name: "Webinars", path: "#" },
      ],
    },
    {
      title: "Company",
      links: [
        { name: "About Us", path: "/about" },
        { name: "Careers", path: "#" },
        { name: "News", path: "#" },
        { name: "Contact", path: "#" },
        { name: "Partners", path: "#" },
      ],
    },
  ];
});

onMounted(() => contentStore.fetchFooter());
</script>

<style scoped>
/* ── Page shell ─────────────────────────────────────────────────────────────── */
.footer-shell {
  background: transparent;
  padding: 2.5rem 1.5rem 2.5rem; /* equal top & bottom so card floats */
}

/* ── The card itself ────────────────────────────────────────────────────────── */
.footer-card {
  max-width: 1320px;
  margin: 0 auto;
  background: #ffffff;
  border-radius: 1.75rem; /* all four corners rounded */
  padding: 4rem 4rem 2rem;
  box-shadow: 0 8px 48px rgba(0, 0, 0, 0.08);
}

/* ── Top section grid ───────────────────────────────────────────────────────── */
.footer-top {
  display: grid;
  grid-template-columns: 1.8fr repeat(4, 1fr) 1.8fr;
  gap: 2.5rem;
  padding-bottom: 2.5rem;
}

/* ── Brand column ───────────────────────────────────────────────────────────── */
.footer-brand {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.footer-logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.logo-img {
  width: 48px;
  height: 30px;
  object-fit: contain;
}

.logo-name {
  font-family: var(--font-heading);
  font-size: 0.75rem;
  font-weight: 400;
  color: #1a202c;
  letter-spacing: 0.04em;
}

.footer-tagline {
  font-family: var(--font-body);
  font-size: 0.85rem;
  color: #673ee6; /* brand purple for emphasis text */
  line-height: 1.7;
  max-width: 22ch;
}

/* ── Link columns ───────────────────────────────────────────────────────────── */
.footer-col {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.col-heading {
  font-family: var(--font-body) !important; /* use Ubuntu for column labels */
  font-size: 0.7rem !important;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6b7280;
}

.col-links {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.col-link {
  font-family: var(--font-body);
  font-size: 0.9rem;
  color: #374151;
  text-decoration: none;
  transition: color 0.2s ease;
}

.col-link:hover {
  color: #673ee6;
}

/* ── Newsletter column ──────────────────────────────────────────────────────── */
.newsletter-copy {
  font-family: var(--font-body);
  font-size: 0.85rem;
  color: #4b5563;
  line-height: 1.65;
}

.newsletter-form {
  display: flex;
  align-items: center;
  border: 1px solid #d1d5db;
  border-radius: 0.6rem;
  overflow: hidden;
  background: #ffffff;
  margin-top: 0.5rem;
}

.newsletter-input {
  flex: 1;
  border: none;
  outline: none;
  padding: 0.65rem 0.9rem;
  font-family: var(--font-body);
  font-size: 0.85rem;
  background: transparent;
  color: #1a202c;
}

.newsletter-input::placeholder {
  color: #9ca3af;
}

.newsletter-btn {
  background: #1a202c;
  border: none;
  cursor: pointer;
  padding: 0.65rem 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease;
}

.newsletter-btn:hover {
  background: #673ee6;
}

.btn-arrow {
  width: 1rem;
  height: 1rem;
  color: #ffffff;
}

/* ── Divider ────────────────────────────────────────────────────────────────── */
.footer-divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.1);
  margin: 0 -0.5rem;
}

/* ── Bottom row ─────────────────────────────────────────────────────────────── */
.footer-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2rem 0;
  flex-wrap: wrap;
  gap: 1.5rem;
}

/* Socials */
.social-row {
  display: flex;
  gap: 0.75rem;
}

.social-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.4rem;
  height: 2.4rem;
  border-radius: 50%;
  border: 1px solid #d1d5db;
  color: #4b5563;
  text-decoration: none;
  transition: all 0.2s ease;
}

.social-btn:hover {
  border-color: #673ee6;
  color: #673ee6;
  background: rgba(103, 62, 230, 0.06);
  transform: translateY(-2px);
}

.social-icon {
  width: 1rem;
  height: 1rem;
}

/* Badges */
.badges-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.85rem;
  border-radius: 0.6rem;
  border: 1px solid rgba(103, 62, 230, 0.15);
  background: rgba(103, 62, 230, 0.05);
}

.badge-icon {
  width: 1.15rem;
  height: 1.15rem;
  color: #673ee6;
}

.badge-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.badge-title {
  font-family: var(--font-body);
  font-size: 0.7rem;
  font-weight: 700;
  color: #1a202c;
}

.badge-sub {
  font-family: var(--font-body);
  font-size: 0.6rem;
  color: #6b7280;
}

/* ── Copyright bar ──────────────────────────────────────────────────────────── */
.footer-copy {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 0;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  font-family: var(--font-body);
  font-size: 0.78rem;
  color: #9ca3af;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.legal-links {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.legal-link {
  color: #9ca3af;
  text-decoration: none;
  transition: color 0.2s ease;
}

.legal-link:hover {
  color: #673ee6;
}

.sep {
  color: #d1d5db;
}

/* ── Responsive ─────────────────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .footer-top {
    grid-template-columns: 1fr 1fr 1fr;
  }
  .newsletter-col {
    grid-column: span 3;
  }
}

@media (max-width: 640px) {
  .footer-card {
    padding: 2.5rem 1.5rem 0;
    border-radius: 1rem 1rem 0 0;
  }
  .footer-top {
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
  }
  .footer-brand {
    grid-column: span 2;
  }
  .newsletter-col {
    grid-column: span 2;
  }
  .footer-bottom {
    flex-direction: column;
    align-items: flex-start;
  }
  .footer-copy {
    flex-direction: column;
    align-items: flex-start;
  }
  .badges-row {
    gap: 0.5rem;
  }
}
</style>
