<template>
  <!-- This component doesn't render anything, just sets meta tags dynamically -->
</template>

<script setup>
import { useHead } from "@vueuse/head";
import { computed, watch, onMounted } from "vue";
import { useSEOStore } from "@/stores/seo";
import { useRoute } from "vue-router";

const props = defineProps({
  page: {
    type: String,
    required: true, // e.g., 'home', 'about', 'blog', 'dashboard'
  },
  // Optional overrides - if not provided, will use dynamic data from admin
  title: {
    type: String,
    default: null,
  },
  description: {
    type: String,
    default: null,
  },
  image: {
    type: String,
    default: null,
  },
  url: {
    type: String,
    default: null,
  },
  type: {
    type: String,
    default: null,
  },
  keywords: {
    type: String,
    default: null,
  },
});

const seoStore = useSEOStore();
const route = useRoute();

// Fetch dynamic SEO data on mount
onMounted(async () => {
  await seoStore.fetchGlobalSEO();
  await seoStore.fetchPageSEO(props.page);
});

// Watch for page changes
watch(
  () => props.page,
  async (newPage) => {
    await seoStore.fetchPageSEO(newPage);
  },
);

// Get page SEO data
const pageSEO = computed(() => seoStore.pageSEO[props.page] || {});
const globalSEO = computed(() => seoStore.globalSEO || {});

// Computed SEO values (priority: props > dynamic data > defaults)
const seoTitle = computed(() => {
  return (
    props.title ||
    pageSEO.value.seo?.title ||
    "PurpleOps - Advanced Cybersecurity Platform"
  );
});

const seoDescription = computed(() => {
  return (
    props.description ||
    pageSEO.value.seo?.description ||
    "Protect your organization with PurpleOps's comprehensive cybersecurity solutions."
  );
});

const seoKeywords = computed(() => {
  return (
    props.keywords ||
    pageSEO.value.seo?.keywords ||
    "cybersecurity, security platform, threat detection"
  );
});

const seoImage = computed(() => {
  return (
    props.image ||
    pageSEO.value.seo?.ogImage ||
    globalSEO.value.defaultOgImage ||
    "/logo1.png"
  );
});

const seoUrl = computed(() => {
  if (props.url) return props.url;
  const baseUrl = globalSEO.value.siteUrl || "https://PurpleOps.com";
  return pageSEO.value.seo?.canonical || `${baseUrl}${route.fullPath}`;
});

const seoType = computed(() => {
  return props.type || pageSEO.value.seo?.ogType || "website";
});

const seoRobots = computed(() => {
  return pageSEO.value.seo?.robots || "index, follow";
});

const seoAuthor = computed(() => {
  return (
    pageSEO.value.seo?.author || globalSEO.value.defaultAuthor || "PurpleOps Team"
  );
});

const twitterCard = computed(() => {
  return pageSEO.value.seo?.twitterCard || "summary_large_image";
});

const twitterSite = computed(() => {
  return (
    pageSEO.value.seo?.twitterSite || globalSEO.value.twitterSite || "@PurpleOps"
  );
});

const siteName = computed(() => {
  return globalSEO.value.siteName || "PurpleOps";
});

const themeColor = computed(() => {
  return globalSEO.value.themeColor || "#8b5cf6";
});

// Full title with site name
const fullTitle = computed(() => `${seoTitle.value} | ${siteName.value}`);

// Use useHead to set all meta tags
useHead(() => ({
  title: fullTitle.value,
  meta: [
    // Basic SEO
    { name: "description", content: seoDescription.value },
    { name: "keywords", content: seoKeywords.value },
    { name: "author", content: seoAuthor.value },
    { name: "robots", content: seoRobots.value },

    // Open Graph (Facebook, LinkedIn)
    { property: "og:title", content: fullTitle.value },
    { property: "og:description", content: seoDescription.value },
    { property: "og:image", content: seoImage.value },
    { property: "og:url", content: seoUrl.value },
    { property: "og:type", content: seoType.value },
    { property: "og:site_name", content: siteName.value },

    // Twitter Card
    { name: "twitter:card", content: twitterCard.value },
    { name: "twitter:title", content: fullTitle.value },
    { name: "twitter:description", content: seoDescription.value },
    { name: "twitter:image", content: seoImage.value },
    { name: "twitter:site", content: twitterSite.value },

    // Additional
    { name: "theme-color", content: themeColor.value },
    { name: "msapplication-TileColor", content: themeColor.value },
  ],
  link: [{ rel: "canonical", href: seoUrl.value }],
}));
</script>
