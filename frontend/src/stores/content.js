import { defineStore } from "pinia";
import { ref } from "vue";
import axios from "axios";

const API_BASE = "http://localhost:8000/api"; // (import.meta.env.VITE_API_URL || 'http://localhost:8001/api').replace(/\/$/, '')

export const useContentStore = defineStore("content", () => {
  const hero = ref(null);
  const features = ref(null);
  const about = ref(null);
  const services = ref(null);
  const testimonials = ref(null);
  const header = ref(null);
  const footer = ref(null);
  const bookDemo = ref(null);
  const pricing = ref(null);
  const auth = ref(null);
  const clientDashboard = ref(null);
  const isLoading = ref(false);
  const error = ref(null);

  async function fetchSection(section) {
    try {
      const response = await axios.get(`${API_BASE}/content/${section}`);
      return response.data.content;
    } catch (err) {
      console.error(`Failed to fetch ${section}:`, err);
      return null;
    }
  }

  async function fetchAllContent() {
    isLoading.value = true;
    error.value = null;

    try {
      const [
        heroData,
        featuresData,
        aboutData,
        servicesData,
        testimonialsData,
      ] = await Promise.all([
        fetchSection("hero"),
        fetchSection("features"),
        fetchSection("about"),
        fetchSection("services"),
        fetchSection("testimonials"),
      ]);

      hero.value = heroData;
      features.value = featuresData;
      about.value = aboutData;
      services.value = servicesData;
      testimonials.value = testimonialsData;
    } catch (err) {
      error.value = "Failed to load content";
      console.error("Content fetch error:", err);
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchHero() {
    hero.value = await fetchSection("hero");
  }

  async function fetchFeatures() {
    features.value = await fetchSection("features");
  }

  async function fetchAbout() {
    about.value = await fetchSection("about");
  }

  async function fetchServices() {
    services.value = await fetchSection("services");
  }

  async function fetchTestimonials() {
    testimonials.value = await fetchSection("testimonials");
  }

  async function fetchHeader() {
    header.value = await fetchSection("header");
  }

  async function fetchFooter() {
    footer.value = await fetchSection("footer");
  }

  async function fetchBookDemo() {
    bookDemo.value = await fetchSection("bookDemo");
  }

  async function fetchPricing() {
    pricing.value = await fetchSection("pricing");
  }

  async function fetchAuth() {
    auth.value = await fetchSection("auth");
  }

  async function fetchClientDashboard() {
    // For now, return empty object since backend endpoint doesn't exist yet
    // This prevents 404 errors and allows pages to use fallback values
    clientDashboard.value = {};
    return clientDashboard.value;
  }

  return {
    hero,
    features,
    about,
    services,
    testimonials,
    header,
    footer,
    bookDemo,
    pricing,
    auth,
    clientDashboard,
    isLoading,
    error,
    fetchAllContent,
    fetchHero,
    fetchFeatures,
    fetchAbout,
    fetchServices,
    fetchTestimonials,
    fetchHeader,
    fetchFooter,
    fetchBookDemo,
    fetchPricing,
    fetchAuth,
    fetchClientDashboard,
  };
});
