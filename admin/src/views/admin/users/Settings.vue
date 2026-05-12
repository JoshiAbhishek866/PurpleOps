<script setup>
import { useAdminAuthStore } from '@/stores/adminAuth'
import { useRouter } from 'vue-router'

const authStore = useAdminAuthStore()
const router = useRouter()

function logout() {
  authStore.logout()
  router.push('/pages/login')
}
</script>

<template>
  <div>
    <CCard class="mb-4">
      <CCardHeader><strong>Account Settings</strong></CCardHeader>
      <CCardBody>
        <CRow>
          <CCol :md="6">
            <div class="mb-3"><CFormLabel>Email</CFormLabel><CFormInput :value="authStore.admin?.email" disabled /></div>
            <div class="mb-3"><CFormLabel>Name</CFormLabel><CFormInput :value="authStore.fullName" disabled /></div>
            <div class="mb-3"><CFormLabel>Role</CFormLabel><CFormInput :value="authStore.admin?.role" disabled /></div>
            <div class="mb-3"><CFormLabel>Permissions</CFormLabel><div class="d-flex flex-wrap gap-2"><CBadge v-for="p in authStore.admin?.permissions" :key="p" color="info">{{ p }}</CBadge></div></div>
          </CCol>
        </CRow>
        <hr />
        <CButton color="danger" @click="logout"><CIcon icon="cil-lock-locked" class="me-2" />Logout</CButton>
      </CCardBody>
    </CCard>
  </div>
</template>
