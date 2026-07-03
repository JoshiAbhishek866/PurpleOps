<template>
  <div class="about-page">
    <DynamicSEO page="about" />
    <div class="container">
      <!-- Hero Section -->
      <section class="about-hero" data-testid="about-hero">
        <h1 class="heading-luxury">{{ aboutTitle }}</h1>
        <p class="hero-subtitle">
          {{ aboutDescription }}
        </p>
      </section>

      <!-- Mission Section -->
      <section class="mission-section glass" data-testid="mission-section">
        <h2 class="section-title">Our Mission</h2>
        <p class="mission-text">
          {{ missionText }}
        </p>
      </section>

      <!-- Vision Section -->
      <section class="vision-section glass" data-testid="vision-section">
        <h2 class="section-title">Our Vision</h2>
        <p class="vision-text">
          {{ visionText }}
        </p>
      </section>

      <!-- Company Info -->
      <section class="company-info" data-testid="company-info">
        <div class="info-grid">
          <div
            v-for="info in companyInfo"
            :key="info.title"
            class="info-card glass"
          >
            <h3 class="info-title">{{ info.title }}</h3>
            <p class="info-value">{{ info.value }}</p>
          </div>
        </div>
      </section>

      <!-- Values Section -->
      <section class="values-section" data-testid="values-section">
        <h2 class="section-title">Our Values</h2>
        <div class="values-grid">
          <div
            v-for="value in displayValues"
            :key="value.id"
            class="value-card glass"
            :data-testid="`value-${value.id}`"
          >
            <component :is="getValueIcon(value.icon)" class="value-icon" />
            <h3 class="value-title">{{ value.title }}</h3>
            <p class="value-description">{{ value.description }}</p>
          </div>
        </div>
      </section>

      <!-- Certifications -->
      <!-- <section class="certifications-section glass" data-testid="certifications-section">
        <h2 class="section-title">Certifications & Compliance</h2>
        <div class="certifications-grid">
          <div 
            v-for="cert in certifications" 
            :key="cert"
            class="certification-badge"
            :data-testid="`cert-${cert.replace(/\s+/g, '-').toLowerCase()}`"
          >
            {{ cert }}
          </div>
        </div>
      </section> -->
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useContentStore } from "@/stores/content";
import DynamicSEO from "@/components/DynamicSEO.vue";
import {
  ShieldCheckIcon,
  LightBulbIcon,
  EyeIcon,
  HeartIcon,
} from "@heroicons/vue/24/outline";

const contentStore = useContentStore();

// Dynamic content
const aboutTitle = computed(() => contentStore.about?.title || "About PurpleOps");
const aboutDescription = computed(
  () =>
    contentStore.about?.description ||
    "Protecting organizations with cutting-edge cybersecurity analytics and threat detection since 2020",
);
const missionText = computed(
  () =>
    contentStore.about?.mission ||
    "To empower organizations with advanced cybersecurity analytics that transform how they detect, respond to, and prevent cyber threats. We believe that proactive security should be accessible, intelligent, and automated.",
);

const visionText = computed(
  () =>
    contentStore.about?.vision ||
    "To empower organizations with advanced cybersecurity analytics that transform how they detect, respond to, and prevent cyber threats. We believe that proactive security should be accessible, intelligent, and automated.",
);

// Company info from content store with fallback
const companyInfo = computed(() => {
  if (contentStore.about?.companyInfo?.length) {
    return contentStore.about.companyInfo;
  }
  return [
    { title: "Founded", value: "2020" },
    { title: "Team Size", value: "50-100 employees" },
    { title: "Global Offices", value: "San Francisco, New York, London" },
  ];
});

// Icon mapping
const iconMap = {
  ShieldCheckIcon,
  LightBulbIcon,
  EyeIcon,
  HeartIcon,
};

function getValueIcon(iconName) {
  return iconMap[iconName] || ShieldCheckIcon;
}

const defaultValues = [
  {
    id: 1,
    icon: "ShieldCheckIcon",
    title: "Security First",
    description:
      "Everything we do is designed with security as the foundation, never as an afterthought.",
  },
  {
    id: 2,
    icon: "LightBulbIcon",
    title: "Innovation",
    description:
      "We continuously push the boundaries of what's possible in cybersecurity technology.",
  },
  {
    id: 3,
    icon: "EyeIcon",
    title: "Transparency",
    description:
      "Clear communication and honest practices build trust with our clients and partners.",
  },
  {
    id: 4,
    icon: "HeartIcon",
    title: "Customer Success",
    description:
      "Our success is measured by the security and peace of mind we provide our clients.",
  },
];

// Values from content store with fallback
const displayValues = computed(() => {
  if (contentStore.about?.values?.length) {
    return contentStore.about.values;
  }
  return defaultValues;
});

const values = defaultValues; // Keep for backward compatibility

const certifications = [
  "SOC 2 Type II",
  "ISO 27001",
  "GDPR Compliant",
  "CCPA Compliant",
];

onMounted(() => {
  contentStore.fetchAbout();
});
</script>

<style scoped>
.about-page {
  @apply py-20;
  min-height: 100vh;
}

.container {
  @apply max-w-6xl mx-auto px-6 space-y-20;
}

/* Hero Section */
.about-hero {
  @apply text-center py-16;
}

.hero-subtitle {
  @apply text-2xl text-gray-600 mt-6 max-w-3xl mx-auto leading-relaxed;
}

/* Mission Section */
.mission-section {
  @apply p-12 text-center rounded-2xl mt-12;
  margin-top: 8rem !important;
}

.mission-text {
  @apply text-lg text-gray-700 leading-relaxed max-w-4xl mx-auto mt-6;
}

/* Vision Section */
.vision-section {
  @apply p-12 text-center rounded-2xl mt-12;
  margin-top: 8rem !important;
}

.vision-text {
  @apply text-lg text-gray-700 leading-relaxed max-w-4xl mx-auto mt-6;
}

/* Company Info */
.info-grid {
  @apply grid grid-cols-1 md:grid-cols-3 gap-6;
}

.info-card {
  @apply p-8 text-center rounded-xl;
}

.info-title {
  @apply text-lg font-semibold text-gray-600 mb-2;
}

.info-value {
  @apply text-2xl font-bold;
}

/* Values Section */
.values-grid {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-12;
}

.value-card {
  @apply p-8 text-center rounded-xl transition-all duration-300 hover:scale-105;
}

.value-icon {
  @apply w-12 h-12 mx-auto mb-4 p-2 rounded-lg;
}

.value-title {
  @apply text-xl font-bold mb-4;
  color: #1a202c;
}

.value-description {
  @apply text-gray-600 leading-relaxed;
}

/* Certifications */
.certifications-section {
  @apply p-12 text-center rounded-2xl;
}

.certifications-grid {
  @apply grid grid-cols-2 md:grid-cols-4 gap-4 mt-8;
}

.certification-badge {
  @apply px-4 py-3 rounded-lg font-semibold text-center;
  background: linear-gradient(
    135deg,
    rgba(139, 92, 246, 0.1),
    rgba(16, 185, 129, 0.1)
  );
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: #8b5cf6;
}

/* Common Styles */
.section-title {
  @apply text-3xl font-bold text-center;
  color: #1a202c;
}

/* Responsive Design */
@media (max-width: 768px) {
  .values-grid {
    @apply grid-cols-1 gap-4;
  }

  .certifications-grid {
    @apply grid-cols-1 gap-3;
  }
}
</style>
