import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const API_BASE = 'http://localhost:8000' // import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

export const useAdminDataStore = defineStore('adminData', () => {
  const overview = ref(null)
  const content = ref({})
  const blogPosts = ref([])
  const demoRequests = ref([])
  const clients = ref([])
  const adminUsers = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  // Dashboard
  async function fetchOverview() {
    try {
      const response = await axios.get(`${API_BASE}/api/admin/dashboard`)
      overview.value = response.data.overview
      return response.data
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch'
    }
  }

  // Content
  async function fetchContent() {
    try {
      const response = await axios.get(`${API_BASE}/api/admin/content`)
      const contentArray = response.data.content
      content.value = contentArray.reduce((acc, item) => { acc[item.section] = item; return acc; }, {})
      return content.value
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch'
    }
  }

  async function updateContent(section, contentData) {
    isLoading.value = true
    try {
      const response = await axios.put(`${API_BASE}/api/admin/content/${section}`, { content: contentData, isActive: true })
      content.value[section] = response.data.content
      return { success: true, content: response.data.content }
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to update'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  // Blog
  async function fetchBlogPosts(params = {}) {
    try {
      const queryString = new URLSearchParams(params).toString()
      const response = await axios.get(`${API_BASE}/api/admin/blog?${queryString}`)
      blogPosts.value = response.data.posts
      return response.data
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch'
    }
  }

  async function createBlogPost(postData) {
    isLoading.value = true
    try {
      const response = await axios.post(`${API_BASE}/api/admin/blog`, postData)
      blogPosts.value.unshift(response.data.post)
      return { success: true, post: response.data.post }
    } catch (err) {
      return { success: false, error: err.response?.data?.message || 'Failed to create' }
    } finally {
      isLoading.value = false
    }
  }

  async function updateBlogPost(id, postData) {
    isLoading.value = true
    try {
      const response = await axios.put(`${API_BASE}/api/admin/blog/${id}`, postData)
      const index = blogPosts.value.findIndex(p => p._id === id)
      if (index !== -1) blogPosts.value[index] = response.data.post
      return { success: true, post: response.data.post }
    } catch (err) {
      return { success: false, error: err.response?.data?.message || 'Failed to update' }
    } finally {
      isLoading.value = false
    }
  }

  async function deleteBlogPost(id) {
    isLoading.value = true
    try {
      await axios.delete(`${API_BASE}/api/admin/blog/${id}`)
      blogPosts.value = blogPosts.value.filter(p => p._id !== id)
      return { success: true }
    } catch (err) {
      return { success: false, error: err.response?.data?.message || 'Failed to delete' }
    } finally {
      isLoading.value = false
    }
  }

  // Demo Requests
  async function fetchDemoRequests(params = {}) {
    try {
      const queryString = new URLSearchParams(params).toString()
      const response = await axios.get(`${API_BASE}/api/admin/demo-requests?${queryString}`)
      demoRequests.value = response.data.requests
      return response.data
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch'
    }
  }

  async function updateDemoRequest(id, data) {
    isLoading.value = true
    try {
      const response = await axios.put(`${API_BASE}/api/admin/demo-requests/${id}`, data)
      const index = demoRequests.value.findIndex(r => r._id === id)
      if (index !== -1) demoRequests.value[index] = response.data.request
      return { success: true, request: response.data.request }
    } catch (err) {
      return { success: false, error: err.response?.data?.message || 'Failed to update' }
    } finally {
      isLoading.value = false
    }
  }

  // Clients
  async function fetchClients(params = {}) {
    try {
      const queryString = new URLSearchParams(params).toString()
      const response = await axios.get(`${API_BASE}/api/admin/clients?${queryString}`)
      clients.value = response.data.clients
      return response.data
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch'
    }
  }

  async function createClient(clientData) {
    isLoading.value = true
    try {
      const response = await axios.post(`${API_BASE}/api/admin/clients`, clientData)
      clients.value.unshift(response.data.client)
      return { success: true, client: response.data.client }
    } catch (err) {
      return { success: false, error: err.response?.data?.message || 'Failed to create' }
    } finally {
      isLoading.value = false
    }
  }

  async function updateClient(id, clientData) {
    isLoading.value = true
    try {
      const response = await axios.put(`${API_BASE}/api/admin/clients/${id}`, clientData)
      const index = clients.value.findIndex(c => c._id === id)
      if (index !== -1) clients.value[index] = response.data.client
      return { success: true, client: response.data.client }
    } catch (err) {
      return { success: false, error: err.response?.data?.message || 'Failed to update' }
    } finally {
      isLoading.value = false
    }
  }

  async function deleteClient(id) {
    isLoading.value = true
    try {
      await axios.delete(`${API_BASE}/api/admin/clients/${id}`)
      clients.value = clients.value.filter(c => c._id !== id)
      return { success: true }
    } catch (err) {
      return { success: false, error: err.response?.data?.message || 'Failed to delete' }
    } finally {
      isLoading.value = false
    }
  }

  // Admin Users
  async function fetchAdminUsers() {
    try {
      const response = await axios.get(`${API_BASE}/api/admin/auth/users`)
      adminUsers.value = response.data.admins
      return response.data
    } catch (err) {
      error.value = err.response?.data?.message || 'Failed to fetch'
    }
  }

  async function createAdminUser(userData) {
    isLoading.value = true
    try {
      const response = await axios.post(`${API_BASE}/api/admin/auth/users`, userData)
      adminUsers.value.unshift(response.data.admin)
      return { success: true, admin: response.data.admin }
    } catch (err) {
      return { success: false, error: err.response?.data?.message || 'Failed to create' }
    } finally {
      isLoading.value = false
    }
  }

  async function updateAdminUser(id, userData) {
    isLoading.value = true
    try {
      const response = await axios.put(`${API_BASE}/api/admin/auth/users/${id}`, userData)
      const index = adminUsers.value.findIndex(a => a._id === id)
      if (index !== -1) adminUsers.value[index] = response.data.admin
      return { success: true, admin: response.data.admin }
    } catch (err) {
      return { success: false, error: err.response?.data?.message || 'Failed to update' }
    } finally {
      isLoading.value = false
    }
  }

  async function deleteAdminUser(id) {
    isLoading.value = true
    try {
      await axios.delete(`${API_BASE}/api/admin/auth/users/${id}`)
      adminUsers.value = adminUsers.value.filter(a => a._id !== id)
      return { success: true }
    } catch (err) {
      return { success: false, error: err.response?.data?.message || 'Failed to delete' }
    } finally {
      isLoading.value = false
    }
  }

  return {
    overview, content, blogPosts, demoRequests, clients, adminUsers, isLoading, error,
    fetchOverview, fetchContent, updateContent,
    fetchBlogPosts, createBlogPost, updateBlogPost, deleteBlogPost,
    fetchDemoRequests, updateDemoRequest,
    fetchClients, createClient, updateClient, deleteClient,
    fetchAdminUsers, createAdminUser, updateAdminUser, deleteAdminUser
  }
})
