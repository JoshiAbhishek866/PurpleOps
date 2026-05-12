import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(false)

  function toggleTheme() {
    isDark.value = !isDark.value
    updateDOM()
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  }

  function initializeTheme() {
    const saved = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    
    isDark.value = saved ? saved === 'dark' : prefersDark
    updateDOM()
  }

  function updateDOM() {
    if (isDark.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  return {
    isDark,
    toggleTheme,
    initializeTheme
  }
})