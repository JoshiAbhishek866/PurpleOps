<template>
  <Card :variant="variant" :hover="hover" class="widget-card">
    <template #header>
      <div class="widget-header">
        <div class="widget-left">
          <component :is="icon" v-if="icon" class="widget-icon" />
          <div class="widget-texts">
            <div class="widget-title">{{ title }}</div>
            <div v-if="subtitle" class="widget-subtitle">{{ subtitle }}</div>
          </div>
        </div>
        <div class="widget-right">
          <div class="widget-value">{{ formattedValue }}</div>
          <div v-if="trend" class="widget-trend" :class="trendClass">{{ trendText }}</div>
        </div>
      </div>
    </template>

    <div class="widget-body">
      <slot />
    </div>

    <template #footer>
      <slot name="footer" />
    </template>
  </Card>
</template>

<script setup>
import Card from '@/components/ui/Card.vue'
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  value: { type: [String, Number], default: 0 },
  icon: { type: [Object, Function], default: null },
  variant: { type: String, default: 'default' },
  hover: { type: Boolean, default: false },
  trend: { type: Number, default: null },
  format: { type: String, default: null }
})

const formattedValue = computed(() => {
  if (props.format === 'percentage') return `${props.value}%`
  if (typeof props.value === 'number') return props.value.toLocaleString()
  return props.value
})

const trendClass = computed(() => (props.trend >= 0 ? 'text-red-500' : 'text-green-500'))
const trendText = computed(() => (props.trend != null ? `${props.trend}%` : ''))
</script>

<style scoped>
.widget-card {
  /* small adjustments for widget layout */
}

.widget-header {
  @apply flex items-center justify-between gap-2;
}

.widget-left {
  @apply flex items-center gap-3;
}

.widget-icon {
  @apply w-10 h-10 rounded-lg flex items-center justify-center text-white bg-gradient-to-br from-purple-500 to-green-500;
}

.widget-texts {
  @apply flex flex-col;
}

.widget-title {
  @apply text-sm font-semibold text-gray-900 dark:text-white;
}

.widget-subtitle {
  @apply text-xs text-gray-500 dark:text-gray-400;
}

.widget-right {
  @apply flex flex-col items-end;
}

.widget-value {
  @apply text-2xl font-bold text-gray-900 dark:text-white;
}

.widget-trend {
  @apply text-sm font-medium;
}

.widget-body {
  @apply p-2;
}
</style>