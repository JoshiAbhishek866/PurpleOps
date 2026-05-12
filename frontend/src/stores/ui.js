import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const isLoading = ref(false)

  function startLoading() {
    isLoading.value = true
  }

  function stopLoading() {
    isLoading.value = false
  }

  return {
    isLoading,
    startLoading,
    stopLoading
  }
})

