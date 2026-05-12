<template>
  <div class="dashboard-layout">
    <DynamicSEO page="dashboard" />
    <!-- App Sidebar -->
    <Sidebar />

    <!-- Main Content Area -->
    <main class="main-content">
      <div class="content-wrapper">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import Sidebar from "@/components/ui/Sidebar.vue";
import DynamicSEO from "@/components/DynamicSEO.vue";
</script>

<style scoped>
.dashboard-layout {
  @apply min-h-screen flex;
  background: #f8f9fa;
}

.dark .dashboard-layout {
  background: #000000;
}

.main-content {
  @apply flex-1 ml-[260px] transition-all duration-300;
  min-height: 100vh;
}

.content-wrapper {
  @apply p-6;
}

/* Responsive */
@media (max-width: 1024px) {
  .main-content {
    @apply ml-[70px];
  }
}
</style>
