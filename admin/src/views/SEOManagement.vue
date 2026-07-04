<template>
  <div>
    <!-- Header Card -->
    <CCard class="mb-4">
      <CCardHeader class="d-flex justify-content-between align-items-center">
        <div>
          <strong>SEO Management</strong>
          <div class="text-muted small mt-1">
            Manage SEO metadata for all pages across your website
          </div>
        </div>
        <div class="d-flex gap-2">
          <CButton color="secondary" variant="outline" @click="refreshData" :disabled="loading">
            <CSpinner v-if="loading" size="sm" class="me-1" />Refresh
          </CButton>
          <CButton color="primary" @click="showGlobalSettings = true"> ⚙️ Global Settings </CButton>
        </div>
      </CCardHeader>

      <CCardBody>
        <!-- Loading -->
        <div v-if="loading && !pages.length" class="text-center py-5">
          <CSpinner color="primary" />
          <p class="mt-3 text-muted">Loading SEO settings...</p>
        </div>

        <!-- Pages Table -->
        <div v-else>
          <CTable hover responsive bordered align="middle">
            <CTableHead color="light">
              <CTableRow>
                <CTableHeaderCell>Page</CTableHeaderCell>
                <CTableHeaderCell>URL</CTableHeaderCell>
                <CTableHeaderCell>Title</CTableHeaderCell>
                <CTableHeaderCell>Description</CTableHeaderCell>
                <CTableHeaderCell>Keywords</CTableHeaderCell>
                <CTableHeaderCell>Robots</CTableHeaderCell>
                <CTableHeaderCell class="text-center">Actions</CTableHeaderCell>
              </CTableRow>
            </CTableHead>
            <CTableBody>
              <CTableRow v-for="page in pages" :key="page.page">
                <CTableDataCell>
                  <div class="d-flex align-items-center gap-2">
                    <span>{{ getPageIcon(page.page) }}</span>
                    <strong>{{ formatPageName(page.page) }}</strong>
                  </div>
                </CTableDataCell>
                <CTableDataCell>
                  <CBadge color="secondary" class="font-monospace">{{
                    getPagePath(page.page)
                  }}</CBadge>
                </CTableDataCell>
                <CTableDataCell style="max-width: 200px">
                  <span
                    class="text-truncate d-block"
                    style="max-width: 200px"
                    :title="page.seo?.title"
                  >
                    {{ page.seo?.title || '—' }}
                  </span>
                </CTableDataCell>
                <CTableDataCell style="max-width: 220px">
                  <span
                    class="text-truncate d-block text-muted small"
                    style="max-width: 220px"
                    :title="page.seo?.description"
                  >
                    {{ page.seo?.description || '—' }}
                  </span>
                </CTableDataCell>
                <CTableDataCell style="max-width: 160px">
                  <span
                    class="text-truncate d-block text-muted small"
                    style="max-width: 160px"
                    :title="page.seo?.keywords"
                  >
                    {{ page.seo?.keywords || '—' }}
                  </span>
                </CTableDataCell>
                <CTableDataCell>
                  <CBadge :color="page.seo?.robots?.includes('noindex') ? 'warning' : 'success'">
                    {{ page.seo?.robots || 'index, follow' }}
                  </CBadge>
                </CTableDataCell>
                <CTableDataCell class="text-center">
                  <div class="d-flex gap-1 justify-content-center">
                    <CButton
                      color="primary"
                      size="sm"
                      variant="outline"
                      @click="editPage(page)"
                      title="Edit"
                    >
                      <CIcon icon="cil-pencil" />
                    </CButton>
                    <CButton
                      v-if="!page.isDefault"
                      color="danger"
                      size="sm"
                      variant="outline"
                      @click="deletePage(page.page)"
                      title="Reset to default"
                    >
                      <CIcon icon="cil-trash" />
                    </CButton>
                  </div>
                </CTableDataCell>
              </CTableRow>
            </CTableBody>
          </CTable>

          <!-- Add New Page Button -->
          <div class="mt-3">
            <CButton color="primary" variant="outline" @click="addNewPage">
              <CIcon icon="cil-plus" class="me-1" />Add New Page
            </CButton>
          </div>
        </div>
      </CCardBody>
    </CCard>

    <!-- Edit / Add Page Modal -->
    <CModal :visible="!!editingPage" @close="closeEditModal" size="lg" backdrop="static">
      <CModalHeader>
        <CModalTitle>
          {{
            editingPage?.page
              ? `Edit SEO — ${formatPageName(editingPage.page)}`
              : 'Add New Page SEO'
          }}
        </CModalTitle>
      </CModalHeader>
      <CModalBody>
        <div class="mb-3">
          <CFormLabel>Page Identifier</CFormLabel>
          <CFormInput
            v-model="editForm.page"
            :disabled="!!editingPage?.page"
            placeholder="e.g., home, about, blog"
          />
          <div class="form-text">Lowercase, no spaces (use hyphens)</div>
        </div>

        <div class="mb-3">
          <CFormLabel>Page Title <span class="text-danger">*</span></CFormLabel>
          <CFormInput
            v-model="editForm.seo.title"
            placeholder="e.g., Secure Your Digital Assets | PurpleOps"
          />
        </div>

        <div class="mb-3">
          <CFormLabel>Meta Description <span class="text-danger">*</span></CFormLabel>
          <CFormTextarea
            v-model="editForm.seo.description"
            rows="3"
            placeholder="Brief description of the page (150-160 characters)"
          />
          <div class="form-text d-flex justify-content-between">
            <span>Recommended: 150–160 characters</span>
            <span :class="editForm.seo.description.length > 160 ? 'text-danger' : 'text-muted'">
              {{ editForm.seo.description.length }} / 160
            </span>
          </div>
        </div>

        <div class="mb-3">
          <CFormLabel>Keywords</CFormLabel>
          <CFormInput v-model="editForm.seo.keywords" placeholder="keyword1, keyword2, keyword3" />
          <div class="form-text">Comma-separated keywords</div>
        </div>

        <CRow class="mb-3">
          <CCol :md="8">
            <CFormLabel>OG Image URL</CFormLabel>
            <CFormInput
              v-model="editForm.seo.ogImage"
              type="url"
              placeholder="https://example.com/og-image.jpg"
            />
          </CCol>
          <CCol :md="4">
            <CFormLabel>OG Type</CFormLabel>
            <CFormSelect v-model="editForm.seo.ogType">
              <option value="website">Website</option>
              <option value="article">Article</option>
              <option value="product">Product</option>
            </CFormSelect>
          </CCol>
        </CRow>

        <CRow class="mb-3">
          <CCol :md="8">
            <CFormLabel>Canonical URL</CFormLabel>
            <CFormInput
              v-model="editForm.seo.canonical"
              type="url"
              placeholder="https://PurpleOps.com/page"
            />
          </CCol>
          <CCol :md="4">
            <CFormLabel>Robots</CFormLabel>
            <CFormSelect v-model="editForm.seo.robots">
              <option value="index, follow">Index, Follow</option>
              <option value="noindex, follow">No Index, Follow</option>
              <option value="index, nofollow">Index, No Follow</option>
              <option value="noindex, nofollow">No Index, No Follow</option>
            </CFormSelect>
          </CCol>
        </CRow>

        <div class="mb-3">
          <CFormLabel>Author</CFormLabel>
          <CFormInput v-model="editForm.seo.author" placeholder="PurpleOps Team" />
        </div>
      </CModalBody>
      <CModalFooter>
        <CButton color="secondary" variant="outline" @click="closeEditModal">Cancel</CButton>
        <CButton color="primary" @click="savePage" :disabled="saving">
          <CSpinner v-if="saving" size="sm" class="me-1" />{{
            saving ? 'Saving...' : 'Save Changes'
          }}
        </CButton>
      </CModalFooter>
    </CModal>

    <!-- Global Settings Modal -->
    <CModal
      :visible="showGlobalSettings"
      @close="showGlobalSettings = false"
      size="lg"
      backdrop="static"
    >
      <CModalHeader>
        <CModalTitle>Global SEO Settings</CModalTitle>
      </CModalHeader>
      <CModalBody>
        <div class="mb-3">
          <CFormLabel>Site Name <span class="text-danger">*</span></CFormLabel>
          <CFormInput v-model="globalForm.siteName" placeholder="PurpleOps" />
        </div>

        <div class="mb-3">
          <CFormLabel>Site URL <span class="text-danger">*</span></CFormLabel>
          <CFormInput v-model="globalForm.siteUrl" type="url" placeholder="https://PurpleOps.com" />
        </div>

        <div class="mb-3">
          <CFormLabel>Default OG Image</CFormLabel>
          <CFormInput
            v-model="globalForm.defaultOgImage"
            type="url"
            placeholder="https://PurpleOps.com/og-image.jpg"
          />
        </div>

        <CRow class="mb-3">
          <CCol :md="3">
            <CFormLabel>Theme Color</CFormLabel>
            <CFormInput v-model="globalForm.themeColor" type="color" style="height: 40px" />
          </CCol>
          <CCol :md="4">
            <CFormLabel>Twitter Handle</CFormLabel>
            <CFormInput v-model="globalForm.twitterSite" placeholder="@PurpleOps" />
          </CCol>
          <CCol :md="5">
            <CFormLabel>Default Author</CFormLabel>
            <CFormInput v-model="globalForm.defaultAuthor" placeholder="PurpleOps Team" />
          </CCol>
        </CRow>
      </CModalBody>
      <CModalFooter>
        <CButton color="secondary" variant="outline" @click="showGlobalSettings = false"
          >Cancel</CButton
        >
        <CButton color="primary" @click="saveGlobalSettings" :disabled="saving">
          <CSpinner v-if="saving" size="sm" class="me-1" />{{
            saving ? 'Saving...' : 'Save Settings'
          }}
        </CButton>
      </CModalFooter>
    </CModal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useSEOStore } from '@/stores/seo'

const seoStore = useSEOStore()

const loading = ref(false)
const saving = ref(false)
const editingPage = ref(null)
const showGlobalSettings = ref(false)
const pages = ref([])

const editForm = ref({
  page: '',
  seo: {
    title: '',
    description: '',
    keywords: '',
    ogImage: '',
    ogType: 'website',
    canonical: '',
    robots: 'index, follow',
    author: '',
  },
})

const globalForm = ref({
  siteName: 'PurpleOps',
  siteUrl: 'https://PurpleOps.com',
  defaultOgImage: 'https://PurpleOps.com/og-image.jpg',
  themeColor: '#8b5cf6',
  twitterSite: '@PurpleOps',
  defaultAuthor: 'PurpleOps Team',
})

const pageIcons = {
  home: '🏠',
  about: 'ℹ️',
  blog: '📰',
  'book-demo': '📅',
  dashboard: '📊',
  'architecture-map': '🗺️',
  pricing: '💰',
}

function getPageIcon(page) {
  return pageIcons[page] || '📄'
}

function formatPageName(page) {
  return page
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function getPagePath(page) {
  if (page === 'home') return '/'
  if (page.startsWith('dashboard')) return `/dashboard/${page.replace('dashboard-', '')}`
  return `/${page}`
}

async function refreshData() {
  loading.value = true
  try {
    await Promise.all([seoStore.fetchGlobalSEO(), seoStore.fetchAllPagesSEO()])
    pages.value = Object.values(seoStore.pageSEO)
    if (seoStore.globalSEO) {
      globalForm.value = { ...seoStore.globalSEO }
    }
  } catch (error) {
    console.error('Error refreshing data:', error)
  } finally {
    loading.value = false
  }
}

function editPage(page) {
  editingPage.value = page
  editForm.value = {
    page: page.page,
    seo: { ...page.seo },
  }
}

function addNewPage() {
  editingPage.value = {}
  editForm.value = {
    page: '',
    seo: {
      title: '',
      description: '',
      keywords: '',
      ogImage: '',
      ogType: 'website',
      canonical: '',
      robots: 'index, follow',
      author: '',
    },
  }
}

function closeEditModal() {
  editingPage.value = null
  editForm.value = {
    page: '',
    seo: {
      title: '',
      description: '',
      keywords: '',
      ogImage: '',
      ogType: 'website',
      canonical: '',
      robots: 'index, follow',
      author: '',
    },
  }
}

async function savePage() {
  if (!editForm.value.seo.title || !editForm.value.seo.description) {
    alert('Please fill in required fields')
    return
  }
  saving.value = true
  try {
    await seoStore.updatePageSEO(editForm.value.page, editForm.value.seo)
    await refreshData()
    closeEditModal()
  } catch (error) {
    alert('Failed to save page SEO: ' + error.message)
  } finally {
    saving.value = false
  }
}

async function deletePage(page) {
  if (!confirm(`Reset SEO settings for "${formatPageName(page)}" to defaults?`)) return
  try {
    await seoStore.deletePageSEO(page)
    await refreshData()
  } catch (error) {
    alert('Failed to reset page SEO: ' + error.message)
  }
}

async function saveGlobalSettings() {
  saving.value = true
  try {
    await seoStore.updateGlobalSEO(globalForm.value)
    showGlobalSettings.value = false
  } catch (error) {
    alert('Failed to save global settings: ' + error.message)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  refreshData()
})
</script>
