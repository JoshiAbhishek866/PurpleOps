<template>
  <div class="login-page">
    <DynamicSEO page="login" />
    <div class="login-container">
      <!-- Logo and Header -->
      <div class="login-header" data-testid="login-header">
        <div class="logo-container">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M12 2L2 7V12C2 17 6 21 12 22C18 21 22 17 22 12V7L12 2Z"
              />
            </svg>
          </div>
          <h1 class="logo-text">PurpleOps</h1>
        </div>
        <p class="login-subtitle">Access your security dashboard</p>
      </div>

      <!-- Login Form -->
      <div class="login-form-container glass" data-testid="login-form">
        <form @submit.prevent="handleLogin" class="login-form">
          <h2 class="form-title">Company Login</h2>
          <p class="form-description">
            This is a restricted access portal for authorized company personnel
            only.
          </p>

          <!-- Error Display -->
          <div v-if="error" class="error-banner" data-testid="error-message">
            <ExclamationTriangleIcon class="error-icon" />
            <span>{{ error }}</span>
          </div>

          <div class="form-group">
            <label for="email" class="form-label">Email Address</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              autocomplete="email"
              class="form-input"
              :class="{ error: errors.email }"
              data-testid="email-input"
              placeholder="Enter your company email"
            />
            <span v-if="errors.email" class="error-text">{{
              errors.email
            }}</span>
          </div>

          <div class="form-group">
            <label for="password" class="form-label">Password</label>
            <div class="password-input-container">
              <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                required
                autocomplete="current-password"
                class="form-input"
                :class="{ error: errors.password }"
                data-testid="password-input"
                placeholder="Enter your password"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="password-toggle"
                data-testid="password-toggle"
              >
                <component
                  :is="showPassword ? EyeSlashIcon : EyeIcon"
                  class="icon-sm"
                />
              </button>
            </div>
            <span v-if="errors.password" class="error-text">{{
              errors.password
            }}</span>
          </div>

          <div class="form-options">
            <label class="checkbox-container">
              <input
                v-model="form.rememberMe"
                type="checkbox"
                data-testid="remember-me-checkbox"
              />
              <span class="checkmark"></span>
              Remember me
            </label>

            <router-link
              to="/auth/forgot-password"
              class="forgot-password-link"
              data-testid="forgot-password-link"
            >
              Forgot password?
            </router-link>
          </div>

          <LuxuryButton
            type="submit"
            size="lg"
            :loading="loading"
            :disabled="!isFormValid"
            class="btn-full"
            data-testid="login-submit-button"
          >
            Sign In
          </LuxuryButton>

          <!-- Registration Link -->
          <div class="register-section">
            <p class="register-text">
              Don't have an account?
              <router-link
                to="/auth/register"
                class="register-link"
                data-testid="register-link"
              >
                Request Access
              </router-link>
            </p>
          </div>
        </form>
      </div>

      <!-- Security Notice -->
      <div class="security-notice glass">
        <ShieldCheckIcon class="notice-icon" />
        <div class="notice-content">
          <h3 class="notice-title">Secure Access</h3>
          <p class="notice-description">
            All login attempts are monitored and logged. Unauthorized access
            attempts will be reported to security personnel.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import DynamicSEO from "@/components/DynamicSEO.vue";
import LuxuryButton from "@/components/LuxuryButton.vue";
import {
  EyeIcon,
  EyeSlashIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
} from "@heroicons/vue/24/outline";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const form = ref({
  email: "",
  password: "",
  rememberMe: false,
});

const errors = ref({});
const showPassword = ref(false);
const loading = ref(false);
const error = ref("");

const isFormValid = computed(() => {
  return (
    form.value.email && form.value.password && !Object.keys(errors.value).length
  );
});

function validateForm() {
  errors.value = {};

  if (!form.value.email.trim()) {
    errors.value.email = "Email is required";
  } else if (!/\S+@\S+\.\S+/.test(form.value.email)) {
    errors.value.email = "Please enter a valid email address";
  }

  if (!form.value.password) {
    errors.value.password = "Password is required";
  } else if (form.value.password.length < 8) {
    errors.value.password = "Password must be at least 8 characters";
  }

  return Object.keys(errors.value).length === 0;
}

async function handleLogin() {
  if (!validateForm()) return;

  loading.value = true;
  error.value = "";

  try {
    const result = await authStore.login({
      email: form.value.email,
      password: form.value.password,
    });

    if (result.success) {
      // Redirect to intended page or dashboard
      const redirect = route.query.redirect || "/dashboard";
      await router.push(redirect);
    } else {
      error.value = result.error || "Login failed";
    }
  } catch (err) {
    error.value = "An unexpected error occurred. Please try again.";
    console.error("Login error:", err);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem 0;
  background: var(--bg-primary);
  position: relative;
}

.login-page::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: url("https://images.unsplash.com/photo-1563986768609-322da13575f3?w=1920&h=1080&fit=crop");
  background-size: cover;
  background-position: center;
  opacity: 0.05;
  z-index: 0;
}

.login-container {
  max-width: 28rem;
  width: 100%;
  margin: 0 auto;
  padding: 0 1.5rem;
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Header */
.login-header {
  text-align: center;
}

.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.logo-icon {
  width: 3rem;
  height: 3rem;
  color: #8b5cf6;
}

.logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #8b5cf6, #10b981);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-subtitle {
  font-size: 1.125rem;
  color: #d1d5db;
}

/* Form Container */
.login-form-container {
  padding: 2rem;
  border-radius: 1rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-title {
  font-size: 1.5rem;
  font-weight: 700;
  text-align: center;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
}

.form-description {
  text-align: center;
  color: #9ca3af;
  font-size: 0.875rem;
  margin-bottom: 1.5rem;
}

/* Error Banner */
.error-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1.5rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.error-icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
}

/* Form Elements */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  border: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(10px);
  color: var(--text-primary);
  transition:
    box-shadow 0.3s,
    border-color 0.3s;
}

.form-input::placeholder {
  color: #9ca3af;
}

.form-input:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.5);
  border-color: #8b5cf6;
}

.form-input.error {
  border-color: #ef4444;
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.3);
}

.error-text {
  color: #f87171;
  font-size: 0.875rem;
}

.password-input-container {
  position: relative;
}

.password-toggle {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
}
.password-toggle:hover {
  color: #d1d5db;
}

/* Form Options */
.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.checkbox-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  cursor: pointer;
  color: var(--text-secondary);
}

.checkbox-container input[type="checkbox"] {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.checkmark {
  width: 1rem;
  height: 1rem;
  border-radius: 0.25rem;
  border: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.5);
  position: relative;
  flex-shrink: 0;
}

.checkbox-container input[type="checkbox"]:checked + .checkmark {
  background: linear-gradient(135deg, #8b5cf6, #10b981);
  border-color: #8b5cf6;
}

.checkbox-container input[type="checkbox"]:checked + .checkmark::after {
  content: "";
  position: absolute;
  top: 0;
  left: 0.25rem;
  width: 0.375rem;
  height: 0.75rem;
  border-right: 2px solid #fff;
  border-bottom: 2px solid #fff;
  transform: rotate(45deg);
}

.forgot-password-link {
  font-size: 0.875rem;
  color: #a78bfa;
  text-decoration: none;
  cursor: pointer;
  transition: color 0.2s;
}
.forgot-password-link:hover {
  color: #c4b5fd;
}

/* Full-width submit button */
.btn-full {
  width: 100%;
}

/* Registration Section */
.register-section {
  text-align: center;
  padding-top: 1rem;
  border-top: 1px solid #374151;
}

.register-text {
  color: #9ca3af;
}

.register-link {
  color: #a78bfa;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}
.register-link:hover {
  color: #c4b5fd;
}

/* Security Notice */
.security-notice {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.5rem;
  border-radius: 0.75rem;
}

.notice-icon {
  width: 2rem;
  height: 2rem;
  color: #34d399;
  flex-shrink: 0;
}

.notice-content {
  flex: 1;
}

.notice-title {
  font-weight: 700;
  color: #34d399;
  margin-bottom: 0.5rem;
}

.notice-description {
  font-size: 0.875rem;
  color: #9ca3af;
  line-height: 1.625;
}

/* Responsive */
@media (max-width: 480px) {
  .login-container {
    padding: 0 1rem;
  }
  .login-form-container {
    padding: 1.5rem;
  }
}
</style>
