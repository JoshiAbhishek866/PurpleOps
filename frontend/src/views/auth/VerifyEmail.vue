<template>
  <div class="verify-email-page">
    <DynamicSEO page="verify-email" />
    <div class="auth-container glass">
      <!-- Loading State -->
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner-large"></div>
        <p>Verifying your email...</p>
      </div>

      <!-- Success State -->
      <div
        v-else-if="isSuccess"
        class="success-message"
        data-testid="success-message"
      >
        <div class="success-icon">✓</div>
        <h2>Email Verified!</h2>
        <p>
          Your email has been successfully verified. You now have full access to
          all features.
        </p>
        <router-link to="/dashboard" class="action-link"
          >Go to Dashboard</router-link
        >
      </div>

      <!-- Error State -->
      <div v-else class="error-state" data-testid="error-state">
        <div class="error-icon">✕</div>
        <h2>Verification Failed</h2>
        <p>
          {{ error || "This verification link is invalid or has expired." }}
        </p>
        <div class="action-buttons">
          <button
            @click="resendVerification"
            class="action-link"
            :disabled="isResending"
          >
            {{ isResending ? "Sending..." : "Resend Verification Email" }}
          </button>
          <router-link to="/auth/login" class="secondary-link"
            >Back to Login</router-link
          >
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import axios from "axios";
import { useAuthStore } from "@/stores/auth";
import DynamicSEO from "@/components/DynamicSEO.vue";

const API_BASE = (
  import.meta.env.VITE_API_URL || "http://localhost:8000/api"
).replace(/\/$/, "");

const route = useRoute();
const authStore = useAuthStore();

const isLoading = ref(true);
const isSuccess = ref(false);
const isResending = ref(false);
const error = ref("");

onMounted(async () => {
  const token = route.query.token;

  if (!token) {
    error.value = "No verification token provided";
    isLoading.value = false;
    return;
  }

  try {
    await axios.post(`${API_BASE}/auth/verify-email`, { token });
    isSuccess.value = true;

    // Update auth store if user is logged in
    if (authStore.user) {
      authStore.user.emailVerified = true;
    }
  } catch (err) {
    error.value = err.response?.data?.detail || "Verification failed";
  } finally {
    isLoading.value = false;
  }
});

async function resendVerification() {
  if (!authStore.user?.email) {
    error.value = "Please log in to resend verification email";
    return;
  }

  isResending.value = true;

  try {
    await axios.post(`${API_BASE}/auth/send-verification`, {
      email: authStore.user.email,
    });
    alert("Verification email sent! Please check your inbox.");
  } catch (err) {
    alert("Failed to send verification email. Please try again.");
  } finally {
    isResending.value = false;
  }
}
</script>

<style scoped>
.verify-email-page {
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
  text-align: center;
}

.loading-state {
  padding: 2rem 0;
}

.loading-spinner-large {
  width: 50px;
  height: 50px;
  border: 3px solid rgba(255, 255, 255, 0.2);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1.5rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-state p {
  color: rgba(255, 255, 255, 0.7);
  font-size: 1rem;
}

.success-message,
.error-state {
  padding: 1rem 0;
}

.success-icon {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
  font-size: 2rem;
  color: #fff;
}

.error-icon {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: rgba(239, 68, 68, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
  font-size: 2rem;
  color: #ef4444;
}

h2 {
  color: #fff;
  font-size: 1.5rem;
  margin-bottom: 0.75rem;
}

p {
  color: rgba(255, 255, 255, 0.7);
  font-size: 1rem;
  line-height: 1.5;
}

.action-buttons {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.action-link {
  display: inline-block;
  padding: 0.875rem 1.5rem;
  border-radius: 0.5rem;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff;
  text-decoration: none;
  font-weight: 500;
  font-size: 1rem;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-link:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
}

.action-link:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.secondary-link {
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.3s ease;
}

.secondary-link:hover {
  color: #fff;
}
</style>
