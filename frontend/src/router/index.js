import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useUiStore } from "@/stores/ui";

// Public pages
import Home from "@/views/Home.vue";
import About from "@/views/About.vue";
import Blog from "@/views/Blog.vue";
import BookDemo from "@/views/BookDemo.vue";
import Pricing from "@/views/Pricing.vue";
import VulnerabilityDetail from "@/views/VulnerabilityDetail.vue";

// Auth pages
import Login from "@/views/auth/Login.vue";
import Register from "@/views/auth/Register.vue";
import ForgotPassword from "@/views/auth/ForgotPassword.vue";
import ResetPassword from "@/views/auth/ResetPassword.vue";
import VerifyEmail from "@/views/auth/VerifyEmail.vue";

// Dashboard pages
import Dashboard from "@/views/dashboard/Dashboard.vue";
import Overview from "@/views/dashboard/Overview.vue";
import AttackInsights from "@/views/dashboard/AttackInsights.vue";
import DefenseMetrics from "@/views/dashboard/DefenseMetrics.vue";
import SystemHealth from "@/views/dashboard/SystemHealth.vue";
import ActivityLogs from "@/views/dashboard/ActivityLogs.vue";
import Settings from "@/views/dashboard/Settings.vue";
import ScanResults from "@/views/dashboard/ScanResults.vue";
import ArchitectureMap from "@/views/dashboard/ArchitectureMap.vue";

const routes = [
  {
    path: "/",
    name: "Home",
    component: Home,
    meta: { public: true },
  },
  {
    path: "/about",
    name: "About",
    component: About,
    meta: { public: true },
  },
  {
    path: "/blog",
    name: "Blog",
    component: Blog,
    meta: { public: true },
  },
  {
    path: "/book-demo",
    name: "BookDemo",
    component: BookDemo,
    meta: { public: true },
  },
  {
    path: "/pricing",
    name: "Pricing",
    component: Pricing,
    meta: { public: true },
  },
  {
    path: "/vulnerability/:id",
    name: "VulnerabilityDetail",
    component: VulnerabilityDetail,
    meta: { public: true },
  },

  // Auth routes (private access - company only)
  {
    path: "/auth/login",
    name: "Login",
    component: Login,
    meta: { public: true, hideForAuth: true },
  },
  {
    path: "/auth/register",
    name: "Register",
    component: Register,
    meta: { public: true, hideForAuth: true },
  },
  {
    path: "/auth/forgot-password",
    name: "ForgotPassword",
    component: ForgotPassword,
    meta: { public: true, hideForAuth: true },
  },
  {
    path: "/auth/reset-password",
    name: "ResetPassword",
    component: ResetPassword,
    meta: { public: true },
  },
  {
    path: "/auth/verify-email",
    name: "VerifyEmail",
    component: VerifyEmail,
    meta: { public: true },
  },

  // Dashboard routes (require authentication)
  {
    path: "/dashboard",
    name: "Dashboard",
    component: Dashboard,
    meta: { requiresAuth: true },
    children: [
      {
        path: "",
        redirect: "/dashboard/overview",
      },
      {
        path: "overview",
        name: "DashboardOverview",
        component: Overview,
      },
      {
        path: "attack-insights",
        name: "AttackInsights",
        component: AttackInsights,
      },
      {
        path: "defense-metrics",
        name: "DefenseMetrics",
        component: DefenseMetrics,
      },
      {
        path: "system-health",
        name: "SystemHealth",
        component: SystemHealth,
      },
      {
        path: "activity-logs",
        name: "ActivityLogs",
        component: ActivityLogs,
      },
      {
        path: "settings",
        name: "Settings",
        component: Settings,
      },
      {
        path: "scan-results",
        name: "ScanResults",
        component: ScanResults,
      },
      {
        path: "architecture-map",
        name: "ArchitectureMap",
        component: ArchitectureMap,
      },
    ],
  },

  // Catch all route - 404
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: () => import("@/views/NotFound.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    }
    return { top: 0, behavior: "smooth" };
  },
});

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();
  const ui = useUiStore();
  ui.startLoading();

  // Check if route requires authentication
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated()) {
      ui.stopLoading();
      return next("/auth/login");
    }

    // Fetch user profile if not loaded
    if (!authStore.user) {
      await authStore.fetchProfile();
    }
  }

  // Hide auth pages for already authenticated users
  if (to.meta.hideForAuth && authStore.isAuthenticated()) {
    ui.stopLoading();
    return next("/dashboard");
  }

  next();
});

router.afterEach(() => {
  const ui = useUiStore();
  // Allow next tick so view can render, then fade loader
  setTimeout(() => ui.stopLoading(), 150);
});

export default router;
