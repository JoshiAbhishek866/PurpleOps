<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAdminDataStore } from '@/stores/adminData'

const dataStore = useAdminDataStore()
const isLoading = ref(true)
const showModal = ref(false)
const editMode = ref(false)
const selectedClient = ref(null)
const searchQuery = ref('')

const formData = ref({
  name: '',
  email: '',
  phone: '',
  website: '',
  industry: 'technology',
  size: '1-10',
  subscription: { plan: 'free', status: 'trial' },
  services: [],
  securityModels: { offensive: false, defensive: false }
})

const clients = computed(() => dataStore.clients)

const industries = [
  { value: 'technology', label: 'Technology' },
  { value: 'finance', label: 'Finance' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'retail', label: 'Retail' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'government', label: 'Government' }
]

const plans = [
  { value: 'free', label: 'Free', color: 'secondary' },
  { value: 'starter', label: 'Starter', color: 'info' },
  { value: 'professional', label: 'Professional', color: 'primary' },
  { value: 'enterprise', label: 'Enterprise', color: 'warning' }
]

const subscriptionStatuses = [
  { value: 'trial', label: 'Trial', color: 'info' },
  { value: 'active', label: 'Active', color: 'success' },
  { value: 'inactive', label: 'Inactive', color: 'secondary' },
  { value: 'suspended', label: 'Suspended', color: 'warning' },
  { value: 'cancelled', label: 'Cancelled', color: 'danger' }
]

const services = [
  { value: 'web_security', label: 'Web Security' },
  { value: 'app_security', label: 'App Security' },
  { value: 'network_security', label: 'Network Security' },
  { value: 'cloud_security', label: 'Cloud Security' },
  { value: 'api_security', label: 'API Security' },
  { value: 'iot_security', label: 'IoT Security' },
  { value: 'automobile_security', label: 'Automobile Security' }
]

onMounted(async () => {
  await dataStore.fetchClients()
  isLoading.value = false
})

function openCreateModal() {
  editMode.value = false
  formData.value = {
    name: '',
    email: '',
    phone: '',
    website: '',
    industry: 'technology',
    size: '1-10',
    subscription: { plan: 'free', status: 'trial' },
    services: [],
    securityModels: { offensive: false, defensive: false }
  }
  showModal.value = true
}

function openEditModal(client) {
  editMode.value = true
  selectedClient.value = client
  formData.value = JSON.parse(JSON.stringify(client))
  showModal.value = true
}

async function saveClient() {
  let result
  if (editMode.value) {
    const clientId = selectedClient.value.id || selectedClient.value._id
    result = await dataStore.updateClient(clientId, formData.value)
  } else {
    result = await dataStore.createClient(formData.value)
  }
  if (result.success) {
    showModal.value = false
    await dataStore.fetchClients() // Refresh list
  }
}

async function deleteClient(client) {
  if (confirm(`Delete ${client.name}?`)) {
    const clientId = client.id || client._id
    await dataStore.deleteClient(clientId)
  }
}

function getPlanColor(plan) {
  return plans.find(p => p.value === plan)?.color || 'secondary'
}

function getStatusColor(status) {
  return subscriptionStatuses.find(s => s.value === status)?.color || 'secondary'
}

function formatDate(date) {
  return date
    ? new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    : 'N/A'
}

async function applyFilters() {
  isLoading.value = true
  await dataStore.fetchClients({ search: searchQuery.value })
  isLoading.value = false
}

function toggleService(service) {
  if (!formData.value.services) formData.value.services = []
  const index = formData.value.services.indexOf(service)
  if (index > -1) {
    formData.value.services.splice(index, 1)
  } else {
    formData.value.services.push(service)
  }
}
</script>

<template>
  <div>
    <CCard class="mb-4">
      <CCardHeader class="d-flex justify-content-between align-items-center">
        <strong>Client Companies</strong>
        <CButton color="primary" @click="openCreateModal" data-testid="create-client-btn">
          <CIcon icon="cil-plus" class="me-2" />Add Client
        </CButton>
      </CCardHeader>
      <CCardBody>
        <CRow class="mb-4">
          <CCol :md="10">
            <CFormInput
              v-model="searchQuery"
              placeholder="Search clients..."
              @keyup.enter="applyFilters"
            />
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
              <CTableHeaderCell>Company</CTableHeaderCell>
              <CTableHeaderCell>Industry</CTableHeaderCell>
              <CTableHeaderCell>Plan</CTableHeaderCell>
              <CTableHeaderCell>Status</CTableHeaderCell>
              <CTableHeaderCell>Security Models</CTableHeaderCell>
              <CTableHeaderCell>Created</CTableHeaderCell>
              <CTableHeaderCell>Actions</CTableHeaderCell>
            </CTableRow>
          </CTableHead>
          <CTableBody>
            <CTableRow v-for="client in clients" :key="client.id || client._id">
              <CTableDataCell>
                <strong>{{ client.name }}</strong>
                <div class="small text-muted">{{ client.email }}</div>
              </CTableDataCell>
              <CTableDataCell>
                <CBadge color="secondary">{{ client.industry }}</CBadge>
              </CTableDataCell>
              <CTableDataCell>
                <CBadge :color="getPlanColor(client.subscription?.plan)">
                  {{ client.subscription?.plan || 'free' }}
                </CBadge>
              </CTableDataCell>
              <CTableDataCell>
                <CBadge :color="getStatusColor(client.subscription?.status)">
                  {{ client.subscription?.status || 'trial' }}
                </CBadge>
              </CTableDataCell>
              <CTableDataCell>
                <CBadge
                  v-if="client.securityModels?.offensive"
                  color="danger"
                  class="me-1"
                >
                  Offensive
                </CBadge>
                <CBadge v-if="client.securityModels?.defensive" color="success">
                  Defensive
                </CBadge>
                <span v-if="!client.securityModels?.offensive && !client.securityModels?.defensive" class="text-muted">
                  None
                </span>
              </CTableDataCell>
              <CTableDataCell>{{ formatDate(client.createdAt) }}</CTableDataCell>
              <CTableDataCell>
                <CButton
                  color="primary"
                  variant="ghost"
                  size="sm"
                  @click="openEditModal(client)"
                >
                  <CIcon icon="cil-pencil" />
                </CButton>
                <CButton
                  color="danger"
                  variant="ghost"
                  size="sm"
                  @click="deleteClient(client)"
                >
                  <CIcon icon="cil-trash" />
                </CButton>
              </CTableDataCell>
            </CTableRow>
            <CTableRow v-if="clients.length === 0">
              <CTableDataCell colspan="7" class="text-center py-4 text-muted">
                No clients found. Click "Add Client" to create one.
              </CTableDataCell>
            </CTableRow>
          </CTableBody>
        </CTable>
      </CCardBody>
    </CCard>

    <!-- Create/Edit Modal -->
    <CModal :visible="showModal" @close="showModal = false" size="xl">
      <CModalHeader>
        <CModalTitle>{{ editMode ? 'Edit Client' : 'Add New Client' }}</CModalTitle>
      </CModalHeader>
      <CModalBody>
        <CRow>
          <CCol :md="6">
            <h6 class="text-muted mb-3">Company Info</h6>
            <div class="mb-3">
              <CFormLabel>Company Name *</CFormLabel>
              <CFormInput v-model="formData.name" required />
            </div>
            <div class="mb-3">
              <CFormLabel>Email *</CFormLabel>
              <CFormInput v-model="formData.email" type="email" required />
            </div>
            <div class="mb-3">
              <CFormLabel>Phone</CFormLabel>
              <CFormInput v-model="formData.phone" />
            </div>
            <div class="mb-3">
              <CFormLabel>Website</CFormLabel>
              <CFormInput v-model="formData.website" placeholder="https://example.com" />
            </div>
            <CRow>
              <CCol :md="6">
                <div class="mb-3">
                  <CFormLabel>Industry</CFormLabel>
                  <CFormSelect v-model="formData.industry">
                    <option v-for="i in industries" :key="i.value" :value="i.value">
                      {{ i.label }}
                    </option>
                  </CFormSelect>
                </div>
              </CCol>
              <CCol :md="6">
                <div class="mb-3">
                  <CFormLabel>Company Size</CFormLabel>
                  <CFormSelect v-model="formData.size">
                    <option value="1-10">1-10</option>
                    <option value="11-50">11-50</option>
                    <option value="51-200">51-200</option>
                    <option value="201-1000">201-1000</option>
                    <option value="1000+">1000+</option>
                  </CFormSelect>
                </div>
              </CCol>
            </CRow>
          </CCol>

          <CCol :md="6">
            <h6 class="text-muted mb-3">Subscription</h6>
            <CRow>
              <CCol :md="6">
                <div class="mb-3">
                  <CFormLabel>Plan</CFormLabel>
                  <CFormSelect v-model="formData.subscription.plan">
                    <option v-for="p in plans" :key="p.value" :value="p.value">
                      {{ p.label }}
                    </option>
                  </CFormSelect>
                </div>
              </CCol>
              <CCol :md="6">
                <div class="mb-3">
                  <CFormLabel>Status</CFormLabel>
                  <CFormSelect v-model="formData.subscription.status">
                    <option v-for="s in subscriptionStatuses" :key="s.value" :value="s.value">
                      {{ s.label }}
                    </option>
                  </CFormSelect>
                </div>
              </CCol>
            </CRow>

            <h6 class="text-muted mb-3 mt-3">Security Models</h6>
            <CFormCheck
              v-model="formData.securityModels.offensive"
              label="Offensive Security Model"
              class="mb-2"
            />
            <CFormCheck
              v-model="formData.securityModels.defensive"
              label="Defensive Security Model"
              class="mb-3"
            />

            <h6 class="text-muted mb-3">Services</h6>
            <div v-for="s in services" :key="s.value" class="mb-2">
              <CFormCheck
                :id="s.value"
                :checked="formData.services?.includes(s.value)"
                @change="toggleService(s.value)"
                :label="s.label"
              />
            </div>
          </CCol>
        </CRow>
      </CModalBody>
      <CModalFooter>
        <CButton color="secondary" @click="showModal = false">Cancel</CButton>
        <CButton color="primary" @click="saveClient" :disabled="dataStore.isLoading">
          {{ editMode ? 'Update' : 'Create' }}
        </CButton>
      </CModalFooter>
    </CModal>
  </div>
</template>
