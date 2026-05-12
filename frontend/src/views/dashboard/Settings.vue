<template>
  <div class="settings-page">
    <h1 class="page-title" data-testid="settings-title">{{ pageTitle }}</h1>
    <p class="page-subtitle">{{ pageDescription }}</p>
    
    <div class="settings-content">
      <!-- Placeholder for Settings -->
      <div class="placeholder-content glass">
        <h2>Dashboard Settings</h2>
        <p>{{ contentText }}</p>
        <div class="mt-6 space-y-3">
          <div v-if="allowCustomization" class="setting-item">
            <span class="setting-icon">✓</span>
            <span>User Customization Enabled</span>
          </div>
          <div v-if="enableNotifications" class="setting-item">
            <span class="setting-icon">🔔</span>
            <span>Notifications Enabled</span>
          </div>
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
  return contentStore.clientDashboard?.settings?.title || 'Dashboard Settings'
})

const pageDescription = computed(() => {
  return contentStore.clientDashboard?.settings?.description || 'Configure your dashboard preferences and settings'
})

const contentText = computed(() => {
  return contentStore.clientDashboard?.settings?.contentText || 'This section will allow you to customize your dashboard experience and manage preferences.'
})

const allowCustomization = computed(() => {
  return contentStore.clientDashboard?.settings?.allowCustomization !== false
})

const enableNotifications = computed(() => {
  return contentStore.clientDashboard?.settings?.enableNotifications !== false
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
.settings-page {
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
  @apply text-gray-600 mb-4;
}

.dark .placeholder-content p {
  @apply text-gray-400;
}

.setting-item {
  @apply flex items-center gap-3 text-left justify-center;
  color: #1a202c;
}

.dark .setting-item {
  color: #f7fafc;
}

.setting-icon {
  @apply text-xl;
}
</style>