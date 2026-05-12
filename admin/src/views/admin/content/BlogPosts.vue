<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAdminDataStore } from '@/stores/adminData'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001'

const dataStore = useAdminDataStore()
const isLoading = ref(true)
const showModal = ref(false)
const editMode = ref(false)
const selectedPost = ref(null)
const searchQuery = ref('')
const statusFilter = ref('')
const isUploading = ref(false)
const uploadProgress = ref(0)

const formData = ref({ title: '', slug: '', excerpt: '', content: '', featuredImage: '', author: 'Admin', category: 'cybersecurity', tags: [], status: 'draft' })
const posts = computed(() => dataStore.blogPosts)
const categories = [{ value: 'cybersecurity', label: 'Cybersecurity' }, { value: 'ai', label: 'AI & ML' }, { value: 'threat-detection', label: 'Threat Detection' }, { value: 'compliance', label: 'Compliance' }, { value: 'tutorials', label: 'Tutorials' }]
const statuses = [{ value: 'draft', label: 'Draft', color: 'secondary' }, { value: 'published', label: 'Published', color: 'success' }, { value: 'archived', label: 'Archived', color: 'warning' }]

onMounted(async () => { await dataStore.fetchBlogPosts(); isLoading.value = false })

function openCreateModal() { editMode.value = false; formData.value = { title: '', slug: '', excerpt: '', content: '', featuredImage: '', author: 'Admin', category: 'cybersecurity', tags: [], status: 'draft' }; showModal.value = true }
function openEditModal(post) { editMode.value = true; selectedPost.value = post; formData.value = { ...post, author: post.author?.name || post.author || 'Admin' }; showModal.value = true }
async function savePost() { 
  const postData = { ...formData.value }
  if (typeof postData.author === 'string') {
    postData.author = postData.author
  }
  let result
  if (editMode.value) { 
    result = await dataStore.updateBlogPost(selectedPost.value._id || selectedPost.value.id, postData) 
  } else { 
    result = await dataStore.createBlogPost(postData) 
  } 
  if (result.success) showModal.value = false 
}
async function deletePost(id) { if (confirm('Delete this post?')) await dataStore.deleteBlogPost(id) }
function getStatusColor(status) { return statuses.find(s => s.value === status)?.color || 'secondary' }
function formatDate(date) { if (!date) return 'N/A'; return new Date(date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) }
async function applyFilters() { isLoading.value = true; await dataStore.fetchBlogPosts({ search: searchQuery.value, status: statusFilter.value }); isLoading.value = false }

// Image upload handler
async function handleImageUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  
  // Validate file type
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    alert('Please upload an image file (JPEG, PNG, GIF, or WebP)')
    return
  }
  
  // Validate file size (10MB max)
  if (file.size > 10 * 1024 * 1024) {
    alert('File size must be less than 10MB')
    return
  }
  
  isUploading.value = true
  uploadProgress.value = 0
  
  try {
    const formDataUpload = new FormData()
    formDataUpload.append('file', file)
    
    const response = await axios.post(`${API_BASE}/api/uploads/`, formDataUpload, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      }
    })
    
    if (response.data.success) {
      formData.value.featuredImage = `${API_BASE}${response.data.url}`
    }
  } catch (error) {
    console.error('Upload failed:', error)
    alert('Failed to upload image. Please try again.')
  } finally {
    isUploading.value = false
    uploadProgress.value = 0
  }
}

function removeImage() {
  formData.value.featuredImage = ''
}
</script>

<template>
  <div>
    <CCard class="mb-4">
      <CCardHeader class="d-flex justify-content-between align-items-center">
        <strong>Blog Posts</strong>
        <CButton color="primary" @click="openCreateModal" data-testid="create-post-btn"><CIcon icon="cil-plus" class="me-2" />New Post</CButton>
      </CCardHeader>
      <CCardBody>
        <CRow class="mb-4">
          <CCol :md="6"><CFormInput v-model="searchQuery" placeholder="Search posts..." @keyup.enter="applyFilters" /></CCol>
          <CCol :md="4"><CFormSelect v-model="statusFilter" @change="applyFilters"><option value="">All Statuses</option><option v-for="s in statuses" :key="s.value" :value="s.value">{{ s.label }}</option></CFormSelect></CCol>
          <CCol :md="2"><CButton color="secondary" @click="applyFilters" class="w-100">Search</CButton></CCol>
        </CRow>
        <div v-if="isLoading" class="text-center py-5"><CSpinner color="primary" /></div>
        <CTable v-else hover responsive>
          <CTableHead><CTableRow><CTableHeaderCell>Title</CTableHeaderCell><CTableHeaderCell>Category</CTableHeaderCell><CTableHeaderCell>Status</CTableHeaderCell><CTableHeaderCell>Views</CTableHeaderCell><CTableHeaderCell>Date</CTableHeaderCell><CTableHeaderCell>Actions</CTableHeaderCell></CTableRow></CTableHead>
          <CTableBody>
            <CTableRow v-for="post in posts" :key="post._id">
              <CTableDataCell><strong>{{ post.title }}</strong><div class="small text-muted">{{ post.slug }}</div></CTableDataCell>
              <CTableDataCell><CBadge color="info">{{ post.category }}</CBadge></CTableDataCell>
              <CTableDataCell><CBadge :color="getStatusColor(post.status)">{{ post.status }}</CBadge></CTableDataCell>
              <CTableDataCell>{{ post.views || 0 }}</CTableDataCell>
              <CTableDataCell>{{ formatDate(post.createdAt) }}</CTableDataCell>
              <CTableDataCell><CButton color="primary" variant="ghost" size="sm" @click="openEditModal(post)"><CIcon icon="cil-pencil" /></CButton><CButton color="danger" variant="ghost" size="sm" @click="deletePost(post._id)"><CIcon icon="cil-trash" /></CButton></CTableDataCell>
            </CTableRow>
            <CTableRow v-if="posts.length === 0"><CTableDataCell colspan="6" class="text-center py-4 text-muted">No posts found</CTableDataCell></CTableRow>
          </CTableBody>
        </CTable>
      </CCardBody>
    </CCard>
    <CModal :visible="showModal" @close="showModal = false" size="xl">
      <CModalHeader><CModalTitle>{{ editMode ? 'Edit Post' : 'Create New Post' }}</CModalTitle></CModalHeader>
      <CModalBody>
        <CRow>
          <CCol :md="8">
            <div class="mb-3"><CFormLabel>Title *</CFormLabel><CFormInput v-model="formData.title" required /></div>
            <div class="mb-3"><CFormLabel>Slug</CFormLabel><CFormInput v-model="formData.slug" /></div>
            <div class="mb-3"><CFormLabel>Excerpt *</CFormLabel><CFormTextarea v-model="formData.excerpt" rows="2" required /></div>
            <div class="mb-3"><CFormLabel>Content *</CFormLabel><CFormTextarea v-model="formData.content" rows="10" required /></div>
          </CCol>
          <CCol :md="4">
            <div class="mb-3"><CFormLabel>Status</CFormLabel><CFormSelect v-model="formData.status"><option v-for="s in statuses" :key="s.value" :value="s.value">{{ s.label }}</option></CFormSelect></div>
            <div class="mb-3"><CFormLabel>Category</CFormLabel><CFormSelect v-model="formData.category"><option v-for="c in categories" :key="c.value" :value="c.value">{{ c.label }}</option></CFormSelect></div>
            <div class="mb-3">
              <CFormLabel>Featured Image</CFormLabel>
              <div v-if="formData.featuredImage" class="mb-2">
                <img :src="formData.featuredImage" alt="Featured Image Preview" style="max-width: 100%; max-height: 150px; object-fit: cover; border-radius: 8px;" />
                <CButton color="danger" size="sm" variant="ghost" @click="removeImage" class="mt-1">Remove Image</CButton>
              </div>
              <div v-if="isUploading" class="mb-2">
                <CProgress :value="uploadProgress" />
                <small class="text-muted">Uploading... {{ uploadProgress }}%</small>
              </div>
              <CFormInput type="file" accept="image/*" @change="handleImageUpload" :disabled="isUploading" />
              <small class="text-muted d-block mt-1">Or enter URL:</small>
              <CFormInput v-model="formData.featuredImage" placeholder="https://..." class="mt-1" />
            </div>
            <div class="mb-3"><CFormLabel>Author Name *</CFormLabel><CFormInput v-model="formData.author" required /></div>
            <div class="mb-3"><CFormLabel>Tags (comma separated)</CFormLabel><CFormInput :value="formData.tags?.join(', ')" @input="formData.tags = $event.target.value.split(',').map(s => s.trim()).filter(s => s)" /></div>
          </CCol>
        </CRow>
      </CModalBody>
      <CModalFooter><CButton color="secondary" @click="showModal = false">Cancel</CButton><CButton color="primary" @click="savePost" :disabled="dataStore.isLoading">{{ editMode ? 'Update' : 'Create' }}</CButton></CModalFooter>
    </CModal>
  </div>
</template>
