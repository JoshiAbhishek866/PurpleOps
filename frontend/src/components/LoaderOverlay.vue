<template>
  <div class="loader-overlay" role="status" aria-live="polite">
    <div class="spinner"></div>
    <div class="loader-text">Loading...</div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.loader-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(2px);
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(255, 255, 255, 0.15);
  border-top-color: #00b090;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

.loader-text {
  margin-left: 16px;
  color: #e5e7eb;
  font-weight: 600;
  letter-spacing: 0.02em;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

