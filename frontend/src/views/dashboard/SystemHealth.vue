<template>
  <div class="system-health-page">
    <h1 class="page-title" data-testid="system-health-title">{{ pageTitle }}</h1>
    <p class="page-subtitle">{{ pageDescription }}</p>
    
    <div class="health-content">
      <!-- Placeholder for System Health -->
      <div class="placeholder-content glass">
        <h2>System Health Dashboard</h2>
        <p>{{ contentText }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useContentStore } from '@/stores/content'

const contentStore = useContentStore()

const pageTitle = computed(() => {
  return contentStore.clientDashboard?.systemHealth?.title || 'System Health'
})

const pageDescription = computed(() => {
  return contentStore.clientDashboard?.systemHealth?.description || 'Monitor system performance and health metrics'
})

const contentText = computed(() => {
  return contentStore.clientDashboard?.systemHealth?.contentText || 'This section will show system performance, server health, and resource usage metrics.'
})

onMounted(async () => {
  try {
    await contentStore.fetchClientDashboard()
  } catch (error) {
    console.warn('Could not load client dashboard content, using defaults:', error)
  }
})
</script>

<style scoped>
.system-health-page {
  @apply space-y-8;
}

.page-title {
  @apply text-3xl font-bold;
  color: #1a202c;
}

.dark .page-title {
  color: #f7fafc;
}

.page-subtitle {
  @apply text-gray-600;
}

.dark .page-subtitle {
  @apply text-gray-400;
}

.placeholder-content {
  @apply p-12 text-center rounded-xl;
}

.placeholder-content h2 {
  @apply text-2xl font-bold mb-4;
  color: #1a202c;
}

.dark .placeholder-content h2 {
  color: #f7fafc;
}

.placeholder-content p {
  @apply text-gray-600;
}

.dark .placeholder-content p {
  @apply text-gray-400;
}
</style>