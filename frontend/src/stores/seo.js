import { defineStore } from "pinia";
import { ref, computed } from "vue";

export const useSEOStore = defineStore("seo", () => {
  // State
  const globalSEO = ref(null);
  const pageSEO = ref({}); // Object with page names as keys
  const loading = ref(false);
  const error = ref(null);

  // API Base URL - hardcoded to local backend for local dev
  const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

  // Actions
  async function fetchGlobalSEO() {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE}/seo/global`);
      if (!response.ok) {
        throw new Error("Failed to fetch global SEO settings");
      }
      const data = await response.json();
      globalSEO.value = data;
      return data;
    } catch (err) {
      error.value = err.message;
      console.error("Error fetching global SEO:", err);
      // Return defaults on error
      return {
        siteName: "PurpleOps",
        siteUrl: "https://PurpleOps.com",
        defaultOgImage: "https://PurpleOps.com/og-image.jpg",
        themeColor: "#8b5cf6",
        twitterSite: "@PurpleOps",
        defaultAuthor: "PurpleOps Team",
      };
    } finally {
      loading.value = false;
    }
  }

  async function fetchPageSEO(page) {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE}/seo/pages/${page}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch SEO for page: ${page}`);
      }
      const data = await response.json();
      pageSEO.value[page] = data;
      return data;
    } catch (err) {
      error.value = err.message;
      console.error(`Error fetching SEO for page ${page}:`, err);
      // Return empty object on error - component will use fallbacks
      return {};
    } finally {
      loading.value = false;
    }
  }

  async function updateGlobalSEO(settings) {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE}/admin/seo/global`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(settings),
      });

      if (!response.ok) {
        throw new Error("Failed to update global SEO settings");
      }

      const data = await response.json();
      globalSEO.value = data.settings;
      return data;
    } catch (err) {
      error.value = err.message;
      console.error("Error updating global SEO:", err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function updatePageSEO(page, seoData) {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE}/admin/seo/pages/${page}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(seoData),
      });

      if (!response.ok) {
        throw new Error(`Failed to update SEO for page: ${page}`);
      }

      const data = await response.json();
      pageSEO.value[page] = {
        page: data.page,
        seo: data.seo,
      };
      return data;
    } catch (err) {
      error.value = err.message;
      console.error(`Error updating SEO for page ${page}:`, err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchAllPagesSEO() {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE}/seo/pages`);
      if (!response.ok) {
        throw new Error("Failed to fetch all pages SEO");
      }
      const data = await response.json();

      // Convert array to object with page names as keys
      const pagesObj = {};
      data.pages.forEach((page) => {
        pagesObj[page.page] = page;
      });
      pageSEO.value = pagesObj;

      return data.pages;
    } catch (err) {
      error.value = err.message;
      console.error("Error fetching all pages SEO:", err);
      return [];
    } finally {
      loading.value = false;
    }
  }

  async function deletePageSEO(page) {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE}/admin/seo/pages/${page}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error(`Failed to delete SEO for page: ${page}`);
      }

      // Remove from local state
      delete pageSEO.value[page];

      return await response.json();
    } catch (err) {
      error.value = err.message;
      console.error(`Error deleting SEO for page ${page}:`, err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function bulkUpdateSEO(pages) {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE}/admin/seo/pages/bulk`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ pages }),
      });

      if (!response.ok) {
        throw new Error("Failed to bulk update SEO");
      }

      const data = await response.json();

      // Update local state
      pages.forEach((pageData) => {
        pageSEO.value[pageData.page] = pageData;
      });

      return data;
    } catch (err) {
      error.value = err.message;
      console.error("Error bulk updating SEO:", err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // Computed
  const isLoading = computed(() => loading.value);
  const hasError = computed(() => error.value !== null);

  return {
    // State
    globalSEO,
    pageSEO,
    loading,
    error,

    // Actions
    fetchGlobalSEO,
    fetchPageSEO,
    updateGlobalSEO,
    updatePageSEO,
    fetchAllPagesSEO,
    deletePageSEO,
    bulkUpdateSEO,

    // Computed
    isLoading,
    hasError,
  };
});
