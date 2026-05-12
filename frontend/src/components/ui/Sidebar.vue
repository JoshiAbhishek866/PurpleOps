<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <div class="logo-wrapper">
        <img src="/logo1.png" alt="Sentinel AI Logo" class="logo-icon" />
        <transition name="fade">
          <span v-if="!isCollapsed" class="logo-text">Sentinel AI</span>
        </transition>
      </div>
      <button
        @click="toggleCollapse"
        class="collapse-btn"
        :title="isCollapsed ? 'Expand' : 'Collapse'"
      >
        <svg
          v-if="isCollapsed"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          class="icon-sm"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
          />
        </svg>
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          class="icon-sm"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>

    <nav class="sidebar-nav">
      <div class="nav-section">
        <div v-if="!isCollapsed" class="nav-section-title">Main</div>
        <ul class="nav-list">
          <li v-for="item in mainNavItems" :key="item.name">
            <router-link
              :to="item.path"
              class="nav-item"
              :class="{ active: $route.path === item.path }"
              :title="isCollapsed ? item.name : ''"
            >
              <component :is="item.icon" class="nav-icon" />
              <transition name="fade">
                <span v-if="!isCollapsed" class="nav-text">{{
                  item.name
                }}</span>
              </transition>
            </router-link>
          </li>
        </ul>
      </div>

      <div class="nav-section">
        <div v-if="!isCollapsed" class="nav-section-title">Analytics</div>
        <ul class="nav-list">
          <li v-for="item in analyticsNavItems" :key="item.name">
            <router-link
              :to="item.path"
              class="nav-item"
              :class="{ active: $route.path === item.path }"
              :title="isCollapsed ? item.name : ''"
            >
              <component :is="item.icon" class="nav-icon" />
              <transition name="fade">
                <span v-if="!isCollapsed" class="nav-text">{{
                  item.name
                }}</span>
              </transition>
            </router-link>
          </li>
        </ul>
      </div>
    </nav>

    <div class="sidebar-footer">
      <div class="user-profile">
        <div class="user-avatar">{{ userInitials }}</div>
        <transition name="fade">
          <div v-if="!isCollapsed" class="user-info">
            <div class="user-name">
              {{ user?.firstName }} {{ user?.lastName }}
            </div>
            <div class="user-role">{{ user?.role }}</div>
          </div>
        </transition>
      </div>
      <div class="sidebar-actions">
        <button
          @click="toggleTheme"
          class="action-btn"
          :title="isDark ? 'Light Mode' : 'Dark Mode'"
        >
          <component :is="isDark ? SunIcon : MoonIcon" class="icon-sm" />
        </button>
        <button @click="handleLogout" class="action-btn logout" title="Logout">
          <ArrowRightOnRectangleIcon class="icon-sm" />
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useThemeStore } from "@/stores/theme";
import {
  HomeIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  HeartIcon,
  DocumentTextIcon,
  CogIcon,
  SunIcon,
  MoonIcon,
  ArrowRightOnRectangleIcon,
} from "@heroicons/vue/24/outline";

const router = useRouter();
const authStore = useAuthStore();
const themeStore = useThemeStore();

const isCollapsed = ref(false);
const isDark = computed(() => themeStore.isDark);
const user = computed(() => authStore.user);

const userInitials = computed(() => {
  if (!user.value) return "U";
  return `${user.value.firstName?.[0] || ""}${user.value.lastName?.[0] || ""}`.toUpperCase();
});

const mainNavItems = [
  { name: "Overview", path: "/dashboard/overview", icon: HomeIcon },
  {
    name: "Attack Insights",
    path: "/dashboard/attack-insights",
    icon: ShieldCheckIcon,
  },
  {
    name: "Defense Metrics",
    path: "/dashboard/defense-metrics",
    icon: ChartBarIcon,
  },
  { name: "System Health", path: "/dashboard/system-health", icon: HeartIcon },
];

const analyticsNavItems = [
  {
    name: "Activity Logs",
    path: "/dashboard/activity-logs",
    icon: DocumentTextIcon,
  },
  { name: "Settings", path: "/dashboard/settings", icon: CogIcon },
];

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value;
}
function toggleTheme() {
  themeStore.toggleTheme();
}
async function handleLogout() {
  authStore.logout();
  await router.push("/");
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  width: 260px;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  z-index: 50;
}
.sidebar.collapsed {
  width: 80px;
}

/* Header */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  min-height: 70px;
}
.logo-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.logo-icon {
  width: 5rem;
  height: 3.125rem;
  object-fit: contain;
  flex-shrink: 0;
}
.logo-text {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
}

.collapse-btn {
  padding: 0.5rem;
  border-radius: 0.5rem;
  color: #6b7280;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
}
.collapse-btn:hover {
  background: #f3f4f6;
}

/* Nav */
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 0;
}
.nav-section {
  margin-bottom: 1.5rem;
}
.nav-section-title {
  padding: 0.5rem 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.nav-list {
  padding: 0 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  border-radius: 0.5rem;
  color: #374151;
  text-decoration: none;
  transition:
    background 0.2s,
    color 0.2s;
  position: relative;
}
.nav-item:hover {
  background: #f3f4f6;
}
.nav-item.active {
  background: #673ee6;
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(103, 62, 230, 0.2);
}

.nav-icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
}
.nav-text {
  flex: 1;
  font-size: 0.875rem;
  font-weight: 500;
}

/* Footer */
.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 0.5rem;
  background: #f9fafb;
}
.user-avatar {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background: #673ee6;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.875rem;
  flex-shrink: 0;
}
.user-info {
  flex: 1;
  min-width: 0;
}
.user-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.user-role {
  font-size: 0.75rem;
  color: #6b7280;
  text-transform: capitalize;
}

.sidebar-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  color: #374151;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
}
.action-btn:hover {
  background: #f3f4f6;
}
.action-btn.logout {
  color: #ef4444;
}
.action-btn.logout:hover {
  background: #fef2f2;
}

/* Collapsed overrides */
.sidebar.collapsed .logo-text,
.sidebar.collapsed .nav-text,
.sidebar.collapsed .nav-section-title,
.sidebar.collapsed .user-info {
  display: none;
}
.sidebar.collapsed .nav-item {
  justify-content: center;
}
.sidebar.collapsed .user-profile {
  justify-content: center;
  padding: 0.5rem;
}
.sidebar.collapsed .sidebar-actions {
  flex-direction: column;
  gap: 0.25rem;
}
.sidebar.collapsed .action-btn {
  padding: 0.5rem;
}

/* Scrollbar */
.sidebar-nav::-webkit-scrollbar {
  width: 6px;
}
.sidebar-nav::-webkit-scrollbar-track {
  background: transparent;
}
.sidebar-nav::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}
.sidebar-nav::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
