<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAdminDataStore } from '@/stores/adminData'

const dataStore = useAdminDataStore()
const isLoading = ref(true)
const showModal = ref(false)
const selectedRequest = ref(null)
const statusFilter = ref('')
const searchQuery = ref('')

const requests = computed(() => dataStore.demoRequests)
const statuses = [
  { value: 'new', label: 'New', color: 'primary' },
  { value: 'contacted', label: 'Contacted', color: 'info' },
  { value: 'scheduled', label: 'Scheduled', color: 'warning' },
  { value: 'completed', label: 'Completed', color: 'success' },
  { value: 'cancelled', label: 'Cancelled', color: 'danger' }
]
const priorities = [
  { value: 'low', label: 'Low', color: 'secondary' },
  { value: 'medium', label: 'Medium', color: 'info' },
  { value: 'high', label: 'High', color: 'warning' },
  { value: 'urgent', label: 'Urgent', color: 'danger' }
]

onMounted(async () => {
  await dataStore.fetchDemoRequests()
  isLoading.value = false
})

function openModal(request) {
  selectedRequest.value = { ...request }
  showModal.value = true
}

async function updateRequest() {
  // Use 'id' field which is what the backend returns
  const requestId = selectedRequest.value.id || selectedRequest.value._id
  const result = await dataStore.updateDemoRequest(requestId, selectedRequest.value)
  if (result.success) {
    showModal.value = false
    // Refresh the list to show updated data
    await dataStore.fetchDemoRequests()
  }
}

function getStatusColor(status) {
  return statuses.find(s => s.value === status)?.color || 'secondary'
}

function getPriorityColor(priority) {
  return priorities.find(p => p.value === priority)?.color || 'secondary'
}

function formatDate(date) {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

async function applyFilters() {
  isLoading.value = true
  await dataStore.fetchDemoRequests({
    search: searchQuery.value,
    status: statusFilter.value
  })
  isLoading.value = false
}
</script>

<template>
  <div>
    <CCard class="mb-4">
      <CCardHeader><strong>Demo Requests</strong></CCardHeader>
      <CCardBody>
        <CRow class="mb-4">
          <CCol :md="6">
            <CFormInput
              v-model="searchQuery"
              placeholder="Search..."
              @keyup.enter="applyFilters"
            />
          </CCol>
          <CCol :md="4">
            <CFormSelect v-model="statusFilter" @change="applyFilters">
              <option value="">All Statuses</option>
              <option v-for="s in statuses" :key="s.value" :value="s.value">
                {{ s.label }}
              </option>
            </CFormSelect>
          </CCol>
          <CCol :md="2">
            <CButton color="secondary" @click="applyFilters" class="w-100">
              Search
            </CButton>
          </CCol>
        </CRow>

        <div v-if="isLoading" class="text-center py-5">
          <CSpinner color="primary" />
        </div>

        <CTable v-else hover responsive>
          <CTableHead>
            <CTableRow>
              <CTableHeaderCell>Contact</CTableHeaderCell>
              <CTableHeaderCell>Company</CTableHeaderCell>
              <CTableHeaderCell>Status</CTableHeaderCell>
              <CTableHeaderCell>Priority</CTableHeaderCell>
              <CTableHeaderCell>Date</CTableHeaderCell>
              <CTableHeaderCell>Actions</CTableHeaderCell>
            </CTableRow>
          </CTableHead>
          <CTableBody>
            <CTableRow v-for="request in requests" :key="request.id || request._id">
              <CTableDataCell>
                <strong>{{ request.firstName }} {{ request.lastName }}</strong>
                <div class="small text-muted">{{ request.email }}</div>
              </CTableDataCell>
              <CTableDataCell>
                <strong>{{ request.company }}</strong>
                <div class="small text-muted" v-if="request.jobTitle">
                  {{ request.jobTitle }}
                </div>
              </CTableDataCell>
              <CTableDataCell>
                <CBadge :color="getStatusColor(request.status)">
                  {{ request.status }}
                </CBadge>
              </CTableDataCell>
              <CTableDataCell>
                <CBadge :color="getPriorityColor(request.priority)">
                  {{ request.priority }}
                </CBadge>
              </CTableDataCell>
              <CTableDataCell>{{ formatDate(request.createdAt) }}</CTableDataCell>
              <CTableDataCell>
                <CButton
                  color="primary"
                  variant="ghost"
                  size="sm"
                  @click="openModal(request)"
                >
                  <CIcon icon="cil-pencil" /> View
                </CButton>
              </CTableDataCell>
            </CTableRow>
            <CTableRow v-if="requests.length === 0">
              <CTableDataCell colspan="6" class="text-center py-4 text-muted">
                No demo requests
              </CTableDataCell>
            </CTableRow>
          </CTableBody>
        </CTable>
      </CCardBody>
    </CCard>

    <CModal :visible="showModal" @close="showModal = false" size="lg">
      <CModalHeader>
        <CModalTitle>Demo Request Details</CModalTitle>
      </CModalHeader>
      <CModalBody v-if="selectedRequest">
        <CRow>
          <CCol :md="6">
            <h6 class="text-muted">Contact</h6>
            <p>
              <strong>Name:</strong>
              {{ selectedRequest.firstName }} {{ selectedRequest.lastName }}
            </p>
            <p><strong>Email:</strong> {{ selectedRequest.email }}</p>
            <p><strong>Phone:</strong> {{ selectedRequest.phone || 'N/A' }}</p>
            <p><strong>Company:</strong> {{ selectedRequest.company }}</p>
          </CCol>
          <CCol :md="6">
            <div class="mb-3">
              <CFormLabel>Status</CFormLabel>
              <CFormSelect v-model="selectedRequest.status">
                <option v-for="s in statuses" :key="s.value" :value="s.value">
                  {{ s.label }}
                </option>
              </CFormSelect>
            </div>
            <div class="mb-3">
              <CFormLabel>Priority</CFormLabel>
              <CFormSelect v-model="selectedRequest.priority">
                <option v-for="p in priorities" :key="p.value" :value="p.value">
                  {{ p.label }}
                </option>
              </CFormSelect>
            </div>
          </CCol>
        </CRow>
        <div v-if="selectedRequest.message">
          <strong>Message:</strong>
          <p class="p-3 bg-light rounded">{{ selectedRequest.message }}</p>
        </div>
      </CModalBody>
      <CModalFooter>
        <CButton color="secondary" @click="showModal = false">Close</CButton>
        <CButton color="primary" @click="updateRequest" :disabled="dataStore.isLoading">
          Save
        </CButton>
      </CModalFooter>
    </CModal>
  </div>
</template>
