<template>
  <div class="ui-table-wrapper">
    <Card>
      <div class="overflow-x-auto">
        <table class="ui-table">
          <thead>
            <tr>
              <th v-for="(h, idx) in headers" :key="idx">{{ h }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, rIdx) in rows" :key="rIdx" class="row-hover">
              <td v-for="(col, cIdx) in row" :key="cIdx">{{ col }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>
  </div>
</template>

<script setup>
import Card from '@/components/ui/Card.vue'
const props = defineProps({
  headers: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] }
})
</script>

<style scoped>
.ui-table-wrapper {
  @apply w-full;
}

.ui-table {
  @apply w-full text-sm;
}

.ui-table thead {
  @apply bg-gray-50 dark:bg-gray-800;
}

.ui-table th {
  @apply text-left px-4 py-2 font-medium text-xs text-gray-500 dark:text-gray-400;
}

.ui-table td {
  @apply px-4 py-3;
}

.ui-table tbody tr.row-hover:hover {
  @apply bg-gray-50 dark:bg-gray-900/40;
}
</style>