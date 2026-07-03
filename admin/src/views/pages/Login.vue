<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminAuthStore } from '@/stores/adminAuth'

const router = useRouter()
const authStore = useAdminAuthStore()

const email = ref('')
const password = ref('')
const errorMessage = ref('')
const isLoading = ref(false)

onMounted(() => {
  if (authStore.isAuthenticated) {
    router.push('/dashboard')
  }
})

async function handleLogin() {
  errorMessage.value = ''
  isLoading.value = true
  const result = await authStore.login({ email: email.value, password: password.value })
  isLoading.value = false
  if (result.success) {
    router.push('/dashboard')
  } else {
    errorMessage.value = result.error
  }
}
</script>

<template>
  <div class="bg-body-tertiary min-vh-100 d-flex flex-row align-items-center">
    <CContainer>
      <CRow class="justify-content-center">
        <CCol :md="6" :lg="5" :xl="4">
          <CCard class="p-4">
            <CCardBody>
              <CForm @submit.prevent="handleLogin">
                <div class="text-center mb-4">
                  <h1 class="text-primary fw-bold">PurpleOps</h1>
                  <p class="text-body-secondary">Admin Panel</p>
                </div>
                <h2 class="mb-3">Login</h2>
                <CAlert v-if="errorMessage" color="danger">{{ errorMessage }}</CAlert>
                <CInputGroup class="mb-3">
                  <CInputGroupText><CIcon icon="cil-user" /></CInputGroupText>
                  <CFormInput v-model="email" type="email" placeholder="Email" required data-testid="login-email" />
                </CInputGroup>
                <CInputGroup class="mb-4">
                  <CInputGroupText><CIcon icon="cil-lock-locked" /></CInputGroupText>
                  <CFormInput v-model="password" type="password" placeholder="Password" required data-testid="login-password" />
                </CInputGroup>
                <CButton color="primary" class="w-100" type="submit" :disabled="isLoading" data-testid="login-button">
                  <CSpinner v-if="isLoading" size="sm" class="me-2" />{{ isLoading ? 'Logging in...' : 'Login' }}
                </CButton>
              </CForm>
            </CCardBody>
          </CCard>
        </CCol>
      </CRow>
    </CContainer>
  </div>
</template>
