<template>
  <div class="book-demo-page">
    <DynamicSEO page="book-demo" />
    <div class="container">
      <!-- Hero Section -->
      <section class="demo-hero" data-testid="demo-hero">
        <h1 class="heading-luxury">Book Your Demo</h1>
        <p class="hero-subtitle">
          See PurpleOps in action. Get a personalized demonstration tailored to
          your organization's security needs.
        </p>
      </section>

      <!-- Demo Info Cards -->
      <section class="demo-info" data-testid="demo-info">
        <div class="info-grid">
          <div class="info-card glass">
            <ClockIcon class="info-icon" />
            <h3 class="info-title">30-Minute Session</h3>
            <p class="info-description">
              Quick but comprehensive overview of our platform
            </p>
          </div>
          <div class="info-card glass">
            <UserGroupIcon class="info-icon" />
            <h3 class="info-title">Personalized</h3>
            <p class="info-description">
              Tailored to your specific security requirements
            </p>
          </div>
          <div class="info-card glass">
            <ShieldCheckIcon class="info-icon" />
            <h3 class="info-title">Live Environment</h3>
            <p class="info-description">
              Real-time demonstration with actual threat data
            </p>
          </div>
        </div>
      </section>

      <!-- Demo Form -->
      <section class="demo-form-section glass" data-testid="demo-form-section">
        <div class="form-container">
          <h2 class="form-title">Schedule Your Demo</h2>

          <form @submit.prevent="submitDemo" class="demo-form">
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
                />
                <span v-if="errors.firstName" class="error-message">{{
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
                />
                <span v-if="errors.lastName" class="error-message">{{
                  errors.lastName
                }}</span>
              </div>
            </div>

            <div class="form-row">
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
                />
                <span v-if="errors.email" class="error-message">{{
                  errors.email
                }}</span>
              </div>

              <div class="form-group">
                <label for="phone" class="form-label">Phone Number</label>
                <input
                  id="phone"
                  v-model="form.phone"
                  type="tel"
                  class="form-input"
                  data-testid="phone-input"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="company" class="form-label">Company *</label>
                <input
                  id="company"
                  v-model="form.company"
                  type="text"
                  required
                  class="form-input"
                  :class="{ error: errors.company }"
                  data-testid="company-input"
                />
                <span v-if="errors.company" class="error-message">{{
                  errors.company
                }}</span>
              </div>

              <div class="form-group">
                <label for="companySize" class="form-label">Company Size</label>
                <select
                  id="companySize"
                  v-model="form.companySize"
                  class="form-input"
                  data-testid="company-size-select"
                >
                  <option value="">Select company size</option>
                  <option value="1-10">1-10 employees</option>
                  <option value="11-50">11-50 employees</option>
                  <option value="51-200">51-200 employees</option>
                  <option value="201-1000">201-1000 employees</option>
                  <option value="1000+">1000+ employees</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <label for="preferredDate" class="form-label"
                >Preferred Date</label
              >
              <input
                id="preferredDate"
                v-model="form.preferredDate"
                type="date"
                :min="minDate"
                class="form-input"
                data-testid="preferred-date-input"
              />
            </div>

            <div class="form-group">
              <label for="message" class="form-label"
                >Additional Information</label
              >
              <textarea
                id="message"
                v-model="form.message"
                rows="4"
                placeholder="Tell us about your specific security needs or questions..."
                class="form-input"
                data-testid="message-textarea"
              ></textarea>
            </div>

            <div class="form-actions">
              <LuxuryButton
                type="submit"
                size="lg"
                :loading="submitting"
                :disabled="!isFormValid"
                data-testid="submit-demo-button"
              >
                Schedule Demo
              </LuxuryButton>
            </div>
          </form>

          <!-- Success Message -->
          <div
            v-if="submitted"
            class="success-message"
            data-testid="success-message"
          >
            <CheckCircleIcon class="success-icon" />
            <h3 class="success-title">Demo Request Submitted!</h3>
            <p class="success-description">
              Thank you for your interest. Our team will contact you within 24
              hours to schedule your personalized demonstration.
            </p>
          </div>
        </div>
      </section>

      <!-- What to Expect -->
      <section class="expectations-section" data-testid="expectations-section">
        <h2 class="section-title">What to Expect in Your Demo</h2>
        <div class="expectations-grid">
          <div
            v-for="expectation in expectations"
            :key="expectation.id"
            class="expectation-card glass"
            :data-testid="`expectation-${expectation.id}`"
          >
            <component :is="expectation.icon" class="expectation-icon" />
            <h3 class="expectation-title">{{ expectation.title }}</h3>
            <p class="expectation-description">{{ expectation.description }}</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import axios from "axios";
import LuxuryButton from "@/components/LuxuryButton.vue";
import DynamicSEO from "@/components/DynamicSEO.vue";
import {
  ClockIcon,
  UserGroupIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  EyeIcon,
  ChartBarIcon,
  CogIcon,
} from "@heroicons/vue/24/outline";

const backendBaseUrl = (
  import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"
).replace(/\/$/, "");
const API_BASE = `${backendBaseUrl}/api`;

const form = ref({
  firstName: "",
  lastName: "",
  email: "",
  phone: "",
  company: "",
  companySize: "",
  preferredDate: "",
  message: "",
});

const errors = ref({});
const submitting = ref(false);
const submitted = ref(false);

const expectations = [
  {
    id: 1,
    icon: EyeIcon,
    title: "Platform Overview",
    description:
      "Complete walkthrough of the PurpleOps interface and core features",
  },
  {
    id: 2,
    icon: ChartBarIcon,
    title: "Live Dashboard",
    description: "Real-time security monitoring and threat detection in action",
  },
  {
    id: 3,
    icon: CogIcon,
    title: "Custom Configuration",
    description:
      "See how the platform can be tailored to your specific environment",
  },
];

const minDate = computed(() => {
  const today = new Date();
  today.setDate(today.getDate() + 1); // Tomorrow
  return today.toISOString().split("T")[0];
});

const isFormValid = computed(() => {
  return (
    form.value.firstName &&
    form.value.lastName &&
    form.value.email &&
    form.value.company &&
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

  return Object.keys(errors.value).length === 0;
}

async function submitDemo() {
  if (!validateForm()) return;

  submitting.value = true;

  try {
    const response = await axios.post(`${API_BASE}/book-demo`, form.value);

    if (response.status === 200) {
      submitted.value = true;
      // Reset form
      form.value = {
        firstName: "",
        lastName: "",
        email: "",
        phone: "",
        company: "",
        companySize: "",
        preferredDate: "",
        message: "",
      };
    }
  } catch (error) {
    console.error("Demo submission failed:", error);

    if (error.response?.data?.errors) {
      error.response.data.errors.forEach((err) => {
        errors.value[err.path] = err.msg;
      });
    }
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.book-demo-page {
  @apply py-20;
  min-height: 100vh;
}

.container {
  @apply max-w-6xl mx-auto px-6 space-y-16;
}

/* Hero Section */
.demo-hero {
  @apply text-center py-16;
}

.hero-subtitle {
  @apply text-xl text-gray-600 mt-6 max-w-3xl mx-auto leading-relaxed;
}

/* Demo Info Cards */
.info-grid {
  @apply grid grid-cols-1 md:grid-cols-3 gap-6;
}

.info-card {
  @apply p-8 text-center rounded-xl;
}

.info-icon {
  @apply w-12 h-12 mx-auto mb-4 p-2 rounded-lg;
}

.info-title {
  @apply text-xl font-bold mb-2;
  color: #1a202c;
}

.info-description {
  @apply text-gray-600;
}

/* Demo Form */
.demo-form-section {
  @apply p-12 rounded-2xl;
}

.form-container {
  @apply max-w-3xl mx-auto;
}

.form-title {
  @apply text-3xl font-bold text-center mb-8;
  color: #1a202c;
}

.demo-form {
  @apply space-y-6;
}

.form-row {
  @apply grid grid-cols-1 md:grid-cols-2 gap-6;
}

.form-group {
  @apply space-y-2;
}

.form-label {
  @apply block text-sm font-semibold text-gray-700;
}

.form-input {
  @apply w-full px-4 py-3 rounded-lg transition-all duration-300;
  background: rgba(255, 255, 255, 0.5); /* Slightly transparent background */
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-color); /* Add border for visibility */
  color: var(--text-primary); /* Ensure text is visible */
}

.form-input:focus {
  @apply outline-none ring-2 ring-purple-500;
  background: rgba(255, 255, 255, 0.8);
  border-color: #8b5cf6;
}

.form-input.error {
  @apply ring-2 ring-red-500;
}

.error-message {
  @apply text-red-500 text-sm;
}

.form-actions {
  @apply text-center pt-6;
}

/* Success Message */
.success-message {
  @apply text-center py-12;
}

.success-icon {
  @apply w-16 h-16 mx-auto mb-4 text-green-500;
}

.success-title {
  @apply text-2xl font-bold mb-4 text-green-600;
}

.success-description {
  @apply text-gray-600 max-w-md mx-auto;
}

/* Expectations Section */
.expectations-section {
  @apply text-center;
}

.section-title {
  @apply text-3xl font-bold mb-12;
  color: #1a202c;
}

.expectations-grid {
  @apply grid grid-cols-1 md:grid-cols-3 gap-8;
}

.expectation-card {
  @apply p-8 text-center rounded-xl;
}

.expectation-icon {
  @apply w-12 h-12 mx-auto mb-4 p-2 rounded-lg;
}

.expectation-title {
  @apply text-xl font-bold mb-4;
  color: #1a202c;
}

.expectation-description {
  @apply text-gray-600 leading-relaxed;
}

/* Responsive Design */
@media (max-width: 768px) {
  .form-row {
    @apply grid-cols-1 gap-4;
  }

  .info-grid,
  .expectations-grid {
    @apply grid-cols-1 gap-6;
  }
}
</style>
