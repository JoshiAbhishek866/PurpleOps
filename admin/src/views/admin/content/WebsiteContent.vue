<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useAdminDataStore } from '@/stores/adminData'
import { useRoute } from 'vue-router'

const dataStore = useAdminDataStore()
const route = useRoute()
const isLoading = ref(true)
const activeSection = ref('hero')
const isSaving = ref(false)
const saveMessage = ref('')

const sections = [
  { key: 'header', name: 'Header & Navigation', icon: 'cil-menu' },
  { key: 'footer', name: 'Footer', icon: 'cil-layers' },
  { key: 'hero', name: 'Hero Section', icon: 'cil-home' },
  { key: 'achievements', name: 'Achievements', icon: 'cil-chart' },
  { key: 'features', name: 'Features', icon: 'cil-puzzle' },
  { key: 'services', name: 'Services', icon: 'cil-briefcase' },
  { key: 'offensive_model', name: 'Offensive Model', icon: 'cil-shield-alt' },
  { key: 'defensive_model', name: 'Defensive Model', icon: 'cil-lock-locked' },
  { key: 'demo_cta', name: 'Demo CTA', icon: 'cil-bullhorn' },
  { key: 'about_hero', name: 'About Hero', icon: 'cil-info' },
  { key: 'about_mission', name: 'Mission', icon: 'cil-target' },
  { key: 'about_vision', name: 'Vision', icon: 'cil-lightbulb' },
  { key: 'about_values', name: 'Values', icon: 'cil-heart' },
]

const content = computed(() => dataStore.content)
const currentContent = computed(() => content.value[activeSection.value]?.content || {})

onMounted(async () => {
  await dataStore.fetchContent()
  
  // Check if there's a section query parameter
  if (route.query.section) {
    const sectionKey = route.query.section
    if (sections.find(s => s.key === sectionKey)) {
      activeSection.value = sectionKey
    }
  }
  
  isLoading.value = false
})

// Watch for query parameter changes
watch(() => route.query.section, (newSection) => {
  if (newSection && sections.find(s => s.key === newSection)) {
    activeSection.value = newSection
  }
})


async function saveContent() {
  isSaving.value = true
  saveMessage.value = ''
  const result = await dataStore.updateContent(activeSection.value, currentContent.value)
  if (result.success) {
    saveMessage.value = 'Content saved successfully!'
    setTimeout(() => saveMessage.value = '', 3000)
  } else {
    saveMessage.value = `Error: ${result.error}`
  }
  isSaving.value = false
}

function addItem(arrayKey) {
  if (!currentContent.value[arrayKey]) currentContent.value[arrayKey] = []
  currentContent.value[arrayKey].push({ id: Date.now(), title: '', description: '' })
}

function removeItem(arrayKey, index) {
  currentContent.value[arrayKey].splice(index, 1)
}

// Header-specific functions
function initializeNavLinks() {
  if (!content.value[activeSection.value]) {
    content.value[activeSection.value] = { content: {} }
  }
  content.value[activeSection.value].content.navLinks = [
    { name: 'Home', path: '/' },
    { name: 'About', path: '/about' },
    { name: 'Blog', path: '/blog' }
  ]
}

function addNavLink() {
  if (!currentContent.value.navLinks) {
    currentContent.value.navLinks = []
  }
  currentContent.value.navLinks.push({ name: '', path: '' })
}

function removeNavLink(index) {
  currentContent.value.navLinks.splice(index, 1)
}

// Footer-specific functions
function initializeFooterSections() {
  if (!content.value[activeSection.value]) {
    content.value[activeSection.value] = { content: {} }
  }
  content.value[activeSection.value].content.sections = [
    {
      title: 'Product',
      links: [
        { name: 'Features', path: '/' },
        { name: 'Security', path: '/about' }
      ]
    }
  ]
  content.value[activeSection.value].content.socialLinks = [
    { name: 'LinkedIn', url: '#', icon: 'linkedin' }
  ]
}

function initializeSocialLinks() {
  if (!content.value[activeSection.value]) {
    content.value[activeSection.value] = { content: {} }
  }
  content.value[activeSection.value].content.socialLinks = []
}

// Hero animation settings
function initializeAnimation() {
  if (!content.value[activeSection.value]) {
    content.value[activeSection.value] = { content: {} }
  }
  content.value[activeSection.value].content.animation = {
    modelPath: '/lock.glb',
    primaryColor: '#673ee6',
    secondaryColor: '#00b090',
    scale: 3,
    autoRotate: false,
    rotationSpeed: 0.005
  }
}

// Achievements management
function initializeAchievements() {
  if (!content.value[activeSection.value]) {
    content.value[activeSection.value] = { content: {} }
  }
  content.value[activeSection.value].content.achievementsTitle = 'Trusted by Industry Leaders'
  content.value[activeSection.value].content.achievements = [
    { id: 1, target: 50, suffix: 'M+', label: 'Threats Blocked Daily', decimals: 0 },
    { id: 2, target: 99.9, suffix: '%', label: 'Uptime Guarantee', decimals: 1 },
    { id: 3, target: 500, suffix: '+', label: 'Enterprise Clients', decimals: 0 },
    { id: 4, target: 24, suffix: '/7', label: 'Security Monitoring', decimals: 0 }
  ]
}

function addAchievement() {
  if (!currentContent.value.achievements) {
    currentContent.value.achievements = []
  }
  const newId = currentContent.value.achievements.length > 0 
    ? Math.max(...currentContent.value.achievements.map(a => a.id)) + 1 
    : 1
  currentContent.value.achievements.push({
    id: newId,
    target: 0,
    suffix: '',
    label: '',
    decimals: 0
  })
}

</script>

<template>
  <div>
    <CCard class="mb-4">
      <CCardHeader class="d-flex justify-content-between align-items-center">
        <strong>Website Content Management</strong>
        <CButton color="primary" @click="saveContent" :disabled="isSaving" data-testid="save-content-btn">
          <CSpinner v-if="isSaving" size="sm" class="me-2" />{{ isSaving ? 'Saving...' : 'Save Changes' }}
        </CButton>
      </CCardHeader>
      <CCardBody>
        <CAlert v-if="saveMessage" :color="saveMessage.includes('Error') ? 'danger' : 'success'">{{ saveMessage }}</CAlert>
        <div v-if="isLoading" class="text-center py-5"><CSpinner color="primary" /></div>
        <div v-else>
          <CCard>
            <CCardHeader><strong>{{ sections.find(s => s.key === activeSection)?.name }}</strong></CCardHeader>
            <CCardBody>
                <template v-if="activeSection === 'hero'">
                  <div class="mb-3"><CFormLabel>Title</CFormLabel><CFormInput v-model="currentContent.title" /></div>
                  <div class="mb-3"><CFormLabel>Subtitle</CFormLabel><CFormInput v-model="currentContent.subtitle" /></div>
                  <div class="mb-3"><CFormLabel>Description</CFormLabel><CFormTextarea v-model="currentContent.description" rows="4" /></div>
                  <CRow><CCol :md="6"><div class="mb-3"><CFormLabel>Primary Button Text</CFormLabel><CFormInput v-model="currentContent.primaryButtonText" /></div></CCol><CCol :md="6"><div class="mb-3"><CFormLabel>Primary Button Link</CFormLabel><CFormInput v-model="currentContent.primaryButtonLink" /></div></CCol></CRow>
                  
                  <hr class="my-4" />
                  
                  <h5 class="mb-3">3D Animation Settings</h5>
                  <div v-if="!currentContent.animation">
                    <CButton color="secondary" @click="initializeAnimation">Initialize Animation Settings</CButton>
                  </div>
                  <div v-else>
                    <CRow>
                      <CCol :md="6">
                        <div class="mb-3">
                          <CFormLabel>Model Path</CFormLabel>
                          <CFormInput v-model="currentContent.animation.modelPath" placeholder="/lock.glb" />
                          <small class="text-muted">Path to the 3D model file (e.g., /lock.glb)</small>
                        </div>
                      </CCol>
                      <CCol :md="6">
                        <div class="mb-3">
                          <CFormLabel>Scale</CFormLabel>
                          <CFormInput v-model.number="currentContent.animation.scale" type="number" step="0.1" placeholder="3" />
                          <small class="text-muted">Size of the 3D model (default: 3)</small>
                        </div>
                      </CCol>
                    </CRow>
                    <CRow>
                      <CCol :md="6">
                        <div class="mb-3">
                          <CFormLabel>Primary Color</CFormLabel>
                          <CFormInput v-model="currentContent.animation.primaryColor" type="color" />
                          <small class="text-muted">Primary light color (default: #673ee6)</small>
                        </div>
                      </CCol>
                      <CCol :md="6">
                        <div class="mb-3">
                          <CFormLabel>Secondary Color</CFormLabel>
                          <CFormInput v-model="currentContent.animation.secondaryColor" type="color" />
                          <small class="text-muted">Secondary light color (default: #00b090)</small>
                        </div>
                      </CCol>
                    </CRow>
                    <CRow>
                      <CCol :md="6">
                        <div class="mb-3">
                          <CFormCheck 
                            v-model="currentContent.animation.autoRotate" 
                            label="Enable Auto-Rotation"
                          />
                          <small class="text-muted">Automatically rotate the 3D model</small>
                        </div>
                      </CCol>
                      <CCol :md="6">
                        <div class="mb-3">
                          <CFormLabel>Rotation Speed</CFormLabel>
                          <CFormInput v-model.number="currentContent.animation.rotationSpeed" type="number" step="0.001" placeholder="0.005" />
                          <small class="text-muted">Speed of auto-rotation (default: 0.005)</small>
                        </div>
                      </CCol>
                    </CRow>
                  </div>
                  
                  <hr class="my-4" />
                  
                  <h5 class="mb-3">Achievements Section</h5>
                  <div class="mb-3">
                    <CFormLabel>Section Title</CFormLabel>
                    <CFormInput v-model="currentContent.achievementsTitle" placeholder="Trusted by Industry Leaders" />
                  </div>
                  <div v-if="!currentContent.achievements || currentContent.achievements.length === 0">
                    <CButton color="secondary" @click="initializeAchievements">Initialize Achievements</CButton>
                  </div>
                  <div v-else>
                    <div v-for="(achievement, index) in currentContent.achievements" :key="index" class="border rounded p-3 mb-3">
                      <div class="d-flex justify-content-between mb-2">
                        <strong>Achievement {{ index + 1 }}</strong>
                        <CButton color="danger" size="sm" @click="currentContent.achievements.splice(index, 1)">
                          <CIcon icon="cil-trash" />
                        </CButton>
                      </div>
                      <CRow>
                        <CCol :md="3">
                          <CFormLabel>Target Number</CFormLabel>
                          <CFormInput v-model.number="achievement.target" type="number" step="0.1" placeholder="50" />
                        </CCol>
                        <CCol :md="2">
                          <CFormLabel>Suffix</CFormLabel>
                          <CFormInput v-model="achievement.suffix" placeholder="M+" />
                        </CCol>
                        <CCol :md="5">
                          <CFormLabel>Label</CFormLabel>
                          <CFormInput v-model="achievement.label" placeholder="Threats Blocked Daily" />
                        </CCol>
                        <CCol :md="2">
                          <CFormLabel>Decimals</CFormLabel>
                          <CFormInput v-model.number="achievement.decimals" type="number" min="0" max="2" placeholder="0" />
                        </CCol>
                      </CRow>
                    </div>
                    <CButton color="secondary" variant="outline" @click="addAchievement">
                      <CIcon icon="cil-plus" class="me-2" />Add Achievement
                    </CButton>
                  </div>
                  
                  <hr class="my-4" />
                  
                  <h5 class="mb-3">Demo CTA Section</h5>
                  <CRow>
                    <CCol :md="6">
                      <div class="mb-3">
                        <CFormLabel>Title Line 1</CFormLabel>
                        <CFormInput v-model="currentContent.demoTitle" placeholder="Ready to Protect Your" />
                      </div>
                    </CCol>
                    <CCol :md="6">
                      <div class="mb-3">
                        <CFormLabel>Title Line 2</CFormLabel>
                        <CFormInput v-model="currentContent.demoTitle2" placeholder="Organization?" />
                      </div>
                    </CCol>
                  </CRow>
                  <div class="mb-3">
                    <CFormLabel>Description</CFormLabel>
                    <CFormTextarea v-model="currentContent.demoDescription" rows="3" placeholder="Get a personalized demonstration..." />
                  </div>
                  <CRow>
                    <CCol :md="6">
                      <div class="mb-3">
                        <CFormLabel>Button Text</CFormLabel>
                        <CFormInput v-model="currentContent.demoButtonText" placeholder="Schedule Your Demo Today" />
                      </div>
                    </CCol>
                    <CCol :md="6">
                      <div class="mb-3">
                        <CFormLabel>Button Link</CFormLabel>
                        <CFormInput v-model="currentContent.demoButtonLink" placeholder="/book-demo" />
                      </div>
                    </CCol>
                  </CRow>
                </template>
                
                <!-- Header & Navigation -->
                <template v-else-if="activeSection === 'header'">
                  <div class="mb-4">
                    <h5 class="mb-3">Navigation Links</h5>
                    <div v-if="!currentContent.navLinks || currentContent.navLinks.length === 0">
                      <CButton color="primary" @click="initializeNavLinks">Initialize Navigation Links</CButton>
                    </div>
                    <div v-else>
                      <div v-for="(link, index) in currentContent.navLinks" :key="index" class="border rounded p-3 mb-3">
                        <div class="d-flex justify-content-between mb-2">
                          <strong>Link {{ index + 1 }}</strong>
                          <CButton color="danger" size="sm" @click="removeNavLink(index)">
                            <CIcon icon="cil-trash" />
                          </CButton>
                        </div>
                        <CRow>
                          <CCol :md="6">
                            <CFormLabel>Link Name</CFormLabel>
                            <CFormInput v-model="link.name" placeholder="e.g., Home" />
                          </CCol>
                          <CCol :md="6">
                            <CFormLabel>Link Path</CFormLabel>
                            <CFormInput v-model="link.path" placeholder="e.g., /" />
                          </CCol>
                        </CRow>
                      </div>
                      <CButton color="primary" variant="outline" @click="addNavLink">
                        <CIcon icon="cil-plus" class="me-2" />Add Navigation Link
                      </CButton>
                    </div>
                  </div>
                </template>
                
                <!-- Footer -->
                <template v-else-if="activeSection === 'footer'">
                  <div class="mb-4">
                    <h5 class="mb-3">Footer Sections</h5>
                    <div v-if="!currentContent.sections || currentContent.sections.length === 0">
                      <CButton color="primary" @click="initializeFooterSections">Initialize Footer Sections</CButton>
                    </div>
                    <div v-else>
                      <div v-for="(section, sectionIndex) in currentContent.sections" :key="sectionIndex" class="border rounded p-3 mb-4">
                        <div class="d-flex justify-content-between mb-3">
                          <strong>Section {{ sectionIndex + 1 }}</strong>
                          <CButton color="danger" size="sm" @click="currentContent.sections.splice(sectionIndex, 1)">
                            <CIcon icon="cil-trash" />
                          </CButton>
                        </div>
                        <div class="mb-3">
                          <CFormLabel>Section Title</CFormLabel>
                          <CFormInput v-model="section.title" placeholder="e.g., Product" />
                        </div>
                        <div class="mb-2">
                          <strong>Links</strong>
                        </div>
                        <div v-if="!section.links" class="mb-2">
                          <CButton color="secondary" size="sm" @click="section.links = []">Add Links</CButton>
                        </div>
                        <div v-else>
                          <div v-for="(link, linkIndex) in section.links" :key="linkIndex" class="border-start border-3 ps-3 mb-2">
                            <CRow class="align-items-end">
                              <CCol :md="5">
                                <CFormLabel class="small">Link Name</CFormLabel>
                                <CFormInput v-model="link.name" size="sm" placeholder="e.g., Features" />
                              </CCol>
                              <CCol :md="5">
                                <CFormLabel class="small">Link Path</CFormLabel>
                                <CFormInput v-model="link.path" size="sm" placeholder="e.g., /" />
                              </CCol>
                              <CCol :md="2">
                                <CButton color="danger" size="sm" @click="section.links.splice(linkIndex, 1)">
                                  <CIcon icon="cil-trash" />
                                </CButton>
                              </CCol>
                            </CRow>
                          </div>
                          <CButton color="secondary" variant="outline" size="sm" @click="section.links.push({ name: '', path: '' })">
                            <CIcon icon="cil-plus" class="me-1" />Add Link
                          </CButton>
                        </div>
                      </div>
                      <CButton color="primary" variant="outline" @click="currentContent.sections.push({ title: '', links: [] })">
                        <CIcon icon="cil-plus" class="me-2" />Add Footer Section
                      </CButton>
                    </div>
                  </div>
                  
                  <hr class="my-4" />
                  
                  <div class="mb-4">
                    <h5 class="mb-3">Social Links</h5>
                    <div v-if="!currentContent.socialLinks || currentContent.socialLinks.length === 0">
                      <CButton color="primary" @click="initializeSocialLinks">Initialize Social Links</CButton>
                    </div>
                    <div v-else>
                      <div v-for="(social, index) in currentContent.socialLinks" :key="index" class="border rounded p-3 mb-3">
                        <div class="d-flex justify-content-between mb-2">
                          <strong>Social Link {{ index + 1 }}</strong>
                          <CButton color="danger" size="sm" @click="currentContent.socialLinks.splice(index, 1)">
                            <CIcon icon="cil-trash" />
                          </CButton>
                        </div>
                        <CRow>
                          <CCol :md="4">
                            <CFormLabel>Platform Name</CFormLabel>
                            <CFormInput v-model="social.name" placeholder="e.g., LinkedIn" />
                          </CCol>
                          <CCol :md="4">
                            <CFormLabel>URL</CFormLabel>
                            <CFormInput v-model="social.url" placeholder="e.g., https://linkedin.com/..." />
                          </CCol>
                          <CCol :md="4">
                            <CFormLabel>Icon</CFormLabel>
                            <CFormInput v-model="social.icon" placeholder="e.g., linkedin" />
                          </CCol>
                        </CRow>
                      </div>
                      <CButton color="primary" variant="outline" @click="currentContent.socialLinks.push({ name: '', url: '', icon: '' })">
                        <CIcon icon="cil-plus" class="me-2" />Add Social Link
                      </CButton>
                    </div>
                  </div>
                </template>
                
                <!-- About Hero -->
                <template v-else-if="activeSection === 'about_hero'">
                  <div class="mb-3"><CFormLabel>Title</CFormLabel><CFormInput v-model="currentContent.title" /></div>
                  <div class="mb-3"><CFormLabel>Description</CFormLabel><CFormTextarea v-model="currentContent.description" rows="3" /></div>
                </template>
                <!-- Mission/Vision -->
                <template v-else-if="activeSection === 'about_mission' || activeSection === 'about_vision'">
                  <div class="mb-3"><CFormLabel>Title</CFormLabel><CFormInput v-model="currentContent.title" /></div>
                  <div class="mb-3"><CFormLabel>Text</CFormLabel><CFormTextarea v-model="currentContent.text" rows="5" /></div>
                </template>
                <!-- Demo CTA -->
                <template v-else-if="activeSection === 'demo_cta'">
                  <div class="mb-3"><CFormLabel>Title</CFormLabel><CFormInput v-model="currentContent.title" /></div>
                  <div class="mb-3"><CFormLabel>Description</CFormLabel><CFormTextarea v-model="currentContent.description" rows="3" /></div>
                  <CRow><CCol :md="6"><div class="mb-3"><CFormLabel>Button Text</CFormLabel><CFormInput v-model="currentContent.buttonText" /></div></CCol><CCol :md="6"><div class="mb-3"><CFormLabel>Button Link</CFormLabel><CFormInput v-model="currentContent.buttonLink" /></div></CCol></CRow>
                </template>
                <!-- Offensive/Defensive Model -->
                <template v-else-if="activeSection === 'offensive_model' || activeSection === 'defensive_model'">
                  <div class="mb-3"><CFormLabel>Title</CFormLabel><CFormInput v-model="currentContent.title" /></div>
                  <div class="mb-3"><CFormLabel>Description</CFormLabel><CFormTextarea v-model="currentContent.description" rows="3" /></div>
                  <div class="mb-3"><CFormLabel>Features (one per line)</CFormLabel><CFormTextarea :value="currentContent.features?.join('\n')" @input="currentContent.features = $event.target.value.split('\n')" rows="5" /></div>
                </template>
                <!-- Footer -->
                <template v-else-if="activeSection === 'footer'">
                  <div class="mb-3"><CFormLabel>Company Name</CFormLabel><CFormInput v-model="currentContent.companyName" /></div>
                  <div class="mb-3"><CFormLabel>Tagline</CFormLabel><CFormInput v-model="currentContent.tagline" /></div>
                  <div class="mb-3"><CFormLabel>Copyright Text</CFormLabel><CFormInput v-model="currentContent.copyrightText" /></div>
                </template>
                <!-- Achievements -->
                <template v-else-if="activeSection === 'achievements'">
                  <div v-for="(item, index) in currentContent.items" :key="index" class="border rounded p-3 mb-3">
                    <div class="d-flex justify-content-between mb-2"><strong>Item {{ index + 1 }}</strong><CButton color="danger" size="sm" @click="removeItem('items', index)"><CIcon icon="cil-trash" /></CButton></div>
                    <CRow><CCol :md="6"><CFormLabel>Number</CFormLabel><CFormInput v-model="item.number" /></CCol><CCol :md="6"><CFormLabel>Label</CFormLabel><CFormInput v-model="item.label" /></CCol></CRow>
                  </div>
                  <CButton color="primary" variant="outline" @click="addItem('items')"><CIcon icon="cil-plus" class="me-2" />Add Item</CButton>
                </template>
                <!-- Features -->
                <template v-else-if="activeSection === 'features'">
                  <div class="mb-3"><CFormLabel>Section Title</CFormLabel><CFormInput v-model="currentContent.title" /></div>
                  <hr />
                  <div v-for="(feature, index) in currentContent.features" :key="index" class="border rounded p-3 mb-3">
                    <div class="d-flex justify-content-between mb-2"><strong>Feature {{ index + 1 }}</strong><CButton color="danger" size="sm" @click="removeItem('features', index)"><CIcon icon="cil-trash" /></CButton></div>
                    <div class="mb-2"><CFormLabel>Title</CFormLabel><CFormInput v-model="feature.title" /></div>
                    <div class="mb-2"><CFormLabel>Description</CFormLabel><CFormTextarea v-model="feature.description" rows="2" /></div>
                    <div class="mb-2"><CFormLabel>Benefit</CFormLabel><CFormInput v-model="feature.benefit" /></div>
                  </div>
                  <CButton color="primary" variant="outline" @click="addItem('features')"><CIcon icon="cil-plus" class="me-2" />Add Feature</CButton>
                </template>
                <!-- Services -->
                <template v-else-if="activeSection === 'services'">
                  <div class="mb-3"><CFormLabel>Section Title</CFormLabel><CFormInput v-model="currentContent.title" /></div>
                  <hr />
                  <div v-for="(service, index) in currentContent.services" :key="index" class="border rounded p-3 mb-3">
                    <div class="d-flex justify-content-between mb-2"><strong>Service {{ index + 1 }}</strong><CButton color="danger" size="sm" @click="removeItem('services', index)"><CIcon icon="cil-trash" /></CButton></div>
                    <div class="mb-2"><CFormLabel>Name</CFormLabel><CFormInput v-model="service.name" /></div>
                    <div class="mb-2"><CFormLabel>Description</CFormLabel><CFormTextarea v-model="service.description" rows="2" /></div>
                  </div>
                  <CButton color="primary" variant="outline" @click="addItem('services')"><CIcon icon="cil-plus" class="me-2" />Add Service</CButton>
                </template>
                <!-- Values -->
                <template v-else-if="activeSection === 'about_values'">
                  <div v-for="(value, index) in currentContent.values" :key="index" class="border rounded p-3 mb-3">
                    <div class="d-flex justify-content-between mb-2"><strong>Value {{ index + 1 }}</strong><CButton color="danger" size="sm" @click="removeItem('values', index)"><CIcon icon="cil-trash" /></CButton></div>
                    <div class="mb-2"><CFormLabel>Title</CFormLabel><CFormInput v-model="value.title" /></div>
                    <div class="mb-2"><CFormLabel>Description</CFormLabel><CFormTextarea v-model="value.description" rows="2" /></div>
                  </div>
                  <CButton color="primary" variant="outline" @click="addItem('values')"><CIcon icon="cil-plus" class="me-2" />Add Value</CButton>
                </template>
                <template v-else><CAlert color="info">Select a section from the sidebar dropdown to edit.</CAlert></template>
              </CCardBody>
            </CCard>
          </div>
      </CCardBody>
    </CCard>
  </div>
</template>
