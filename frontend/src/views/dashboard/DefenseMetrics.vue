<template>
  <div class="defense-metrics-page">
    <h1 class="page-title">Defense Metrics</h1>
    <p class="page-subtitle">
      Defensive security posture - Threat detection, hardening, and compliance
    </p>

    <!-- Defense Results -->
    <div v-if="hasDefenseData" class="defense-content">
      <!-- Defense Summary Cards -->
      <div class="summary-grid">
        <div class="summary-card threats">
          <div class="card-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="1.5"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
              />
            </svg>
          </div>
          <div class="card-content">
            <h4>Threats Detected</h4>
            <p class="card-value">{{ threatsDetected }}</p>
            <span class="card-label">Last 24 hours</span>
          </div>
        </div>

        <div class="summary-card hardening">
          <div class="card-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="1.5"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
              />
            </svg>
          </div>
          <div class="card-content">
            <h4>Hardening Items</h4>
            <p class="card-value">{{ hardeningItems }}</p>
            <span class="card-label">Recommendations</span>
          </div>
        </div>

        <div class="summary-card patches">
          <div class="card-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="1.5"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M11.42 15.17L17.25 21A2.652 2.652 0 0021 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 11-3.586-3.586l6.837-5.63m5.108-.233c.55-.164 1.163-.188 1.743-.14a4.5 4.5 0 004.486-6.336l-3.276 3.277a3.004 3.004 0 01-2.25-2.25l3.276-3.276a4.5 4.5 0 00-6.336 4.486c.091 1.076-.071 2.264-.904 2.95l-.102.085m-1.745 1.437L5.909 7.5H4.5L2.25 3.75l1.5-1.5L7.5 4.5v1.409l4.26 4.26m-1.745 1.437l1.745-1.437m6.615 8.206L15.75 15.75M4.867 19.125h.008v.008h-.008v-.008z"
              />
            </svg>
          </div>
          <div class="card-content">
            <h4>Patches Applied</h4>
            <p class="card-value">{{ patchesApplied }}</p>
            <span class="card-label">This month</span>
          </div>
        </div>

        <div class="summary-card compliance">
          <div class="card-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="1.5"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z"
              />
            </svg>
          </div>
          <div class="card-content">
            <h4>Compliance Score</h4>
            <p class="card-value">{{ complianceScore }}%</p>
            <span class="card-label">CIS Benchmark</span>
          </div>
        </div>
      </div>

      <!-- Threat Detection -->
      <div class="threats-section">
        <h2>Detected Threats</h2>
        <div class="threats-list">
          <div
            v-for="threat in threats"
            :key="threat.id"
            class="threat-card"
            :class="threat.severity"
          >
            <div class="threat-header">
              <div>
                <h4>{{ threat.title }}</h4>
                <p class="threat-time">{{ threat.timestamp }}</p>
              </div>
              <span class="severity-badge" :class="threat.severity">
                {{ threat.severity }}
              </span>
            </div>
            <p class="threat-description">{{ threat.description }}</p>
            <div class="threat-details">
              <span><strong>Source:</strong> {{ threat.source }}</span>
              <span><strong>Action:</strong> {{ threat.action }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Hardening Recommendations -->
      <div class="hardening-section">
        <h2>Security Hardening Recommendations</h2>
        <div class="hardening-list">
          <div
            v-for="item in hardeningRecommendations"
            :key="item.id"
            class="hardening-card"
          >
            <div class="hardening-header">
              <h4>{{ item.title }}</h4>
              <span class="priority-badge" :class="item.priority">
                {{ item.priority }} Priority
              </span>
            </div>
            <p class="hardening-description">{{ item.description }}</p>
            <div class="hardening-actions">
              <button class="btn-secondary">View Details</button>
              <button class="btn-primary">Apply Fix</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Patches -->
      <div class="patches-section">
        <h2>Security Patches</h2>
        <div class="patches-list">
          <div v-for="patch in patches" :key="patch.id" class="patch-card">
            <div class="patch-header">
              <div>
                <h4>{{ patch.title }}</h4>
                <p class="patch-description">{{ patch.description }}</p>
              </div>
              <span class="status-badge" :class="patch.status">
                {{ patch.status }}
              </span>
            </div>

            <div class="patch-details">
              <div class="detail-item">
                <span class="label">Vulnerabilities Fixed:</span>
                <span class="value">{{ patch.vulnerabilitiesFixed }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Applied:</span>
                <span class="value">{{ patch.appliedAt || "Pending" }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Success Rate:</span>
                <span class="value">{{ patch.successRate }}%</span>
              </div>
            </div>

            <div class="patch-actions">
              <button class="btn-secondary">View Changelog</button>
              <button v-if="patch.status === 'pending'" class="btn-primary">
                Apply Now
              </button>
              <button v-if="patch.status === 'applied'" class="btn-secondary">
                Rollback
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- No Results State -->
    <div v-else class="empty-state">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke-width="1.5"
        stroke="currentColor"
        class="empty-icon"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
        />
      </svg>
      <h2>No Defense Data Available</h2>
      <p>Run a security scan to see defensive metrics</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

// Mock data
const threatsDetected = ref(12);
const hardeningItems = ref(8);
const patchesApplied = ref(15);
const complianceScore = ref(87);

const threats = ref([
  {
    id: 1,
    title: "Suspicious Login Attempt",
    description: "Multiple failed login attempts from IP 192.168.1.100",
    severity: "high",
    source: "192.168.1.100",
    action: "Blocked",
    timestamp: "2 minutes ago",
  },
  {
    id: 2,
    title: "Port Scan Detected",
    description: "Systematic port scanning activity detected",
    severity: "medium",
    source: "10.0.0.15",
    action: "Monitored",
    timestamp: "15 minutes ago",
  },
  {
    id: 3,
    title: "Malware Signature Match",
    description: "Known malware signature detected in uploaded file",
    severity: "critical",
    source: "File Upload",
    action: "Quarantined",
    timestamp: "1 hour ago",
  },
]);

const hardeningRecommendations = ref([
  {
    id: 1,
    title: "Enable Multi-Factor Authentication",
    description: "Implement MFA for all user accounts to enhance security",
    priority: "high",
  },
  {
    id: 2,
    title: "Update SSL/TLS Configuration",
    description: "Disable weak ciphers and enable TLS 1.3",
    priority: "high",
  },
  {
    id: 3,
    title: "Implement Rate Limiting",
    description: "Add rate limiting to API endpoints to prevent abuse",
    priority: "medium",
  },
  {
    id: 4,
    title: "Enable Security Headers",
    description: "Add CSP, HSTS, and X-Frame-Options headers",
    priority: "medium",
  },
]);

const patches = ref([
  {
    id: "PATCH-001",
    title: "Security Update 2024-01",
    description:
      "Critical security patches for authentication and SQL injection vulnerabilities",
    status: "applied",
    vulnerabilitiesFixed: 2,
    appliedAt: "2 days ago",
    successRate: 100,
  },
  {
    id: "PATCH-002",
    title: "XSS Protection Update",
    description: "Implements input sanitization and output encoding",
    status: "pending",
    vulnerabilitiesFixed: 1,
    appliedAt: null,
    successRate: 0,
  },
  {
    id: "PATCH-003",
    title: "Dependency Security Update",
    description: "Updates vulnerable npm packages to latest secure versions",
    status: "applied",
    vulnerabilitiesFixed: 5,
    appliedAt: "1 week ago",
    successRate: 100,
  },
]);

const hasDefenseData = computed(() => true);
</script>

<style scoped>
.defense-metrics-page {
  padding: 24px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 8px 0;
}

.page-subtitle {
  color: #6b7280;
  font-size: 16px;
  margin: 0 0 32px 0;
}

/* Summary Grid */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.summary-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 16px;
  border-left: 4px solid;
}

.summary-card.threats {
  border-left-color: #dc2626;
}

.summary-card.hardening {
  border-left-color: #3b82f6;
}

.summary-card.patches {
  border-left-color: #10b981;
}

.summary-card.compliance {
  border-left-color: #8b5cf6;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.threats .card-icon {
  background: #fee2e2;
  color: #dc2626;
}

.hardening .card-icon {
  background: #dbeafe;
  color: #3b82f6;
}

.patches .card-icon {
  background: #d1fae5;
  color: #10b981;
}

.compliance .card-icon {
  background: #ede9fe;
  color: #8b5cf6;
}

.card-icon svg {
  width: 24px;
  height: 24px;
}

.card-content h4 {
  font-size: 14px;
  font-weight: 600;
  color: #6b7280;
  margin: 0 0 8px 0;
}

.card-value {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 4px 0;
}

.card-label {
  font-size: 12px;
  color: #9ca3af;
}

/* Threats Section */
.threats-section,
.hardening-section,
.patches-section {
  margin-bottom: 32px;
}

.threats-section h2,
.hardening-section h2,
.patches-section h2 {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 20px;
}

.threats-list,
.hardening-list,
.patches-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.threat-card,
.hardening-card,
.patch-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-left: 4px solid;
}

.threat-card.critical {
  border-left-color: #dc2626;
}

.threat-card.high {
  border-left-color: #f59e0b;
}

.threat-card.medium {
  border-left-color: #fbbf24;
}

.hardening-card {
  border-left-color: #3b82f6;
}

.patch-card {
  border-left-color: #10b981;
}

.threat-header,
.hardening-header,
.patch-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.threat-header h4,
.hardening-header h4,
.patch-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 4px 0;
}

.threat-time {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

.threat-description,
.hardening-description,
.patch-description {
  color: #374151;
  margin-bottom: 12px;
  line-height: 1.6;
}

.threat-details {
  display: flex;
  gap: 24px;
  font-size: 14px;
  color: #6b7280;
}

.severity-badge,
.priority-badge,
.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.severity-badge.critical {
  background: #fee2e2;
  color: #991b1b;
}

.severity-badge.high {
  background: #fed7aa;
  color: #9a3412;
}

.severity-badge.medium {
  background: #fef3c7;
  color: #92400e;
}

.priority-badge.high {
  background: #fed7aa;
  color: #9a3412;
}

.priority-badge.medium {
  background: #fef3c7;
  color: #92400e;
}

.priority-badge.low {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.applied {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.pending {
  background: #fef3c7;
  color: #92400e;
}

.hardening-actions,
.patch-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.patch-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item .label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.detail-item .value {
  font-size: 15px;
  color: #1a1a1a;
  font-weight: 600;
}

/* Buttons */
.btn-primary,
.btn-secondary {
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  font-size: 14px;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: white;
  border: 2px solid #e5e7eb;
  color: #374151;
}

.btn-secondary:hover {
  border-color: #667eea;
  color: #667eea;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: white;
  border-radius: 16px;
}

.empty-icon {
  width: 80px;
  height: 80px;
  color: #9ca3af;
  margin: 0 auto 24px;
}

.empty-state h2 {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 12px;
}

.empty-state p {
  color: #6b7280;
}

/* Responsive */
@media (max-width: 768px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .threat-header,
  .hardening-header,
  .patch-header {
    flex-direction: column;
    gap: 12px;
  }

  .threat-details {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
