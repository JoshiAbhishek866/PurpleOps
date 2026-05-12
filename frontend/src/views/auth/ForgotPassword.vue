<template>
  <div class="forgot-password-page">
    <DynamicSEO page="forgot-password" />
    <div class="auth-container glass">
      <div class="auth-header">
        <h1 class="heading-luxury">Reset Password</h1>
        <p class="auth-subtitle">Enter your email to receive a reset link</p>
      </div>

      <!-- Success State -->
      <div
        v-if="isSuccess"
        class="success-message"
        data-testid="success-message"
      >
        <div class="success-icon">✓</div>
        <h2>Check Your Email</h2>
        <p>
          If an account exists with {{ email }}, we've sent a password reset
          link.
        </p>
        <p class="text-muted mt-2">The link will expire in 1 hour.</p>
        <router-link to="/auth/login" class="back-link"
          >Back to Login</router-link
        >
      </div>

      <!-- Form State -->
      <form
        v-else
        @submit.prevent="handleSubmit"
        class="auth-form"
        data-testid="forgot-password-form"
      >
        <div class="form-group">
          <label for="email">Email Address</label>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="Enter your email"
            required
            :disabled="isLoading"
            data-testid="email-input"
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
          {{ isLoading ? "Sending..." : "Send Reset Link" }}
        </button>

        <div class="auth-links">
          <router-link to="/auth/login">Back to Login</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";
import DynamicSEO from "@/components/DynamicSEO.vue";

const API_BASE = (
  import.meta.env.VITE_API_URL || "http://localhost:8000/api"
).replace(/\/$/, "");

const email = ref("");
const isLoading = ref(false);
const isSuccess = ref(false);
const error = ref("");

async function handleSubmit() {
  if (!email.value) {
    error.value = "Please enter your email address";
    return;
  }

  isLoading.value = true;
  error.value = "";

  try {
    await axios.post(`${API_BASE}/auth/forgot-password`, {
      email: email.value,
    });
    isSuccess.value = true;
  } catch (err) {
    // Always show success to prevent email enumeration
    isSuccess.value = true;
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
.forgot-password-page {
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

.form-group input::placeholder {
  color: rgba(255, 255, 255, 0.4);
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

.back-link {
  display: inline-block;
  margin-top: 1.5rem;
  color: #6366f1;
  text-decoration: none;
  font-weight: 500;
}

.back-link:hover {
  text-decoration: underline;
}

.auth-links {
  margin-top: 1.5rem;
  text-align: center;
}

.auth-links a {
  color: #6366f1;
  text-decoration: none;
  font-size: 0.9rem;
}

.auth-links a:hover {
  text-decoration: underline;
}

.text-muted {
  color: rgba(255, 255, 255, 0.5) !important;
}

.mt-2 {
  margin-top: 0.5rem;
}
</style>
