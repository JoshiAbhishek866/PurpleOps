<template>
  <div class="reset-password-page">
    <DynamicSEO page="reset-password" />
    <div class="auth-container glass">
      <div class="auth-header">
        <h1 class="heading-luxury">Set New Password</h1>
        <p class="auth-subtitle">Enter your new password below</p>
      </div>

      <!-- Invalid Token State -->
      <div v-if="tokenError" class="error-state" data-testid="token-error">
        <div class="error-icon">✕</div>
        <h2>Invalid or Expired Link</h2>
        <p>This password reset link is invalid or has expired.</p>
        <router-link to="/auth/forgot-password" class="action-link"
          >Request New Link</router-link
        >
      </div>

      <!-- Success State -->
      <div
        v-else-if="isSuccess"
        class="success-message"
        data-testid="success-message"
      >
        <div class="success-icon">✓</div>
        <h2>Password Reset Successfully</h2>
        <p>
          Your password has been changed. You can now log in with your new
          password.
        </p>
        <router-link to="/auth/login" class="action-link"
          >Go to Login</router-link
        >
      </div>

      <!-- Form State -->
      <form
        v-else
        @submit.prevent="handleSubmit"
        class="auth-form"
        data-testid="reset-password-form"
      >
        <div class="form-group">
          <label for="password">New Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="Enter new password"
            required
            minlength="8"
            :disabled="isLoading"
            data-testid="password-input"
          />
          <small class="field-hint">Minimum 8 characters</small>
        </div>

        <div class="form-group">
          <label for="confirmPassword">Confirm Password</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            placeholder="Confirm new password"
            required
            :disabled="isLoading"
            data-testid="confirm-password-input"
          />
        </div>

        <div v-if="error" class="error-message" data-testid="error-message">
          {{ error }}
        </div>

        <button
          type="submit"
          class="submit-btn"
          :disabled="isLoading"
          data-testid="submit-btn"
        >
          <span v-if="isLoading" class="loading-spinner"></span>
          {{ isLoading ? "Resetting..." : "Reset Password" }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import axios from "axios";
import DynamicSEO from "@/components/DynamicSEO.vue";

const API_BASE = (
  import.meta.env.VITE_API_URL || "http://localhost:8000/api"
).replace(/\/$/, "");

const route = useRoute();
const router = useRouter();

const password = ref("");
const confirmPassword = ref("");
const isLoading = ref(false);
const isSuccess = ref(false);
const error = ref("");
const tokenError = ref(false);
const token = ref("");

onMounted(async () => {
  token.value = route.query.token;

  if (!token.value) {
    tokenError.value = true;
    return;
  }

  // Verify token is valid
  try {
    await axios.post(`${API_BASE}/auth/verify-reset-token`, {
      token: token.value,
    });
  } catch (err) {
    tokenError.value = true;
  }
});

async function handleSubmit() {
  error.value = "";

  if (password.value !== confirmPassword.value) {
    error.value = "Passwords do not match";
    return;
  }

  if (password.value.length < 8) {
    error.value = "Password must be at least 8 characters";
    return;
  }

  isLoading.value = true;

  try {
    await axios.post(`${API_BASE}/auth/reset-password`, {
      token: token.value,
      newPassword: password.value,
    });
    isSuccess.value = true;
  } catch (err) {
    error.value =
      err.response?.data?.detail ||
      "Failed to reset password. Please try again.";
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
.reset-password-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
}

.auth-container {
  width: 100%;
  max-width: 420px;
  padding: 2.5rem;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.auth-header {
  text-align: center;
  margin-bottom: 2rem;
}

.heading-luxury {
  font-size: 1.75rem;
  font-weight: 700;
  color: #fff;
  margin-bottom: 0.5rem;
}

.auth-subtitle {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.95rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.form-group input {
  width: 100%;
  padding: 0.875rem 1rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.form-group input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
}

.field-hint {
  display: block;
  margin-top: 0.25rem;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.8rem;
}

.submit-btn {
  width: 100%;
  padding: 0.875rem;
  border-radius: 0.5rem;
  border: none;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-message {
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  border-radius: 0.5rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
  font-size: 0.9rem;
}

.error-state {
  text-align: center;
  padding: 1rem 0;
}

.error-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: rgba(239, 68, 68, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
  font-size: 1.5rem;
  color: #ef4444;
}

.error-state h2 {
  color: #fff;
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
}

.error-state p {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.95rem;
}

.success-message {
  text-align: center;
  padding: 1rem 0;
}

.success-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
  font-size: 1.5rem;
  color: #fff;
}

.success-message h2 {
  color: #fff;
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
}

.success-message p {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.95rem;
}

.action-link {
  display: inline-block;
  margin-top: 1.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
}

.action-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
}
</style>
