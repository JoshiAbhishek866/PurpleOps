import { h, resolveComponent } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import DefaultLayout from '@/layouts/DefaultLayout'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: DefaultLayout,
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Dashboard.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/content/client-dashboard',
        name: 'ClientDashboard',
        component: () => import('@/views/admin/content/ClientDashboard.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/content/website',
        name: 'WebsiteContent',
        component: () => import('@/views/admin/content/WebsiteContent.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/content/blog',
        name: 'BlogPosts',
        component: () => import('@/views/admin/content/BlogPosts.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/content/seo',
        name: 'SEOManagement',
        component: () => import('@/views/SEOManagement.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/content/pricing',
        name: 'PricingEditor',
        component: () => import('@/views/PricingEditor.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/business/demo-requests',
        name: 'DemoRequests',
        component: () => import('@/views/admin/business/DemoRequests.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/business/clients',
        name: 'Clients',
        component: () => import('@/views/admin/business/Clients.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/admin/users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/users/AdminUsers.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: '/admin/settings',
        name: 'Settings',
        component: () => import('@/views/admin/users/Settings.vue'),
        meta: { requiresAuth: true },
      },
    ],
  },
  {
    path: '/pages',
    redirect: '/pages/404',
    name: 'Pages',
    component: {
      render() {
        return h(resolveComponent('router-view'))
      },
    },
    children: [
      { path: '404', name: 'Page404', component: () => import('@/views/pages/Page404') },
      { path: '500', name: 'Page500', component: () => import('@/views/pages/Page500') },
      {
        path: 'login',
        name: 'Login',
        component: () => import('@/views/pages/Login'),
        meta: { guest: true },
      },
      {
        path: 'register',
        name: 'Register',
        component: () => import('@/views/pages/Register'),
        meta: { guest: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('adminToken')
  const isAuthenticated = !!token
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/pages/login')
  } else if (to.meta.guest && isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
