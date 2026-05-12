<template>
  <div class="activity-logs-page">
    <h1 class="page-title" data-testid="activity-logs-title">{{ pageTitle }}</h1>
    <p class="page-subtitle">{{ pageDescription }}</p>
    
    <div class="logs-content">
      <!-- Placeholder for Activity Logs -->
      <div class="placeholder-content glass">
        <h2>Activity Logs Dashboard</h2>
        <p>{{ contentText }}</p>
        <div v-if="retentionDays" class="mt-4 text-sm text-gray-500">
          Log Retention: {{ retentionDays }} days
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useContentStore } from '@/stores/content'

const contentStore = useContentStore()

const pageTitle = computed(() => {
  return contentStore.clientDashboard?.activityLogs?.title || 'Activity Logs'
})

const pageDescription = computed(() => {
  return contentStore.clientDashboard?.activityLogs?.description || 'View and analyze security activity logs'
})

const contentText = computed(() => {
  return contentStore.clientDashboard?.activityLogs?.contentText || 'This section will show detailed activity logs, security events, and audit trails.'
})

const retentionDays = computed(() => {
  return contentStore.clientDashboard?.activityLogs?.retentionDays || 30
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
.activity-logs-page {
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