import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE = 'http://localhost:8000' // import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

export const useAdminAuthStore = defineStore('adminAuth', () => {
  const admin = ref(JSON.parse(localStorage.getItem('admin') || 'null'))
  const token = ref(localStorage.getItem('adminToken'))
  const isLoading = ref(false)
  const error = ref(null)

  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  const isAuthenticated = computed(() => !!token.value && !!admin.value)
  const fullName = computed(() => admin.value ? `${admin.value.firstName} ${admin.value.lastName}` : '')

  async function login(credentials) {
    isLoading.value = true
    error.value = null
    try {
      const response = await axios.post(`${API_BASE}/api/admin/auth/login`, credentials)
      const { token: newToken, admin: adminData } = response.data
      token.value = newToken
      admin.value = adminData
      localStorage.setItem('adminToken', newToken)
      localStorage.setItem('admin', JSON.stringify(adminData))
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
      return { success: true }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Login failed'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  function logout() {
    admin.value = null
    token.value = null
    localStorage.removeItem('adminToken')
    localStorage.removeItem('admin')
    delete axios.defaults.headers.common['Authorization']
  }

  function hasRole(role) { return admin.value?.role === role }
  function hasPermission(perm) { return admin.value?.permissions?.includes(perm) || admin.value?.role === 'super_admin' }

  return { admin, token, isLoading, error, isAuthenticated, fullName, login, logout, hasRole, hasPermission }
})
