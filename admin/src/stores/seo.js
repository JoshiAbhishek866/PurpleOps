import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const useSEOStore = defineStore('seo', () => {
  // State
  const globalSEO = ref(null)
  const pageSEO = ref({}) // Object with page names as keys
  const loading = ref(false)
  const error = ref(null)

  // Actions
  async function fetchGlobalSEO() {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`${API_BASE}/api/seo/global`)
      globalSEO.value = response.data
      return response.data
    } catch (err) {
      error.value = err.message
      console.error('Error fetching global SEO:', err)
      return {
        siteName: 'PurpleOps',
        siteUrl: 'https://PurpleOps.com',
        defaultOgImage: 'https://PurpleOps.com/og-image.jpg',
        themeColor: '#8b5cf6',
        twitterSite: '@PurpleOps',
        defaultAuthor: 'PurpleOps Team',
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchPageSEO(page) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`${API_BASE}/api/seo/pages/${page}`)
      pageSEO.value[page] = response.data
      return response.data
    } catch (err) {
      error.value = err.message
      console.error(`Error fetching SEO for page ${page}:`, err)
      return {}
    } finally {
      loading.value = false
    }
  }

  async function updateGlobalSEO(settings) {
    loading.value = true
    error.value = null

    try {
      const token = localStorage.getItem('adminToken')
      const response = await axios.put(`${API_BASE}/api/admin/seo/global`, settings, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      globalSEO.value = response.data.settings
      return response.data
    } catch (err) {
      error.value = err.message
      console.error('Error updating global SEO:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updatePageSEO(page, seoData) {
    loading.value = true
    error.value = null

    try {
      const token = localStorage.getItem('adminToken')
      const response = await axios.put(`${API_BASE}/api/admin/seo/pages/${page}`, seoData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      pageSEO.value[page] = {
        page: response.data.page,
        seo: response.data.seo,
      }
      return response.data
    } catch (err) {
      error.value = err.message
      console.error(`Error updating SEO for page ${page}:`, err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchAllPagesSEO() {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`${API_BASE}/api/seo/pages`)

      // Convert array to object with page names as keys
      const pagesObj = {}
      response.data.pages.forEach((page) => {
        pagesObj[page.page] = page
      })
      pageSEO.value = pagesObj

      return response.data.pages
    } catch (err) {
      error.value = err.message
      console.error('Error fetching all pages SEO:', err)
      return []
    } finally {
      loading.value = false
    }
  }

  async function deletePageSEO(page) {
    loading.value = true
    error.value = null

    try {
      const token = localStorage.getItem('adminToken')
      const response = await axios.delete(`${API_BASE}/api/admin/seo/pages/${page}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      // Remove from local state
      delete pageSEO.value[page]

      return response.data
    } catch (err) {
      error.value = err.message
      console.error(`Error deleting SEO for page ${page}:`, err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function bulkUpdateSEO(pages) {
    loading.value = true
    error.value = null

    try {
      const token = localStorage.getItem('adminToken')
      const response = await axios.post(
        `${API_BASE}/api/admin/seo/pages/bulk`,
        { pages },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      )

      // Update local state
      pages.forEach((pageData) => {
        pageSEO.value[pageData.page] = pageData
      })

      return response.data
    } catch (err) {
      error.value = err.message
      console.error('Error bulk updating SEO:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    globalSEO,
    pageSEO,
    loading,
    error,

    // Actions
    fetchGlobalSEO,
    fetchPageSEO,
    updateGlobalSEO,
    updatePageSEO,
    fetchAllPagesSEO,
    deletePageSEO,
    bulkUpdateSEO,
  }
})
