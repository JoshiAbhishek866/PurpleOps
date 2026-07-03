<template>
  <!-- This component doesn't render anything, just sets meta tags for admin -->
</template>

<script setup>
import { useHead } from '@vueuse/head'
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: 'PurpleOps Admin Panel - Manage your security platform',
  },
})

// Full title with admin prefix
const fullTitle = computed(() => `${props.title} | PurpleOps Admin`)

useHead({
  title: fullTitle.value,
  meta: [
    // Prevent indexing - admin panel should NOT be in search results
    { name: 'robots', content: 'noindex, nofollow' },
    { name: 'googlebot', content: 'noindex, nofollow' },

    // Basic meta
    { name: 'description', content: props.description },
    { name: 'author', content: 'PurpleOps Team' },

    // Security headers
    { 'http-equiv': 'X-UA-Compatible', content: 'IE=edge' },
    { name: 'referrer', content: 'strict-origin-when-cross-origin' },

    // Theme
    { name: 'theme-color', content: '#8b5cf6' },
    { name: 'msapplication-TileColor', content: '#8b5cf6' },
  ],
})
</script>
