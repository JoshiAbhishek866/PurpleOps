<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminAuthStore } from '@/stores/adminAuth'

const router = useRouter()
const authStore = useAdminAuthStore()
const admin = computed(() => authStore.admin)
const initials = computed(() => admin.value ? `${admin.value.firstName?.[0] || ''}${admin.value.lastName?.[0] || ''}`.toUpperCase() : 'AD')

function goToSettings() { router.push('/admin/settings') }
function logout() { authStore.logout(); router.push('/pages/login') }
</script>

<template>
  <CDropdown placement="bottom-end" variant="nav-item">
    <CDropdownToggle class="py-0 pe-0" :caret="false">
      <CAvatar :src="admin?.avatar" size="md" :color="admin?.avatar ? undefined : 'primary'" text-color="white">{{ initials }}</CAvatar>
    </CDropdownToggle>
    <CDropdownMenu class="pt-0">
      <CDropdownHeader component="h6" class="bg-body-secondary text-body-secondary fw-semibold mb-2 rounded-top">{{ admin?.firstName }} {{ admin?.lastName }}</CDropdownHeader>
      <CDropdownItem class="text-muted small" disabled>{{ admin?.email }}</CDropdownItem>
      <CDropdownItem class="text-muted small" disabled><CBadge :color="admin?.role === 'super_admin' ? 'danger' : admin?.role === 'admin' ? 'warning' : 'info'">{{ admin?.role }}</CBadge></CDropdownItem>
      <CDropdownDivider />
      <CDropdownItem @click="goToSettings" style="cursor: pointer;"><CIcon icon="cil-settings" /> Settings</CDropdownItem>
      <CDropdownDivider />
      <CDropdownItem @click="logout" style="cursor: pointer;" data-testid="logout-btn"><CIcon icon="cil-lock-locked" /> Logout</CDropdownItem>
    </CDropdownMenu>
  </CDropdown>
</template>
