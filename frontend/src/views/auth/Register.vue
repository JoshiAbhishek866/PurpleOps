<template>
  <div class="register-page">
    <DynamicSEO page="register" />
    <div class="register-container">
      <!-- Logo and Header -->
      <div class="register-header" data-testid="register-header">
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
        <p class="register-subtitle">Request access to the security platform</p>
      </div>

      <!-- Registration Form -->
      <div class="register-form-container glass" data-testid="register-form">
        <form @submit.prevent="handleRegister" class="register-form">
          <h2 class="form-title">Request Company Access</h2>
          <p class="form-description">
            Please provide your details below. All registrations require
            approval from our security team.
          </p>

          <!-- Error Display -->
          <div v-if="error" class="error-banner" data-testid="error-message">
            <ExclamationTriangleIcon class="error-icon" />
            <span>{{ error }}</span>
          </div>

          <!-- Success Message -->
          <div
            v-if="registered"
            class="success-banner"
            data-testid="success-message"
          >
            <CheckCircleIcon class="success-icon" />
            <div class="success-content">
              <h3 class="success-title">Registration Submitted</h3>
              <p class="success-description">
                Your access request has been submitted successfully. Our
                security team will review your application and contact you
                within 24-48 hours.
              </p>
            </div>
          </div>

          <div v-if="!registered" class="form-fields">
            <!-- Personal Information -->
            <div class="form-row">
              <div class="form-group">
                <label for="firstName" class="form-label">First Name *</label>
                <input
                  id="firstName"
                  v-model="form.firstName"
                  type="text"
                  required
                  class="form-input"
                  :class="{ error: errors.firstName }"
                  data-testid="first-name-input"
                  placeholder="Enter your first name"
                />
                <span v-if="errors.firstName" class="error-text">{{
                  errors.firstName
                }}</span>
              </div>

              <div class="form-group">
                <label for="lastName" class="form-label">Last Name *</label>
                <input
                  id="lastName"
                  v-model="form.lastName"
                  type="text"
                  required
                  class="form-input"
                  :class="{ error: errors.lastName }"
                  data-testid="last-name-input"
                  placeholder="Enter your last name"
                />
                <span v-if="errors.lastName" class="error-text">{{
                  errors.lastName
                }}</span>
              </div>
            </div>

            <!-- Contact Information -->
            <div class="form-group">
              <label for="email" class="form-label">Email Address *</label>
              <input
                id="email"
                v-model="form.email"
                type="email"
                required
                class="form-input"
                :class="{ error: errors.email }"
                data-testid="email-input"
                placeholder="Enter your company email"
              />
              <span v-if="errors.email" class="error-text">{{
                errors.email
              }}</span>
            </div>

            <!-- Company Information -->
            <div class="form-group">
              <label for="company" class="form-label">Company Name *</label>
              <input
                id="company"
                v-model="form.company"
                type="text"
                required
                class="form-input"
                :class="{ error: errors.company }"
                data-testid="company-input"
                placeholder="Enter your company name"
              />
              <span v-if="errors.company" class="error-text">{{
                errors.company
              }}</span>
            </div>

            <!-- Role Selection -->
            <div class="form-group">
              <label for="role" class="form-label">Requested Role *</label>
              <select
                id="role"
                v-model="form.role"
                required
                class="form-input"
                data-testid="role-select"
              >
                <option value="">Select your role</option>
                <option value="viewer">
                  Viewer - Read-only access to dashboards
                </option>
                <option value="analyst">
                  Analyst - Security analysis and reporting
                </option>
                <option value="admin">
                  Admin - Full platform administration
                </option>
              </select>
              <span v-if="errors.role" class="error-text">{{
                errors.role
              }}</span>
            </div>

            <!-- Password -->
            <div class="form-group">
              <label for="password" class="form-label">Password *</label>
              <div class="password-input-container">
                <input
                  id="password"
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  required
                  class="form-input"
                  :class="{ error: errors.password }"
                  data-testid="password-input"
                  placeholder="Create a secure password"
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
              <div class="password-requirements">
                <p class="requirements-title">Password must contain:</p>
                <ul class="requirements-list">
                  <li :class="{ valid: passwordChecks.length }">
                    At least 8 characters
                  </li>
                  <li :class="{ valid: passwordChecks.uppercase }">
                    One uppercase letter
                  </li>
                  <li :class="{ valid: passwordChecks.lowercase }">
                    One lowercase letter
                  </li>
                  <li :class="{ valid: passwordChecks.number }">One number</li>
                </ul>
              </div>
              <span v-if="errors.password" class="error-text">{{
                errors.password
              }}</span>
            </div>

            <!-- Confirm Password -->
            <div class="form-group">
              <label for="confirmPassword" class="form-label"
                >Confirm Password *</label
              >
              <input
                id="confirmPassword"
                v-model="form.confirmPassword"
                type="password"
                required
                class="form-input"
                :class="{ error: errors.confirmPassword }"
                data-testid="confirm-password-input"
                placeholder="Confirm your password"
              />
              <span v-if="errors.confirmPassword" class="error-text">{{
                errors.confirmPassword
              }}</span>
            </div>

            <!-- Terms Acceptance -->
            <div class="form-group">
              <label class="checkbox-container">
                <input
                  v-model="form.acceptTerms"
                  type="checkbox"
                  required
                  data-testid="accept-terms-checkbox"
                />
                <span class="checkmark"></span>
                I agree to the
                <button type="button" class="terms-link">
                  Terms of Service
                </button>
                and
                <button type="button" class="terms-link">Privacy Policy</button>
              </label>
              <span v-if="errors.acceptTerms" class="error-text">{{
                errors.acceptTerms
              }}</span>
            </div>

            <LuxuryButton
              type="submit"
              size="lg"
              :loading="loading"
              :disabled="!isFormValid"
              class="btn-full"
              data-testid="register-submit-button"
            >
              Submit Access Request
            </LuxuryButton>
          </div>

          <!-- Login Link -->
          <div class="login-section">
            <p class="login-text">
              Already have an account?
              <router-link
                to="/auth/login"
                class="login-link"
                data-testid="login-link"
              >
                Sign In
              </router-link>
            </p>
          </div>
        </form>
      </div>

      <!-- Security Notice -->
      <div class="security-notice glass">
        <ShieldCheckIcon class="notice-icon" />
        <div class="notice-content">
          <h3 class="notice-title">Secure Registration</h3>
          <p class="notice-description">
            All access requests are reviewed by our security team. Only
            authorized personnel will be granted access to the PurpleOps platform.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import DynamicSEO from "@/components/DynamicSEO.vue";
import LuxuryButton from "@/components/LuxuryButton.vue";
import {
  EyeIcon,
  EyeSlashIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ShieldCheckIcon,
} from "@heroicons/vue/24/outline";

const router = useRouter();
const authStore = useAuthStore();

const form = ref({
  firstName: "",
  lastName: "",
  email: "",
  company: "",
  role: "",
  password: "",
  confirmPassword: "",
  acceptTerms: false,
});

const errors = ref({});
const showPassword = ref(false);
const loading = ref(false);
const error = ref("");
const registered = ref(false);

const passwordChecks = computed(() => ({
  length: form.value.password.length >= 8,
  uppercase: /[A-Z]/.test(form.value.password),
  lowercase: /[a-z]/.test(form.value.password),
  number: /\d/.test(form.value.password),
}));

const isPasswordValid = computed(() => {
  return Object.values(passwordChecks.value).every((check) => check === true);
});

const isFormValid = computed(() => {
  return (
    form.value.firstName &&
    form.value.lastName &&
    form.value.email &&
    form.value.company &&
    form.value.role &&
    isPasswordValid.value &&
    form.value.password === form.value.confirmPassword &&
    form.value.acceptTerms &&
    !Object.keys(errors.value).length
  );
});

function validateForm() {
  errors.value = {};

  if (!form.value.firstName.trim()) {
    errors.value.firstName = "First name is required";
  }

  if (!form.value.lastName.trim()) {
    errors.value.lastName = "Last name is required";
  }

  if (!form.value.email.trim()) {
    errors.value.email = "Email is required";
  } else if (!/\S+@\S+\.\S+/.test(form.value.email)) {
    errors.value.email = "Please enter a valid email address";
  }

  if (!form.value.company.trim()) {
    errors.value.company = "Company name is required";
  }

  if (!form.value.role) {
    errors.value.role = "Please select a role";
  }

  if (!isPasswordValid.value) {
    errors.value.password = "Password does not meet requirements";
  }

  if (form.value.password !== form.value.confirmPassword) {
    errors.value.confirmPassword = "Passwords do not match";
  }

  if (!form.value.acceptTerms) {
    errors.value.acceptTerms = "You must accept the terms and conditions";
  }

  return Object.keys(errors.value).length === 0;
}

async function handleRegister() {
  if (!validateForm()) return;

  loading.value = true;
  error.value = "";

  try {
    const result = await authStore.register({
      firstName: form.value.firstName,
      lastName: form.value.lastName,
      email: form.value.email,
      company: form.value.company,
      role: form.value.role,
      password: form.value.password,
    });

    if (result.success) {
      registered.value = true;
    } else {
      error.value = result.error || "Registration failed";
    }
  } catch (err) {
    error.value = "An unexpected error occurred. Please try again.";
    console.error("Registration error:", err);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem 0;
  background: var(--bg-primary);
  position: relative;
}

.register-page::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: url("https://images.unsplash.com/photo-1563986768609-322da13575f3?w=1920&h=1080&fit=crop");
  background-size: cover;
  background-position: center;
  opacity: 0.05;
  z-index: 0;
}

.register-container {
  max-width: 32rem;
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
.register-header {
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

.register-subtitle {
  font-size: 1.125rem;
  color: #d1d5db;
}

/* Form Container */
.register-form-container {
  padding: 2rem;
  border-radius: 1rem;
}

.register-form {
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

/* Messages */
.error-banner,
.success-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1.5rem;
}

.error-banner {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
}
.success-banner {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #22c55e;
}

.error-icon,
.success-icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
  margin-top: 0.125rem;
}

.success-content {
  flex: 1;
}
.success-title {
  font-weight: 700;
  margin-bottom: 0.5rem;
}
.success-description {
  font-size: 0.875rem;
  opacity: 0.9;
}

/* Form Elements */
.form-fields {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

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

/* Password Requirements */
.password-requirements {
  margin-top: 0.5rem;
  padding: 0.75rem;
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.05);
}

.requirements-title {
  font-size: 0.75rem;
  font-weight: 500;
  color: #9ca3af;
  margin-bottom: 0.5rem;
}

.requirements-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.requirements-list li {
  font-size: 0.75rem;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.requirements-list li.valid {
  color: #4ade80;
}

.requirements-list li.valid::before {
  content: "✓";
  color: #4ade80;
  font-weight: 700;
}

.requirements-list li:not(.valid)::before {
  content: "○";
  color: #6b7280;
}

/* Checkbox */
.checkbox-container {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
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
  margin-top: 0.125rem;
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

.terms-link {
  color: #a78bfa;
  text-decoration: underline;
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
}
.terms-link:hover {
  color: #c4b5fd;
}

/* Full-width submit button */
.btn-full {
  width: 100%;
}

/* Login Section */
.login-section {
  text-align: center;
  padding-top: 1rem;
  border-top: 1px solid #374151;
}

.login-text {
  color: #9ca3af;
}

.login-link {
  color: #a78bfa;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}
.login-link:hover {
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
@media (max-width: 640px) {
  .register-container {
    padding: 0 1rem;
  }
  .register-form-container {
    padding: 1.5rem;
  }
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
