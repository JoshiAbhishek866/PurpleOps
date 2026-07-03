<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAdminDataStore } from '@/stores/adminData'
import { useAdminAuthStore } from '@/stores/adminAuth'
import AdminSEO from '@/components/AdminSEO.vue'

const dataStore = useAdminDataStore()
const authStore = useAdminAuthStore()
const isLoading = ref(true)

const overview = computed(() => dataStore.overview)

onMounted(async () => {
  await dataStore.fetchOverview()
  isLoading.value = false
})
</script>

<template>
  <div>
    <AdminSEO title="Dashboard" description="PurpleOps Admin Dashboard - Overview and Statistics" />
    <div v-if="isLoading" class="text-center py-5"><CSpinner color="primary" /></div>

    <CRow v-else class="mb-4">
      <CCol :sm="6" :lg="4">
        <CCard class="mb-4">
          <CCardBody>
            <div class="d-flex justify-content-between">
              <div>
                <div class="text-body-secondary text-uppercase fw-semibold small">Blog Posts</div>
                <div class="fs-4 fw-semibold">{{ overview?.blog?.total || 0 }}</div>
              </div>
              <div class="bg-success bg-opacity-25 p-3 rounded">
                <CIcon icon="cil-newspaper" size="xl" class="text-success" />
              </div>
            </div>
            <div class="small text-body-secondary mt-2">
              <span class="text-success">{{ overview?.blog?.published || 0 }}</span> published
            </div>
          </CCardBody>
        </CCard>
      </CCol>
      <CCol :sm="6" :lg="4">
        <CCard class="mb-4">
          <CCardBody>
            <div class="d-flex justify-content-between">
              <div>
                <div class="text-body-secondary text-uppercase fw-semibold small">
                  Demo Requests
                </div>
                <div class="fs-4 fw-semibold">{{ overview?.demoRequests?.total || 0 }}</div>
              </div>
              <div class="bg-warning bg-opacity-25 p-3 rounded">
                <CIcon icon="cil-calendar" size="xl" class="text-warning" />
              </div>
            </div>
            <div class="small text-body-secondary mt-2">
              <span class="text-warning">{{ overview?.demoRequests?.pending || 0 }}</span> pending
            </div>
          </CCardBody>
        </CCard>
      </CCol>
      <CCol :sm="6" :lg="4">
        <CCard class="mb-4">
          <CCardBody>
            <div class="d-flex justify-content-between">
              <div>
                <div class="text-body-secondary text-uppercase fw-semibold small">Clients</div>
                <div class="fs-4 fw-semibold">{{ overview?.clients?.total || 0 }}</div>
              </div>
              <div class="bg-primary bg-opacity-25 p-3 rounded">
                <CIcon icon="cil-building" size="xl" class="text-primary" />
              </div>
            </div>
            <div class="small text-body-secondary mt-2">
              <span class="text-primary">{{ overview?.clients?.active || 0 }}</span> active
            </div>
          </CCardBody>
        </CCard>
      </CCol>
    </CRow>
  </div>
</template>
