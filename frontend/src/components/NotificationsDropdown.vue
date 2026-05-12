<template>
  <div class="notifications-dropdown" ref="dropdownRef">
    <button 
      class="notification-bell" 
      @click="toggleDropdown"
      :class="{ 'has-unread': notificationsStore.hasUnread }"
      data-testid="notification-bell"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="bell-icon">
        <path fill-rule="evenodd" d="M5.25 9a6.75 6.75 0 0113.5 0v.75c0 2.123.8 4.057 2.118 5.52a.75.75 0 01-.297 1.206c-1.544.57-3.16.99-4.831 1.243a3.75 3.75 0 11-7.48 0 24.585 24.585 0 01-4.831-1.244.75.75 0 01-.298-1.205A8.217 8.217 0 005.25 9.75V9zm4.502 8.9a2.25 2.25 0 104.496 0 25.057 25.057 0 01-4.496 0z" clip-rule="evenodd" />
      </svg>
      <span v-if="notificationsStore.unreadCount > 0" class="badge">
        {{ notificationsStore.unreadCount > 99 ? '99+' : notificationsStore.unreadCount }}
      </span>
    </button>

    <transition name="dropdown">
      <div v-if="isOpen" class="dropdown-panel glass" data-testid="notifications-panel">
        <div class="dropdown-header">
          <h3>Notifications</h3>
          <div class="header-actions">
            <button 
              v-if="notificationsStore.hasUnread"
              @click="notificationsStore.markAllAsRead()"
              class="mark-all-btn"
            >
              Mark all read
            </button>
          </div>
        </div>

        <div class="dropdown-body">
          <div v-if="notificationsStore.isLoading" class="loading-state">
            <div class="loading-spinner"></div>
          </div>
          
          <div v-else-if="notificationsStore.notifications.length === 0" class="empty-state">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="empty-icon">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
            </svg>
            <p>No notifications yet</p>
          </div>

          <div v-else class="notifications-list">
            <div 
              v-for="notification in notificationsStore.notifications" 
              :key="notification.id"
              class="notification-item"
              :class="{ 'unread': !notification.read, [notification.type]: true }"
              @click="handleNotificationClick(notification)"
            >
              <div class="notification-icon">
                <component :is="getNotificationIcon(notification.type)" />
              </div>
              <div class="notification-content">
                <p class="notification-title">{{ notification.title }}</p>
                <p class="notification-message">{{ notification.message }}</p>
                <span class="notification-time">{{ formatTime(notification.createdAt) }}</span>
              </div>
              <button 
                @click.stop="notificationsStore.deleteNotification(notification.id)"
                class="delete-btn"
                aria-label="Delete notification"
              >
                ×
              </button>
            </div>
          </div>
        </div>

        <div v-if="notificationsStore.notifications.length > 0" class="dropdown-footer">
          <button @click="notificationsStore.clearAll()" class="clear-all-btn">
            Clear all
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, h } from 'vue'
import { useNotificationsStore } from '@/stores/notifications'
import { useAuthStore } from '@/stores/auth'

const notificationsStore = useNotificationsStore()
const authStore = useAuthStore()

const isOpen = ref(false)
const dropdownRef = ref(null)

// Notification type icons as render functions
const icons = {
  info: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor' }, [
    h('path', { 'fill-rule': 'evenodd', d: 'M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm8.706-1.442c1.146-.573 2.437.463 2.126 1.706l-.709 2.836.042-.02a.75.75 0 01.67 1.34l-.04.022c-1.147.573-2.438-.463-2.127-1.706l.71-2.836-.042.02a.75.75 0 11-.671-1.34l.041-.022zM12 9a.75.75 0 100-1.5.75.75 0 000 1.5z', 'clip-rule': 'evenodd' })
  ]),
  success: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor' }, [
    h('path', { 'fill-rule': 'evenodd', d: 'M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z', 'clip-rule': 'evenodd' })
  ]),
  warning: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor' }, [
    h('path', { 'fill-rule': 'evenodd', d: 'M9.401 3.003c1.155-2 4.043-2 5.197 0l7.355 12.748c1.154 2-.29 4.5-2.599 4.5H4.645c-2.309 0-3.752-2.5-2.598-4.5L9.4 3.003zM12 8.25a.75.75 0 01.75.75v3.75a.75.75 0 01-1.5 0V9a.75.75 0 01.75-.75zm0 8.25a.75.75 0 100-1.5.75.75 0 000 1.5z', 'clip-rule': 'evenodd' })
  ]),
  error: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor' }, [
    h('path', { 'fill-rule': 'evenodd', d: 'M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25zm-1.72 6.97a.75.75 0 10-1.06 1.06L10.94 12l-1.72 1.72a.75.75 0 101.06 1.06L12 13.06l1.72 1.72a.75.75 0 101.06-1.06L13.06 12l1.72-1.72a.75.75 0 10-1.06-1.06L12 10.94l-1.72-1.72z', 'clip-rule': 'evenodd' })
  ]),
  security: () => h('svg', { xmlns: 'http://www.w3.org/2000/svg', viewBox: '0 0 24 24', fill: 'currentColor' }, [
    h('path', { 'fill-rule': 'evenodd', d: 'M12.516 2.17a.75.75 0 00-1.032 0 11.209 11.209 0 01-7.877 3.08.75.75 0 00-.722.515A12.74 12.74 0 002.25 9.75c0 5.942 4.064 10.933 9.563 12.348a.749.749 0 00.374 0c5.499-1.415 9.563-6.406 9.563-12.348 0-1.39-.223-2.73-.635-3.985a.75.75 0 00-.722-.516l-.143.001c-2.996 0-5.717-1.17-7.734-3.08zm3.094 8.016a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z', 'clip-rule': 'evenodd' })
  ])
}

function getNotificationIcon(type) {
  return icons[type] || icons.info
}

function toggleDropdown() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    notificationsStore.fetchNotifications()
  }
}

function handleNotificationClick(notification) {
  if (!notification.read) {
    notificationsStore.markAsRead(notification.id)
  }
  if (notification.link) {
    window.location.href = notification.link
  }
}

function formatTime(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

function handleClickOutside(event) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  
  // Connect WebSocket if authenticated
  if (authStore.user?.id) {
    notificationsStore.connectWebSocket(authStore.user.id)
    notificationsStore.requestBrowserNotificationPermission()
  }
  
  // Fetch initial notifications
  notificationsStore.fetchNotifications()
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  notificationsStore.disconnectWebSocket()
})
</script>

<style scoped>
.notifications-dropdown {
  position: relative;
}

.notification-bell {
  position: relative;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
}

.notification-bell:hover {
  background: rgba(255, 255, 255, 0.1);
}

.bell-icon {
  width: 24px;
  height: 24px;
  color: rgba(255, 255, 255, 0.8);
}

.notification-bell.has-unread .bell-icon {
  animation: bell-ring 0.5s ease-in-out;
}

@keyframes bell-ring {
  0%, 100% { transform: rotate(0); }
  25% { transform: rotate(15deg); }
  50% { transform: rotate(-15deg); }
  75% { transform: rotate(10deg); }
}

.badge {
  position: absolute;
  top: 0;
  right: 0;
  background: #ef4444;
  color: white;
  font-size: 0.65rem;
  font-weight: 600;
  padding: 0.1rem 0.35rem;
  border-radius: 9999px;
  min-width: 18px;
  text-align: center;
}

.dropdown-panel {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  width: 360px;
  max-height: 480px;
  background: rgba(30, 30, 40, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.75rem;
  overflow: hidden;
  z-index: 1000;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.dropdown-header h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.mark-all-btn {
  background: transparent;
  border: none;
  color: #6366f1;
  font-size: 0.85rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  transition: background 0.2s ease;
}

.mark-all-btn:hover {
  background: rgba(99, 102, 241, 0.1);
}

.dropdown-body {
  max-height: 360px;
  overflow-y: auto;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: rgba(255, 255, 255, 0.5);
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 0.5rem;
  opacity: 0.5;
}

.notifications-list {
  padding: 0.5rem 0;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background 0.2s ease;
  position: relative;
}

.notification-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.notification-item.unread {
  background: rgba(99, 102, 241, 0.05);
}

.notification-item.unread::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: #6366f1;
}

.notification-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notification-icon svg {
  width: 18px;
  height: 18px;
}

.notification-item.info .notification-icon {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.notification-item.success .notification-icon {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.notification-item.warning .notification-icon {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.notification-item.error .notification-icon {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.notification-item.security .notification-icon {
  background: rgba(139, 92, 246, 0.2);
  color: #8b5cf6;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-size: 0.9rem;
  font-weight: 500;
  color: #fff;
  margin: 0 0 0.25rem;
}

.notification-message {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 0.25rem;
  line-height: 1.4;
}

.notification-time {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.delete-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.25rem;
  opacity: 0;
  transition: all 0.2s ease;
}

.notification-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.dropdown-footer {
  padding: 0.75rem 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
}

.clear-all-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
  cursor: pointer;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
}

.clear-all-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

/* Dropdown animation */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
