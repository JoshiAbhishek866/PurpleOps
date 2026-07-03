<template>
  <!-- This component doesn't render anything, just sets meta tags -->
</template>

<script setup>
import { useHead } from "@vueuse/head";
import { computed } from "vue";

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
  image: {
    type: String,
    default: "https://PurpleOps.com/og-image.jpg",
  },
  url: {
    type: String,
    default: "https://PurpleOps.com",
  },
  type: {
    type: String,
    default: "website",
  },
  keywords: {
    type: String,
    default:
      "cybersecurity, AI security, threat detection, vulnerability scanning",
  },
});

// Full title with site name
const fullTitle = computed(() => `${props.title} | PurpleOps`);

useHead({
  title: fullTitle.value,
  meta: [
    // Basic SEO
    { name: "description", content: props.description },
    { name: "keywords", content: props.keywords },
    { name: "author", content: "PurpleOps Team" },
    { name: "robots", content: "index, follow" },

    // Open Graph (Facebook, LinkedIn)
    { property: "og:title", content: fullTitle.value },
    { property: "og:description", content: props.description },
    { property: "og:image", content: props.image },
    { property: "og:url", content: props.url },
    { property: "og:type", content: props.type },
    { property: "og:site_name", content: "PurpleOps" },

    // Twitter Card
    { name: "twitter:card", content: "summary_large_image" },
    { name: "twitter:title", content: fullTitle.value },
    { name: "twitter:description", content: props.description },
    { name: "twitter:image", content: props.image },
    { name: "twitter:site", content: "@PurpleOps" },

    // Additional
    { name: "theme-color", content: "#8b5cf6" },
    { name: "msapplication-TileColor", content: "#8b5cf6" },
  ],
  link: [{ rel: "canonical", href: props.url }],
});
</script>
