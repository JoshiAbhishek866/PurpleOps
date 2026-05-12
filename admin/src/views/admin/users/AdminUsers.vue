<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAdminDataStore } from '@/stores/adminData'
import { useAdminAuthStore } from '@/stores/adminAuth'
import AdminSEO from '@/components/AdminSEO.vue'

const dataStore = useAdminDataStore()
const authStore = useAdminAuthStore()
const isLoading = ref(true)
const showModal = ref(false)
const editMode = ref(false)
const selectedUser = ref(null)

const formData = ref({
  email: '',
  password: '',
  firstName: '',
  lastName: '',
  role: 'editor',
  permissions: ['content', 'blog'],
  isActive: true,
})
const users = computed(() => dataStore.adminUsers)
const roles = [
  { value: 'super_admin', label: 'Super Admin', color: 'danger' },
  { value: 'admin', label: 'Admin', color: 'warning' },
  { value: 'editor', label: 'Editor', color: 'info' },
]
const allPermissions = [
  { value: 'content', label: 'Content' },
  { value: 'blog', label: 'Blog' },
  { value: 'users', label: 'Users' },
  { value: 'clients', label: 'Clients' },
  { value: 'demo_requests', label: 'Demo Requests' },
  { value: 'settings', label: 'Settings' },
  { value: 'analytics', label: 'Analytics' },
]

onMounted(async () => {
  await dataStore.fetchAdminUsers()
  isLoading.value = false
})

function openCreateModal() {
  editMode.value = false
  formData.value = {
    email: '',
    password: '',
    firstName: '',
    lastName: '',
    role: 'editor',
    permissions: ['content', 'blog'],
    isActive: true,
  }
  showModal.value = true
}
function openEditModal(user) {
  editMode.value = true
  selectedUser.value = user
  formData.value = { ...user, password: '' }
  showModal.value = true
}
async function saveUser() {
  let result
  const data = { ...formData.value }
  if (editMode.value && !data.password) delete data.password
  if (editMode.value) {
    result = await dataStore.updateAdminUser(selectedUser.value._id, data)
  } else {
    result = await dataStore.createAdminUser(data)
  }
  if (result.success) showModal.value = false
}
async function deleteUser(id) {
  if (id === authStore.admin?.id) {
    alert('Cannot delete yourself')
    return
  }
  if (confirm('Delete this admin?')) await dataStore.deleteAdminUser(id)
}
function getRoleColor(role) {
  return roles.find((r) => r.value === role)?.color || 'secondary'
}
function formatDate(date) {
  return date ? new Date(date).toLocaleString() : 'Never'
}
function togglePermission(perm) {
  if (!formData.value.permissions) formData.value.permissions = []
  const index = formData.value.permissions.indexOf(perm)
  if (index > -1) {
    formData.value.permissions.splice(index, 1)
  } else {
    formData.value.permissions.push(perm)
  }
}
</script>

<template>
  <div>
    <AdminSEO title="Admin Users" description="Manage admin users and permissions" />
    <CCard class="mb-4">
      <CCardHeader class="d-flex justify-content-between align-items-center">
        <strong>Admin Users</strong>
        <CButton
          v-if="authStore.hasRole('super_admin')"
          color="primary"
          @click="openCreateModal"
          data-testid="create-admin-btn"
          ><CIcon icon="cil-plus" class="me-2" />Add Admin</CButton
        >
      </CCardHeader>
      <CCardBody>
        <div v-if="isLoading" class="text-center py-5"><CSpinner color="primary" /></div>
        <CTable v-else hover responsive>
          <CTableHead
            ><CTableRow
              ><CTableHeaderCell>Name</CTableHeaderCell><CTableHeaderCell>Email</CTableHeaderCell
              ><CTableHeaderCell>Role</CTableHeaderCell><CTableHeaderCell>Status</CTableHeaderCell
              ><CTableHeaderCell>Last Login</CTableHeaderCell
              ><CTableHeaderCell>Actions</CTableHeaderCell></CTableRow
            ></CTableHead
          >
          <CTableBody>
            <CTableRow v-for="user in users" :key="user._id">
              <CTableDataCell
                ><strong>{{ user.firstName }} {{ user.lastName }}</strong>
                <div v-if="user._id === authStore.admin?.id" class="small text-muted">
                  (You)
                </div></CTableDataCell
              >
              <CTableDataCell>{{ user.email }}</CTableDataCell>
              <CTableDataCell
                ><CBadge :color="getRoleColor(user.role)">{{ user.role }}</CBadge></CTableDataCell
              >
              <CTableDataCell
                ><CBadge :color="user.isActive ? 'success' : 'danger'">{{
                  user.isActive ? 'Active' : 'Inactive'
                }}</CBadge></CTableDataCell
              >
              <CTableDataCell>{{ formatDate(user.lastLogin) }}</CTableDataCell>
              <CTableDataCell>
                <CButton
                  v-if="authStore.hasRole('super_admin')"
                  color="primary"
                  variant="ghost"
                  size="sm"
                  @click="openEditModal(user)"
                  ><CIcon icon="cil-pencil"
                /></CButton>
                <CButton
                  v-if="authStore.hasRole('super_admin') && user._id !== authStore.admin?.id"
                  color="danger"
                  variant="ghost"
                  size="sm"
                  @click="deleteUser(user._id)"
                  ><CIcon icon="cil-trash"
                /></CButton>
              </CTableDataCell>
            </CTableRow>
            <CTableRow v-if="users.length === 0"
              ><CTableDataCell colspan="6" class="text-center py-4 text-muted"
                >No admin users</CTableDataCell
              ></CTableRow
            >
          </CTableBody>
        </CTable>
      </CCardBody>
    </CCard>
    <CModal :visible="showModal" @close="showModal = false" size="lg">
      <CModalHeader
        ><CModalTitle>{{ editMode ? 'Edit Admin' : 'Create Admin' }}</CModalTitle></CModalHeader
      >
      <CModalBody>
        <CRow
          ><CCol :md="6"
            ><div class="mb-3">
              <CFormLabel>First Name *</CFormLabel
              ><CFormInput v-model="formData.firstName" required /></div></CCol
          ><CCol :md="6"
            ><div class="mb-3">
              <CFormLabel>Last Name *</CFormLabel
              ><CFormInput v-model="formData.lastName" required /></div></CCol
        ></CRow>
        <div class="mb-3">
          <CFormLabel>Email *</CFormLabel
          ><CFormInput v-model="formData.email" type="email" required :disabled="editMode" />
        </div>
        <div class="mb-3">
          <CFormLabel>{{
            editMode ? 'New Password (leave empty to keep)' : 'Password *'
          }}</CFormLabel
          ><CFormInput v-model="formData.password" type="password" :required="!editMode" />
        </div>
        <CRow
          ><CCol :md="6"
            ><div class="mb-3">
              <CFormLabel>Role</CFormLabel
              ><CFormSelect v-model="formData.role"
                ><option v-for="r in roles" :key="r.value" :value="r.value">
                  {{ r.label }}
                </option></CFormSelect
              >
            </div></CCol
          ><CCol :md="6"
            ><div class="mb-3">
              <CFormLabel>Status</CFormLabel
              ><CFormSelect v-model="formData.isActive"
                ><option :value="true">Active</option>
                <option :value="false">Inactive</option></CFormSelect
              >
            </div></CCol
          ></CRow
        >
        <div class="mb-3">
          <CFormLabel>Permissions</CFormLabel>
          <div class="d-flex flex-wrap gap-2">
            <CFormCheck
              v-for="p in allPermissions"
              :key="p.value"
              :id="p.value"
              :checked="formData.permissions?.includes(p.value)"
              @change="togglePermission(p.value)"
              :label="p.label"
            />
          </div>
        </div>
      </CModalBody>
      <CModalFooter
        ><CButton color="secondary" @click="showModal = false">Cancel</CButton
        ><CButton color="primary" @click="saveUser" :disabled="dataStore.isLoading">{{
          editMode ? 'Update' : 'Create'
        }}</CButton></CModalFooter
      >
    </CModal>
  </div>
</template>
