<template>
  <div
    class="ui-card"
    :class="[
      `card-${variant}`,
      { 'card-hover': hover },
      { 'card-clickable': clickable },
    ]"
    @click="handleClick"
  >
    <div v-if="$slots.header || title" class="card-header">
      <div v-if="title" class="card-title">
        <component v-if="icon" :is="icon" class="card-title-icon" />
        <span>{{ title }}</span>
      </div>
      <div v-if="$slots.header" class="card-header-content">
        <slot name="header" />
      </div>
    </div>

    <div class="card-body">
      <slot />
    </div>

    <div v-if="$slots.footer" class="card-footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  title: {
    type: String,
    default: "",
  },
  icon: {
    type: Object,
    default: null,
  },
  variant: {
    type: String,
    default: "default",
    validator: (value) =>
      ["default", "primary", "success", "warning", "danger"].includes(value),
  },
  hover: {
    type: Boolean,
    default: false,
  },
  clickable: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["click"]);

function handleClick() {
  if (props.clickable) {
    emit("click");
  }
}
</script>

<style scoped>
.ui-card {
  @apply bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700;
  @apply shadow-sm transition-all duration-200;
}

.card-primary {
  @apply border-purple-500 dark:border-purple-400;
}

.card-success {
  @apply border-green-500 dark:border-green-400;
}

.card-warning {
  @apply border-yellow-500 dark:border-yellow-400;
}

.card-danger {
  @apply border-red-500 dark:border-red-400;
}

.card-hover:hover {
  @apply shadow-md transform -translate-y-0.5;
}

.card-clickable {
  @apply cursor-pointer;
}

.card-header {
  @apply px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between;
}

.card-title {
  @apply flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white;
}

.card-title-icon {
  @apply w-5 h-5 text-purple-600 dark:text-purple-400;
}

.card-header-content {
  @apply flex items-center gap-2;
}

.card-body {
  @apply px-6 py-4;
}

.card-footer {
  @apply px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 rounded-b-lg;
}
</style>
