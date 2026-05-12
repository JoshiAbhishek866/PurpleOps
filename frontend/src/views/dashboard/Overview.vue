<template>
  <div class="overview-page">
    <div class="page-header">
      <div>
        <h1 class="page-title" data-testid="overview-title">{{ pageTitle }}</h1>
        <p class="page-subtitle">{{ pageDescription }}</p>
      </div>
      <SecurityScanner />
    </div>

    <!-- Loading State -->
    <div
      v-if="loading"
      class="loading-container"
      data-testid="loading-overview"
    >
      <div class="loading-spinner-large"></div>
      <p>Loading security data...</p>
    </div>

    <div v-else class="overview-content">
      <!-- Stats Grid with Core UI Widgets -->

      <section class="stats-section" data-testid="stats-section">
        <div class="stats-grid">
          <Widget
            :title="stats[0]?.label || 'Total Events'"
            :value="overview.totalEvents || 0"
            :icon="ShieldCheckIcon"
            color="blue"
            data-testid="total-events-card"
          />

          <Widget
            :title="stats[1]?.label || 'Events (24h)'"
            subtitle="Last 24 hours"
            :value="overview.events24h || 0"
            :icon="ClockIcon"
            color="green"
            :trend="overview.trends?.percentage || 0"
            data-testid="events-24h-card"
          />

          <Widget
            :title="stats[2]?.label || 'Blocked Attacks'"
            :value="overview.blockedAttacks || 0"
            :icon="ExclamationTriangleIcon"
            color="red"
            data-testid="blocked-attacks-card"
          />

          <Widget
            :title="stats[3]?.label || 'System Uptime'"
            :value="overview.systemUptime || 0"
            :icon="HeartIcon"
            color="purple"
            format="percentage"
            data-testid="system-uptime-card"
          />
        </div>
      </section>

      <!-- Charts Section with Core UI Cards -->
      <section class="charts-section" v-if="showCharts">
        <div class="charts-grid">
          <!-- Threat Timeline Chart -->
          <Card
            v-if="threatActivityEnabled"
            :title="threatActivityTitle"
            :icon="ShieldCheckIcon"
            data-testid="threat-timeline-chart"
          >
            <div class="chart-container">
              <canvas ref="timelineChart"></canvas>
            </div>
          </Card>

          <!-- Attack Types Distribution -->
          <Card
            v-if="attackTypesEnabled"
            :title="attackTypesTitle"
            :icon="ChartBarIcon"
            data-testid="attack-types-chart"
          >
            <div class="chart-container">
              <canvas ref="attackTypesChart"></canvas>
            </div>
          </Card>
        </div>
      </section>

      <!-- Recent Events -->
      <section class="recent-events-section" data-testid="recent-events">
        <div class="section-header">
          <h2 class="section-title">Recent Security Events</h2>
          <router-link to="/dashboard/activity-logs" class="view-all-link">
            View All Logs →
          </router-link>
        </div>

        <div class="events-list glass">
          <div
            v-for="event in recentEvents"
            :key="event.id"
            class="event-item"
            :data-testid="`event-${event.id}`"
          >
            <div class="event-icon" :class="`severity-${event.severity}`">
              <component :is="getEventIcon(event.eventType)" class="icon-xs" />
            </div>
            <div class="event-content">
              <p class="event-description">{{ event.description }}</p>
              <p class="event-meta">
                {{ event.eventType }} • {{ event.source?.ip || "Unknown" }} •
                {{ formatDate(event.createdAt) }}
              </p>
            </div>
            <div class="event-status">
              <span class="status-badge" :class="`status-${event.status}`">
                {{ event.status }}
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useDashboardStore } from "@/stores/dashboard";
import { useContentStore } from "@/stores/content";
import { Chart, registerables } from "chart.js";
import Widget from "@/components/ui/Widget.vue";
import Card from "@/components/ui/Card.vue";
import {
  ShieldCheckIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  HeartIcon,
  BugAntIcon,
  FireIcon,
  EyeIcon,
  ChartBarIcon,
} from "@heroicons/vue/24/outline";
import SecurityScanner from "@/components/SecurityScanner.vue";
Chart.register(...registerables);

const dashboardStore = useDashboardStore();
const contentStore = useContentStore();
const timelineChart = ref(null);
const attackTypesChart = ref(null);

const loading = ref(true);
const overview = computed(() => dashboardStore.overview);
const recentEvents = ref([]);

// Dynamic content from content store with fallbacks
const pageTitle = computed(() => {
  return contentStore.clientDashboard?.pageTitle || "Security Overview";
});

const pageDescription = computed(() => {
  return (
    contentStore.clientDashboard?.pageDescription ||
    "Real-time security monitoring and threat analysis"
  );
});

const stats = computed(() => {
  return (
    contentStore.clientDashboard?.stats || [
      { label: "Total Events" },
      { label: "Events (24h)" },
      { label: "Blocked Attacks" },
      { label: "System Uptime" },
    ]
  );
});

const showCharts = computed(() => {
  return threatActivityEnabled.value || attackTypesEnabled.value;
});

const threatActivityEnabled = computed(() => {
  return (
    contentStore.clientDashboard?.charts?.threatActivity?.enabled !== false
  );
});

const threatActivityTitle = computed(() => {
  return (
    contentStore.clientDashboard?.charts?.threatActivity?.title ||
    "Threat Activity (Last 7 Days)"
  );
});

const attackTypesEnabled = computed(() => {
  return contentStore.clientDashboard?.charts?.attackTypes?.enabled !== false;
});

const attackTypesTitle = computed(() => {
  return (
    contentStore.clientDashboard?.charts?.attackTypes?.title ||
    "Attack Types Distribution"
  );
});

const trendClass = computed(() => {
  const trends = overview.value.trends;
  if (!trends) return "";
  return trends.direction === "increase" ? "text-red-500" : "text-green-500";
});

const trendText = computed(() => {
  const trends = overview.value.trends;
  if (!trends) return "";
  const direction = trends.direction === "increase" ? "↑" : "↓";
  return `${direction} ${trends.percentage}% vs last week`;
});

function formatNumber(num) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + "M";
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + "K";
  }
  return num?.toString() || "0";
}

function formatDate(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now - date;

  if (diff < 60000) return "Just now";
  if (diff < 3600000) return Math.floor(diff / 60000) + "m ago";
  if (diff < 86400000) return Math.floor(diff / 3600000) + "h ago";
  return Math.floor(diff / 86400000) + "d ago";
}

function getEventIcon(eventType) {
  const icons = {
    attack_blocked: ShieldCheckIcon,
    malware_detected: BugAntIcon,
    ddos_mitigated: FireIcon,
    intrusion_attempt: ExclamationTriangleIcon,
    vulnerability_scan: EyeIcon,
  };
  return icons[eventType] || ExclamationTriangleIcon;
}

function createTimelineChart() {
  if (!timelineChart.value) return;

  // Mock data for timeline
  const labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const data = [12, 19, 8, 15, 22, 18, 25];

  new Chart(timelineChart.value, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Security Events",
          data,
          borderColor: "rgb(139, 92, 246)",
          backgroundColor: "rgba(139, 92, 246, 0.1)",
          fill: true,
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });
}

function createAttackTypesChart() {
  if (!attackTypesChart.value) return;

  // Mock data for attack types
  const data = [30, 25, 20, 15, 10];
  const labels = ["Malware", "Phishing", "DDoS", "Intrusion", "Other"];

  new Chart(attackTypesChart.value, {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data,
          backgroundColor: [
            "#8b5cf6",
            "#10b981",
            "#f59e0b",
            "#ef4444",
            "#6b7280",
          ],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
        },
      },
    },
  });
}

async function loadData() {
  try {
    // Fetch dashboard data
    await dashboardStore.fetchOverview();

    // Try to fetch client dashboard content, but don't fail if it errors
    try {
      await contentStore.fetchClientDashboard();
    } catch (contentError) {
      console.warn(
        "Could not load client dashboard content, using defaults:",
        contentError,
      );
      // Continue with default content - don't throw error
    }

    // Mock recent events
    recentEvents.value = [
      {
        id: "1",
        eventType: "attack_blocked",
        severity: "high",
        description: "SQL injection attack blocked on login endpoint",
        source: { ip: "192.168.1.100" },
        status: "blocked",
        createdAt: new Date(Date.now() - 300000), // 5 minutes ago
      },
      {
        id: "2",
        eventType: "malware_detected",
        severity: "critical",
        description: "Malware signature detected in file upload",
        source: { ip: "10.0.0.15" },
        status: "quarantined",
        createdAt: new Date(Date.now() - 900000), // 15 minutes ago
      },
      {
        id: "3",
        eventType: "ddos_mitigated",
        severity: "medium",
        description: "DDoS attack attempt mitigated successfully",
        source: { ip: "203.0.113.50" },
        status: "resolved",
        createdAt: new Date(Date.now() - 1800000), // 30 minutes ago
      },
    ];
  } catch (error) {
    console.error("Failed to load overview data:", error);
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  await loadData();

  // Create charts after data is loaded
  setTimeout(() => {
    createTimelineChart();
    createAttackTypesChart();
  }, 100);
});
</script>

<style scoped>
.overview-page {
  @apply space-y-8;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  gap: 20px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
}

.page-title {
  @apply text-3xl font-bold;
  color: #1a202c;
  margin: 0;
}

.dark .page-title {
  color: #f7fafc;
}

.page-subtitle {
  @apply text-gray-600;
  margin-top: 0.5rem;
  margin-bottom: 0;
}

.dark .page-subtitle {
  @apply text-gray-400;
}

/* Loading */
.loading-container {
  @apply text-center py-20;
}

.loading-container p {
  @apply mt-4 text-gray-600;
}

.dark .loading-container p {
  @apply text-gray-400;
}

/* Stats Section */
.stats-grid {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6;
}

.stat-card {
  @apply p-6 rounded-xl;
}

.stat-card {
  @apply flex items-center gap-4;
}

.stat-icon {
  @apply w-12 h-12 rounded-lg flex items-center justify-center;
}

.stat-content {
  @apply flex-1;
}

.stat-label {
  @apply text-sm font-medium text-gray-600 mb-1;
}

.dark .stat-label {
  @apply text-gray-400;
}

.stat-value {
  @apply text-2xl font-bold;
  color: #1a202c;
}

.dark .stat-value {
  color: #f7fafc;
}

.stat-trend {
  @apply text-sm font-medium;
}

/* Charts Section */
.charts-section {
  @apply mt-8;
}

.charts-grid {
  @apply grid grid-cols-1 lg:grid-cols-2 gap-6;
}

.chart-card {
  @apply p-6 rounded-xl;
}

.chart-title {
  @apply text-lg font-bold mb-4;
  color: #1a202c;
}

.dark .chart-title {
  color: #f7fafc;
}

.chart-container {
  @apply relative h-64;
}

/* Recent Events */
.recent-events-section {
  @apply mt-8;
}

.section-header {
  @apply flex items-center justify-between mb-6;
}

.section-title {
  @apply text-xl font-bold;
  color: #1a202c;
}

.dark .section-title {
  color: #f7fafc;
}

.view-all-link {
  @apply text-purple-600 hover:text-purple-700 font-medium no-underline;
}

.dark .view-all-link {
  @apply text-purple-400 hover:text-purple-300;
}

.events-list {
  @apply p-6 rounded-xl space-y-4;
}

.event-item {
  @apply flex items-center gap-4 p-4 rounded-lg;
  background: rgba(255, 255, 255, 0.5);
}

.dark .event-item {
  background: rgba(139, 92, 246, 0.05);
}

.event-icon {
  @apply w-8 h-8 rounded-full flex items-center justify-center;
}

.event-icon.severity-low {
  @apply bg-blue-100 text-blue-600;
}

.event-icon.severity-medium {
  @apply bg-yellow-100 text-yellow-600;
}

.event-icon.severity-high {
  @apply bg-orange-100 text-orange-600;
}

.event-icon.severity-critical {
  @apply bg-red-100 text-red-600;
}

.dark .event-icon.severity-low {
  @apply bg-blue-900 text-blue-400;
}

.dark .event-icon.severity-medium {
  @apply bg-yellow-900 text-yellow-400;
}

.dark .event-icon.severity-high {
  @apply bg-orange-900 text-orange-400;
}

.dark .event-icon.severity-critical {
  @apply bg-red-900 text-red-400;
}

.event-content {
  @apply flex-1;
}

.event-description {
  @apply font-medium text-gray-900;
}

.dark .event-description {
  @apply text-gray-100;
}

.event-meta {
  @apply text-sm text-gray-600;
}

.dark .event-meta {
  @apply text-gray-400;
}

.status-badge {
  @apply px-3 py-1 text-xs font-medium rounded-full;
}

.status-badge.status-blocked {
  @apply bg-red-100 text-red-800;
}

.status-badge.status-quarantined {
  @apply bg-yellow-100 text-yellow-800;
}

.status-badge.status-resolved {
  @apply bg-green-100 text-green-800;
}

.dark .status-badge.status-blocked {
  @apply bg-red-900 text-red-200;
}

.dark .status-badge.status-quarantined {
  @apply bg-yellow-900 text-yellow-200;
}

.dark .status-badge.status-resolved {
  @apply bg-green-900 text-green-200;
}

/* Responsive Design */
@media (max-width: 768px) {
  .stats-grid {
    @apply grid-cols-1 gap-4;
  }

  .charts-grid {
    @apply grid-cols-1;
  }
}
</style>
