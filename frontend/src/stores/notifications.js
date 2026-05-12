import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api' // (import.meta.env.VITE_API_URL || 'http://localhost:8001/api').replace(/\/$/, '')

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref([])
  const unreadCount = ref(0)
  const isLoading = ref(false)
  const websocket = ref(null)
  const isConnected = ref(false)

  function getAuthHeaders() {
    const token = localStorage.getItem('token')
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  async function fetchNotifications(unreadOnly = false) {
    isLoading.value = true
    try {
      const response = await axios.get(`${API_BASE}/notifications/`, {
        params: { unread_only: unreadOnly },
        headers: getAuthHeaders()
      })
      notifications.value = response.data.notifications
      unreadCount.value = response.data.unreadCount
      return response.data
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
    } finally {
      isLoading.value = false
    }
  }

  async function markAsRead(notificationId) {
    try {
      await axios.put(`${API_BASE}/notifications/${notificationId}/read`, {}, {
        headers: getAuthHeaders()
      })
      const notification = notifications.value.find(n => n.id === notificationId)
      if (notification && !notification.read) {
        notification.read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    } catch (error) {
      console.error('Failed to mark notification as read:', error)
    }
  }

  async function markAllAsRead() {
    try {
      await axios.put(`${API_BASE}/notifications/mark-all-read`, {}, {
        headers: getAuthHeaders()
      })
      notifications.value.forEach(n => n.read = true)
      unreadCount.value = 0
    } catch (error) {
      console.error('Failed to mark all as read:', error)
    }
  }

  async function deleteNotification(notificationId) {
    try {
      await axios.delete(`${API_BASE}/notifications/${notificationId}`, {
        headers: getAuthHeaders()
      })
      const index = notifications.value.findIndex(n => n.id === notificationId)
      if (index !== -1) {
        if (!notifications.value[index].read) {
          unreadCount.value = Math.max(0, unreadCount.value - 1)
        }
        notifications.value.splice(index, 1)
      }
    } catch (error) {
      console.error('Failed to delete notification:', error)
    }
  }

  async function clearAll() {
    try {
      await axios.delete(`${API_BASE}/notifications/`, {
        headers: getAuthHeaders()
      })
      notifications.value = []
      unreadCount.value = 0
    } catch (error) {
      console.error('Failed to clear notifications:', error)
    }
  }

  // WebSocket connection for real-time notifications
  function connectWebSocket(userId) {
    if (websocket.value?.readyState === WebSocket.OPEN) {
      return // Already connected
    }

    const wsUrl = API_BASE.replace('http', 'ws').replace('/api', '') + `/api/notifications/ws/${userId}`

    try {
      websocket.value = new WebSocket(wsUrl)

      websocket.value.onopen = () => {
        isConnected.value = true
        console.log('WebSocket connected')
      }

      websocket.value.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'notification') {
          // Add new notification to the top
          notifications.value.unshift(data.data)
          if (!data.data.read) {
            unreadCount.value++
          }
          // Trigger browser notification if supported
          showBrowserNotification(data.data)
        }
      }

      websocket.value.onclose = () => {
        isConnected.value = false
        console.log('WebSocket disconnected')
        // Attempt reconnection after 5 seconds
        setTimeout(() => {
          if (userId) connectWebSocket(userId)
        }, 5000)
      }

      websocket.value.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
    }
  }

  function disconnectWebSocket() {
    if (websocket.value) {
      websocket.value.close()
      websocket.value = null
      isConnected.value = false
    }
  }

  function showBrowserNotification(notification) {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(notification.title, {
        body: notification.message,
        icon: '/favicon.ico',
        tag: notification.id
      })
    }
  }

  async function requestBrowserNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
      await Notification.requestPermission()
    }
  }

  // Add a local notification (for immediate UI feedback)
  function addNotification(notification) {
    const newNotification = {
      id: `local-${Date.now()}`,
      ...notification,
      read: false,
      createdAt: new Date().toISOString()
    }
    notifications.value.unshift(newNotification)
    unreadCount.value++
  }

  const hasUnread = computed(() => unreadCount.value > 0)
  const recentNotifications = computed(() => notifications.value.slice(0, 5))

  return {
    notifications,
    unreadCount,
    isLoading,
    isConnected,
    hasUnread,
    recentNotifications,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    clearAll,
    connectWebSocket,
    disconnectWebSocket,
    requestBrowserNotificationPermission,
    addNotification
  }
})
