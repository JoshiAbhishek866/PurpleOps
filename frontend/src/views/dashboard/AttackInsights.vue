<template>
  <div class="attack-insights-page">
    <h1 class="page-title">Attack Insights</h1>
    <p class="page-subtitle">
      Offensive security scan results - Vulnerabilities, exploits, and
      reconnaissance data
    </p>

    <!-- Scan Results -->
    <div v-if="hasScanResults" class="insights-content">
      <!-- Vulnerability Summary Cards -->
      <div class="summary-grid">
        <div class="summary-card critical">
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
            <h4>Critical</h4>
            <p class="card-value">{{ vulnerabilities.critical }}</p>
            <span class="card-label">CVSS 9.0-10.0</span>
          </div>
        </div>

        <div class="summary-card high">
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
                d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
              />
            </svg>
          </div>
          <div class="card-content">
            <h4>High</h4>
            <p class="card-value">{{ vulnerabilities.high }}</p>
            <span class="card-label">CVSS 7.0-8.9</span>
          </div>
        </div>

        <div class="summary-card medium">
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
                d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
              />
            </svg>
          </div>
          <div class="card-content">
            <h4>Medium</h4>
            <p class="card-value">{{ vulnerabilities.medium }}</p>
            <span class="card-label">CVSS 4.0-6.9</span>
          </div>
        </div>

        <div class="summary-card low">
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
                d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div class="card-content">
            <h4>Low</h4>
            <p class="card-value">{{ vulnerabilities.low }}</p>
            <span class="card-label">CVSS 0.1-3.9</span>
          </div>
        </div>
      </div>

      <!-- Vulnerabilities List -->
      <div class="vulnerabilities-section">
        <h2>Discovered Vulnerabilities</h2>
        <div class="vulnerabilities-list">
          <div
            v-for="vuln in sortedVulnerabilities"
            :key="vuln.id"
            class="vuln-card"
          >
            <div class="vuln-header">
              <div class="vuln-title-section">
                <h4>{{ vuln.title }}</h4>
                <span class="vuln-id">{{ vuln.cve || vuln.id }}</span>
              </div>
              <div class="vuln-badges">
                <span class="severity-badge" :class="vuln.severity">
                  {{ vuln.severity }}
                </span>
                <span class="cvss-badge"> CVSS {{ vuln.cvss }} </span>
                <span class="priority-badge" :class="vuln.priority">
                  {{ vuln.priority }} Priority
                </span>
              </div>
            </div>

            <p class="vuln-description">{{ vuln.description }}</p>

            <div class="vuln-details">
              <div class="detail-row">
                <span class="detail-label">Affected Component:</span>
                <span class="detail-value">{{ vuln.component }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Attack Vector:</span>
                <span class="detail-value">{{ vuln.attackVector }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Exploit Available:</span>
                <span
                  class="detail-value"
                  :class="vuln.exploitAvailable ? 'text-red' : 'text-green'"
                >
                  {{ vuln.exploitAvailable ? "Yes" : "No" }}
                </span>
              </div>
            </div>

            <div class="vuln-actions">
              <button @click="showVulnDetails(vuln)" class="btn-secondary">
                View Full Details
              </button>
              <button @click="showPatchModal(vuln)" class="btn-primary">
                Apply Patch
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Reconnaissance Data -->
      <div class="recon-section">
        <h2>Reconnaissance Data</h2>
        <div class="recon-grid">
          <div class="recon-card">
            <h4>Open Ports</h4>
            <div class="port-list">
              <span v-for="port in openPorts" :key="port" class="port-badge">
                {{ port }}
              </span>
            </div>
          </div>
          <div class="recon-card">
            <h4>Services Detected</h4>
            <ul class="service-list">
              <li v-for="service in services" :key="service">{{ service }}</li>
            </ul>
          </div>
          <div class="recon-card">
            <h4>Technologies</h4>
            <div class="tech-list">
              <span v-for="tech in technologies" :key="tech" class="tech-badge">
                {{ tech }}
              </span>
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
          d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5"
        />
      </svg>
      <h2>No Attack Data Available</h2>
      <p>Run a security scan to see offensive security insights</p>
    </div>

    <!-- Vulnerability Details Modal -->
    <Transition name="modal">
      <div v-if="selectedVuln" class="modal-overlay" @click="closeVulnDetails">
        <div class="modal-container vuln-details-modal" @click.stop>
          <div class="modal-header">
            <h2>Vulnerability Details</h2>
            <button @click="closeVulnDetails" class="close-btn">
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
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="vuln-detail-header">
              <h3>{{ selectedVuln.title }}</h3>
              <div class="badges">
                <span class="severity-badge" :class="selectedVuln.severity">{{
                  selectedVuln.severity
                }}</span>
                <span class="cvss-badge">CVSS {{ selectedVuln.cvss }}</span>
              </div>
            </div>

            <div class="detail-section">
              <h4>How This Vulnerability Was Discovered</h4>
              <div class="discovery-timeline">
                <div
                  v-for="(step, index) in selectedVuln.discoverySteps"
                  :key="index"
                  class="timeline-item"
                >
                  <div class="timeline-marker">{{ index + 1 }}</div>
                  <div class="timeline-content">
                    <h5>{{ step.title }}</h5>
                    <p>{{ step.description }}</p>
                    <div v-if="step.code" class="code-block">
                      <pre>{{ step.code }}</pre>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>Technical Details</h4>
              <div class="tech-details-grid">
                <div class="tech-detail">
                  <span class="label">CVE ID:</span>
                  <span class="value">{{ selectedVuln.cve }}</span>
                </div>
                <div class="tech-detail">
                  <span class="label">CVSS Score:</span>
                  <span class="value"
                    >{{ selectedVuln.cvss }} ({{ selectedVuln.severity }})</span
                  >
                </div>
                <div class="tech-detail">
                  <span class="label">Attack Vector:</span>
                  <span class="value">{{ selectedVuln.attackVector }}</span>
                </div>
                <div class="tech-detail">
                  <span class="label">Attack Complexity:</span>
                  <span class="value">{{ selectedVuln.attackComplexity }}</span>
                </div>
                <div class="tech-detail">
                  <span class="label">Privileges Required:</span>
                  <span class="value">{{
                    selectedVuln.privilegesRequired
                  }}</span>
                </div>
                <div class="tech-detail">
                  <span class="label">User Interaction:</span>
                  <span class="value">{{ selectedVuln.userInteraction }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>Impact Analysis</h4>
              <div class="impact-grid">
                <div class="impact-item">
                  <span class="impact-label">Confidentiality:</span>
                  <span
                    class="impact-value"
                    :class="
                      'impact-' +
                      selectedVuln.impact.confidentiality.toLowerCase()
                    "
                  >
                    {{ selectedVuln.impact.confidentiality }}
                  </span>
                </div>
                <div class="impact-item">
                  <span class="impact-label">Integrity:</span>
                  <span
                    class="impact-value"
                    :class="
                      'impact-' + selectedVuln.impact.integrity.toLowerCase()
                    "
                  >
                    {{ selectedVuln.impact.integrity }}
                  </span>
                </div>
                <div class="impact-item">
                  <span class="impact-label">Availability:</span>
                  <span
                    class="impact-value"
                    :class="
                      'impact-' + selectedVuln.impact.availability.toLowerCase()
                    "
                  >
                    {{ selectedVuln.impact.availability }}
                  </span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>Proof of Concept</h4>
              <div class="poc-content">
                <p>{{ selectedVuln.proofOfConcept.description }}</p>
                <div class="code-block">
                  <pre>{{ selectedVuln.proofOfConcept.code }}</pre>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>References</h4>
              <ul class="references-list">
                <li
                  v-for="(ref, index) in selectedVuln.references"
                  :key="index"
                >
                  <a :href="ref.url" target="_blank">{{ ref.title }}</a>
                </li>
              </ul>
            </div>
          </div>

          <div class="modal-footer">
            <button @click="closeVulnDetails" class="btn-secondary">
              Close
            </button>
            <button @click="showPatchModal(selectedVuln)" class="btn-primary">
              Apply Patch
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Patch Application Modal -->
    <Transition name="modal">
      <div v-if="patchModalVuln" class="modal-overlay" @click="closePatchModal">
        <div class="modal-container patch-modal" @click.stop>
          <div class="modal-header">
            <h2>Apply Security Patch</h2>
            <button @click="closePatchModal" class="close-btn">
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
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="patch-info">
              <h3>Patch for: {{ patchModalVuln.title }}</h3>
              <p class="patch-description">
                {{ patchModalVuln.patch.description }}
              </p>
            </div>

            <div class="patch-section">
              <h4>Patch Details</h4>
              <div class="patch-details-grid">
                <div class="patch-detail">
                  <span class="label">Patch Version:</span>
                  <span class="value">{{ patchModalVuln.patch.version }}</span>
                </div>
                <div class="patch-detail">
                  <span class="label">Release Date:</span>
                  <span class="value">{{
                    patchModalVuln.patch.releaseDate
                  }}</span>
                </div>
                <div class="patch-detail">
                  <span class="label">Estimated Time:</span>
                  <span class="value">{{
                    patchModalVuln.patch.estimatedTime
                  }}</span>
                </div>
                <div class="patch-detail">
                  <span class="label">Requires Restart:</span>
                  <span class="value">{{
                    patchModalVuln.patch.requiresRestart ? "Yes" : "No"
                  }}</span>
                </div>
              </div>
            </div>

            <div class="patch-section">
              <h4>What This Patch Will Do</h4>
              <ul class="patch-actions-list">
                <li
                  v-for="(action, index) in patchModalVuln.patch.actions"
                  :key="index"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke-width="1.5"
                    stroke="currentColor"
                    class="check-icon"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  {{ action }}
                </li>
              </ul>
            </div>

            <div class="patch-section">
              <h4>Pre-Patch Checklist</h4>
              <div class="checklist">
                <label
                  v-for="(item, index) in patchModalVuln.patch.checklist"
                  :key="index"
                  class="checkbox-item"
                >
                  <input type="checkbox" v-model="patchChecklist[index]" />
                  <span>{{ item }}</span>
                </label>
              </div>
            </div>

            <div v-if="patchProgress.active" class="patch-section">
              <h4>Patch Progress</h4>
              <div class="progress-container">
                <div class="progress-bar">
                  <div
                    class="progress-fill"
                    :style="{ width: patchProgress.percentage + '%' }"
                  ></div>
                </div>
                <p class="progress-text">
                  {{ patchProgress.currentStep }} ({{
                    patchProgress.percentage
                  }}%)
                </p>
              </div>
              <div class="progress-logs">
                <div
                  v-for="(log, index) in patchProgress.logs"
                  :key="index"
                  class="log-entry"
                >
                  <span class="log-time">{{ log.time }}</span>
                  <span class="log-message">{{ log.message }}</span>
                </div>
              </div>
            </div>

            <div
              v-if="patchProgress.completed"
              class="patch-section success-message"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="1.5"
                stroke="currentColor"
                class="success-icon"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <h4>Patch Applied Successfully!</h4>
              <p>
                The vulnerability has been patched. Your system is now secure.
              </p>
            </div>
          </div>

          <div class="modal-footer">
            <button @click="closePatchModal" class="btn-secondary">
              Cancel
            </button>
            <button
              @click="applyPatch"
              :disabled="!allChecklistComplete || patchProgress.active"
              class="btn-primary"
            >
              {{ patchProgress.active ? "Applying..." : "Apply Patch" }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useSecurityStore } from "@/stores/security";
import { usePatchStore } from "@/stores/patches";

const securityStore = useSecurityStore();
const patchStore = usePatchStore();

// State
const selectedVuln = ref(null);
const patchModalVuln = ref(null);
const patchChecklist = ref([]);
const patchProgress = ref({
  active: false,
  completed: false,
  percentage: 0,
  currentStep: "",
  logs: [],
});

// Mock vulnerabilities data with detailed discovery information
const vulnerabilitiesData = ref([
  {
    id: "CVE-2024-0001",
    cve: "CVE-2024-0001",
    title: "SQL Injection in Login Form",
    description:
      "Improper input validation allows SQL injection attacks through the login form",
    severity: "critical",
    cvss: 9.8,
    priority: "immediate",
    component: "Authentication Module",
    attackVector: "Network",
    attackComplexity: "Low",
    privilegesRequired: "None",
    userInteraction: "None",
    exploitAvailable: true,
    discoverySteps: [
      {
        title: "Initial Reconnaissance",
        description:
          "Scanner identified login form at /auth/login endpoint during automated crawling",
        code: "GET /auth/login HTTP/1.1\nHost: target.com",
      },
      {
        title: "Input Validation Testing",
        description:
          "Tested various SQL injection payloads in username and password fields",
        code: "username: admin' OR '1'='1\npassword: anything",
      },
      {
        title: "Vulnerability Confirmation",
        description:
          "Successfully bypassed authentication using SQL injection, confirming the vulnerability",
        code: "Response: 200 OK\nSet-Cookie: session=authenticated\nLocation: /dashboard",
      },
      {
        title: "Impact Assessment",
        description:
          "Verified ability to extract database contents and escalate privileges",
      },
    ],
    impact: {
      confidentiality: "High",
      integrity: "High",
      availability: "High",
    },
    proofOfConcept: {
      description:
        "The following payload demonstrates the SQL injection vulnerability:",
      code: `POST /auth/login HTTP/1.1
Host: target.com
Content-Type: application/json

{
  "username": "admin' OR '1'='1' --",
  "password": "anything"
}

Response: Successfully authenticated as admin`,
    },
    references: [
      {
        title: "OWASP SQL Injection",
        url: "https://owasp.org/www-community/attacks/SQL_Injection",
      },
      {
        title: "CWE-89: SQL Injection",
        url: "https://cwe.mitre.org/data/definitions/89.html",
      },
      {
        title: "CVE-2024-0001 Details",
        url: "https://nvd.nist.gov/vuln/detail/CVE-2024-0001",
      },
    ],
    patch: {
      version: "1.2.3",
      releaseDate: "2024-01-15",
      description:
        "Security patch that implements parameterized queries and input validation",
      estimatedTime: "5-10 minutes",
      requiresRestart: true,
      actions: [
        "Replace direct SQL queries with parameterized statements",
        "Implement input validation and sanitization",
        "Add rate limiting to login endpoint",
        "Enable SQL injection detection in WAF",
        "Update authentication middleware",
      ],
      checklist: [
        "Backup current database",
        "Notify active users of upcoming restart",
        "Verify backup integrity",
        "Review patch notes and changelog",
      ],
    },
  },
  {
    id: "CVE-2024-0002",
    cve: "CVE-2024-0002",
    title: "Cross-Site Scripting (XSS) Vulnerability",
    description: "Reflected XSS vulnerability in search functionality",
    severity: "high",
    cvss: 7.5,
    priority: "high",
    component: "Search Module",
    attackVector: "Network",
    attackComplexity: "Low",
    privilegesRequired: "None",
    userInteraction: "Required",
    exploitAvailable: false,
    discoverySteps: [
      {
        title: "Endpoint Discovery",
        description: "Identified search functionality at /search endpoint",
        code: "GET /search?q=test HTTP/1.1",
      },
      {
        title: "XSS Payload Testing",
        description: "Tested various XSS payloads in search parameter",
        code: `GET /search?q=${"<"}script${">"}alert(1)${"<"}/script${">"}`,
      },
      {
        title: "Vulnerability Confirmation",
        description: "Confirmed XSS execution in search results page",
        code: "Response contained unescaped script tag in HTML",
      },
    ],
    impact: {
      confidentiality: "Low",
      integrity: "Low",
      availability: "None",
    },
    proofOfConcept: {
      description: "XSS payload that executes in user context:",
      code: `GET /search?q=${"<"}img src=x onerror=alert(document.cookie)${">"}

Result: Cookie theft via JavaScript execution`,
    },
    references: [
      {
        title: "OWASP XSS Guide",
        url: "https://owasp.org/www-community/attacks/xss/",
      },
      {
        title: "CWE-79: XSS",
        url: "https://cwe.mitre.org/data/definitions/79.html",
      },
    ],
    patch: {
      version: "1.2.4",
      releaseDate: "2024-01-16",
      description: "Implements output encoding and Content Security Policy",
      estimatedTime: "3-5 minutes",
      requiresRestart: false,
      actions: [
        "Add output encoding for user input",
        "Implement Content Security Policy headers",
        "Enable XSS protection in browser",
        "Sanitize search query parameters",
      ],
      checklist: [
        "Test search functionality after patch",
        "Verify CSP headers are present",
        "Check for any broken functionality",
      ],
    },
  },
]);

// Reconnaissance data
const openPorts = ref([22, 80, 443, 3306, 8080]);
const services = ref([
  "SSH (OpenSSH 8.2)",
  "HTTP (nginx 1.18.0)",
  "HTTPS (nginx 1.18.0)",
  "MySQL (5.7.33)",
  "HTTP-Proxy (8080)",
]);
const technologies = ref([
  "PHP 7.4",
  "MySQL",
  "nginx",
  "WordPress 5.8",
  "jQuery 3.6",
]);

// Computed
const hasScanResults = computed(() => vulnerabilitiesData.value.length > 0);

const vulnerabilities = computed(() => {
  const summary = { critical: 0, high: 0, medium: 0, low: 0 };
  vulnerabilitiesData.value.forEach((v) => {
    if (v.cvss >= 9.0) summary.critical++;
    else if (v.cvss >= 7.0) summary.high++;
    else if (v.cvss >= 4.0) summary.medium++;
    else summary.low++;
  });
  return summary;
});

const sortedVulnerabilities = computed(() => {
  return [...vulnerabilitiesData.value].sort((a, b) => b.cvss - a.cvss);
});

const allChecklistComplete = computed(() => {
  return patchChecklist.value.every((item) => item === true);
});

// Methods
const showVulnDetails = (vuln) => {
  selectedVuln.value = vuln;
};

const closeVulnDetails = () => {
  selectedVuln.value = null;
};

const showPatchModal = (vuln) => {
  closeVulnDetails();
  patchModalVuln.value = vuln;
  patchChecklist.value = new Array(vuln.patch.checklist.length).fill(false);
  patchProgress.value = {
    active: false,
    completed: false,
    percentage: 0,
    currentStep: "",
    logs: [],
  };
};

const closePatchModal = () => {
  patchModalVuln.value = null;
  patchChecklist.value = [];
  patchProgress.value = {
    active: false,
    completed: false,
    percentage: 0,
    currentStep: "",
    logs: [],
  };
};

const applyPatch = async () => {
  if (!allChecklistComplete.value) return;

  patchProgress.value.active = true;
  patchProgress.value.logs = [];

  const steps = [
    { step: "Preparing patch environment...", duration: 1000, percentage: 20 },
    { step: "Downloading patch files...", duration: 1500, percentage: 40 },
    { step: "Applying security fixes...", duration: 2000, percentage: 60 },
    { step: "Running validation tests...", duration: 1500, percentage: 80 },
    { step: "Finalizing patch...", duration: 1000, percentage: 100 },
  ];

  for (const { step, duration, percentage } of steps) {
    patchProgress.value.currentStep = step;
    patchProgress.value.percentage = percentage;
    patchProgress.value.logs.push({
      time: new Date().toLocaleTimeString(),
      message: step,
    });

    await new Promise((resolve) => setTimeout(resolve, duration));
  }

  patchProgress.value.active = false;
  patchProgress.value.completed = true;
  patchProgress.value.logs.push({
    time: new Date().toLocaleTimeString(),
    message: "✓ Patch applied successfully!",
  });

  // Wait 2 seconds to show success message, then close modal and remove vulnerability
  await new Promise((resolve) => setTimeout(resolve, 2000));

  // Add to patched vulnerabilities store
  patchStore.addPatchedVulnerability(patchModalVuln.value);

  // Remove the patched vulnerability from the list
  const vulnIndex = vulnerabilitiesData.value.findIndex(
    (v) => v.id === patchModalVuln.value.id,
  );
  if (vulnIndex !== -1) {
    vulnerabilitiesData.value.splice(vulnIndex, 1);
  }

  // Close the modal
  closePatchModal();
};

// Lifecycle
onMounted(async () => {
  // TODO: Fetch actual scan results from API
});
</script>

<style scoped>
.attack-insights-page {
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

.summary-card.critical {
  border-left-color: #dc2626;
}

.summary-card.high {
  border-left-color: #f59e0b;
}

.summary-card.medium {
  border-left-color: #fbbf24;
}

.summary-card.low {
  border-left-color: #10b981;
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

.critical .card-icon {
  background: #fee2e2;
  color: #dc2626;
}

.high .card-icon {
  background: #fed7aa;
  color: #f59e0b;
}

.medium .card-icon {
  background: #fef3c7;
  color: #fbbf24;
}

.low .card-icon {
  background: #d1fae5;
  color: #10b981;
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

/* Vulnerabilities Section */
.vulnerabilities-section {
  margin-bottom: 32px;
}

.vulnerabilities-section h2 {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 20px;
}

.vulnerabilities-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.vuln-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-left: 4px solid;
}

.vuln-card:has(.severity-badge.critical) {
  border-left-color: #dc2626;
}

.vuln-card:has(.severity-badge.high) {
  border-left-color: #f59e0b;
}

.vuln-card:has(.severity-badge.medium) {
  border-left-color: #fbbf24;
}

.vuln-card:has(.severity-badge.low) {
  border-left-color: #10b981;
}

.vuln-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 16px;
}

.vuln-title-section h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 4px 0;
}

.vuln-id {
  font-size: 13px;
  color: #6b7280;
  font-family: monospace;
}

.vuln-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.severity-badge,
.cvss-badge,
.priority-badge {
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

.severity-badge.low {
  background: #d1fae5;
  color: #065f46;
}

.cvss-badge {
  background: #e0e7ff;
  color: #3730a3;
}

.priority-badge.immediate {
  background: #fee2e2;
  color: #991b1b;
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

.vuln-description {
  color: #374151;
  margin-bottom: 16px;
  line-height: 1.6;
}

.vuln-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.detail-value {
  font-size: 14px;
  color: #1a1a1a;
  font-weight: 600;
}

.text-red {
  color: #dc2626;
}

.text-green {
  color: #10b981;
}

.vuln-actions {
  display: flex;
  gap: 12px;
}

/* Reconnaissance Section */
.recon-section {
  margin-bottom: 32px;
}

.recon-section h2 {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 20px;
}

.recon-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.recon-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.recon-card h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #1a1a1a;
}

.port-list,
.tech-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.port-badge,
.tech-badge {
  background: #ede9fe;
  color: #5b21b6;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
}

.service-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.service-list li {
  padding: 8px 0;
  border-bottom: 1px solid #e5e7eb;
  color: #374151;
}

.service-list li:last-child {
  border-bottom: none;
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

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
  overflow-y: auto;
}

.modal-container {
  background: white;
  border-radius: 16px;
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 30px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s;
  color: #6b7280;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #1a1a1a;
}

.close-btn svg {
  width: 20px;
  height: 20px;
}

.modal-body {
  padding: 30px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 30px;
  border-top: 1px solid #e5e7eb;
}

/* Vulnerability Details Modal */
.vuln-detail-header {
  margin-bottom: 24px;
}

.vuln-detail-header h3 {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 12px;
}

.vuln-detail-header .badges {
  display: flex;
  gap: 8px;
}

.detail-section {
  margin-bottom: 32px;
}

.detail-section h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #374151;
}

.discovery-timeline {
  position: relative;
  padding-left: 40px;
}

.discovery-timeline::before {
  content: "";
  position: absolute;
  left: 15px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #e5e7eb;
}

.timeline-item {
  position: relative;
  margin-bottom: 24px;
}

.timeline-marker {
  position: absolute;
  left: -40px;
  width: 32px;
  height: 32px;
  background: #667eea;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.timeline-content h5 {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #1a1a1a;
}

.timeline-content p {
  color: #6b7280;
  margin-bottom: 12px;
  line-height: 1.6;
}

.code-block {
  background: #1e1e1e;
  border-radius: 8px;
  padding: 16px;
  margin-top: 12px;
  overflow-x: auto;
}

.code-block pre {
  color: #d4d4d4;
  font-family: "Courier New", monospace;
  font-size: 13px;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.tech-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.tech-detail {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
}

.tech-detail .label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.tech-detail .value {
  font-size: 14px;
  color: #1a1a1a;
  font-weight: 600;
}

.impact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.impact-item {
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.impact-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.impact-value {
  font-size: 14px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 12px;
}

.impact-high {
  background: #fee2e2;
  color: #991b1b;
}

.impact-low {
  background: #fef3c7;
  color: #92400e;
}

.impact-none {
  background: #d1fae5;
  color: #065f46;
}

.poc-content p {
  color: #374151;
  margin-bottom: 16px;
  line-height: 1.6;
}

.references-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.references-list li {
  padding: 8px 0;
  border-bottom: 1px solid #e5e7eb;
}

.references-list li:last-child {
  border-bottom: none;
}

.references-list a {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.references-list a:hover {
  text-decoration: underline;
}

/* Patch Modal */
.patch-info {
  margin-bottom: 24px;
}

.patch-info h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.patch-description {
  color: #6b7280;
  line-height: 1.6;
}

.patch-section {
  margin-bottom: 24px;
}

.patch-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.patch-detail {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
}

.patch-detail .label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.patch-detail .value {
  font-size: 14px;
  color: #1a1a1a;
  font-weight: 600;
}

.patch-actions-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.patch-actions-list li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 8px;
  color: #374151;
}

.check-icon {
  width: 20px;
  height: 20px;
  color: #10b981;
  flex-shrink: 0;
}

.checklist {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.checkbox-item:hover {
  background: #f3f4f6;
}

.checkbox-item input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.progress-container {
  margin-bottom: 16px;
}

.progress-bar {
  height: 12px;
  background: #f3f4f6;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: #667eea;
  transition: width 0.3s ease;
  border-radius: 6px;
}

.progress-text {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  text-align: center;
}

.progress-logs {
  max-height: 200px;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 8px;
  padding: 16px;
}

.log-entry {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
  font-family: "Courier New", monospace;
  font-size: 13px;
}

.log-time {
  color: #10b981;
}

.log-message {
  color: #d4d4d4;
}

.success-message {
  text-align: center;
  padding: 32px;
  background: #d1fae5;
  border-radius: 12px;
}

.success-icon {
  width: 64px;
  height: 64px;
  color: #10b981;
  margin: 0 auto 16px;
}

.success-message h4 {
  font-size: 20px;
  font-weight: 700;
  color: #065f46;
  margin-bottom: 8px;
}

.success-message p {
  color: #047857;
}

/* Modal Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .summary-grid,
  .recon-grid {
    grid-template-columns: 1fr;
  }

  .vuln-header {
    flex-direction: column;
  }

  .modal-container {
    max-width: 100%;
    margin: 0;
    border-radius: 0;
  }

  .discovery-timeline {
    padding-left: 30px;
  }

  .timeline-marker {
    left: -30px;
    width: 24px;
    height: 24px;
    font-size: 12px;
  }
}
</style>
