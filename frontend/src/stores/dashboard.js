import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const backendBaseUrl = 'http://localhost:8000/api' // (import.meta.env.VITE_API_URL || 'http://localhost:8001/api').replace(/\/$/, '')
const API_BASE = backendBaseUrl

export const useDashboardStore = defineStore('dashboard', () => {
  const overview = ref({})
  const attackInsights = ref({})
  const defenseMetrics = ref({})
  const activityLogs = ref([])
  const systemHealth = ref({})
  const isLoading = ref(false)
  const error = ref(null)

  async function fetchOverview() {
    isLoading.value = true
    try {
      const response = await axios.get(`${API_BASE}/dashboard/overview`)
      overview.value = response.data.overview
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch overview'
      console.error('Overview fetch error:', err)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchAttackInsights(period = '7d') {
    try {
      const response = await axios.get(`${API_BASE}/dashboard/attack-insights?period=${period}`)
      attackInsights.value = response.data.attackInsights
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch attack insights'
      console.error('Attack insights error:', err)
    }
  }

  async function fetchDefenseMetrics() {
    try {
      const response = await axios.get(`${API_BASE}/dashboard/defense-metrics`)
      defenseMetrics.value = response.data.defenseMetrics
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch defense metrics'
      console.error('Defense metrics error:', err)
    }
  }

  async function fetchActivityLogs(options = {}) {
    try {
      const params = new URLSearchParams(options).toString()
      const response = await axios.get(`${API_BASE}/dashboard/activity-logs?${params}`)
      activityLogs.value = response.data.activityLogs
      return response.data.pagination
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch activity logs'
      console.error('Activity logs error:', err)
    }
  }

  async function fetchSystemHealth() {
    try {
      const response = await axios.get(`${API_BASE}/dashboard/system-health`)
      systemHealth.value = response.data.systemHealth
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch system health'
      console.error('System health error:', err)
    }
  }

  async function exportLogs(format = 'json', filters = {}) {
    try {
      const params = new URLSearchParams({ format, ...filters }).toString()
      const response = await axios.get(`${API_BASE}/dashboard/export-logs?${params}`, {
        responseType: 'blob'
      })

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `security-logs.${format}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to export logs'
      console.error('Export logs error:', err)
    }
  }

  // Real-time data simulation
  function startRealTimeUpdates() {
    // Update overview every 30 seconds
    setInterval(fetchOverview, 30000)

    // Update system health every 60 seconds  
    setInterval(fetchSystemHealth, 60000)
  }

  return {
    overview,
    attackInsights,
    defenseMetrics,
    activityLogs,
    systemHealth,
    isLoading,
    error,
    fetchOverview,
    fetchAttackInsights,
    fetchDefenseMetrics,
    fetchActivityLogs,
    fetchSystemHealth,
    exportLogs,
    startRealTimeUpdates
  }
})