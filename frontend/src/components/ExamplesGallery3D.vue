<template>
  <div class="examples-gallery-3d">
    <div class="gallery-container" ref="galleryContainer">
      <canvas ref="canvas" class="gallery-canvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import * as THREE from 'three'
import { gsap } from 'gsap'

const router = useRouter()
const galleryContainer = ref(null)
const canvas = ref(null)

let scene, camera, renderer, raycaster, mouse
let cardMeshes = []
let animationId = null
let hoveredCardMesh = null

const examples = [
  {
    id: '1',
    title: 'SQL Injection Detection & Prevention',
    description: 'AI-powered detection of SQL injection attempts with real-time query analysis and automatic blocking mechanisms.',
    color: '#673ee6'
  },
  {
    id: '2',
    title: 'Cross-Site Scripting (XSS) Protection',
    description: 'Multi-layered XSS detection using content analysis and browser-level protection mechanisms to prevent script injection.',
    color: '#00b090'
  },
  {
    id: '3',
    title: 'DDoS Attack Mitigation',
    description: 'Distributed denial-of-service protection with intelligent traffic analysis, rate limiting, and load balancing.',
    color: '#8b5cf6'
  },
  {
    id: '4',
    title: 'Zero-Day Exploit Detection',
    description: 'Machine learning-based detection of previously unknown vulnerabilities and attack patterns before patches are available.',
    color: '#34d399'
  },
  {
    id: '5',
    title: 'Ransomware Defense System',
    description: 'Multi-stage ransomware detection and prevention with automated backup protection and behavioral analysis.',
    color: '#f59e0b'
  },
  {
    id: '6',
    title: 'API Authentication Bypass Prevention',
    description: 'Advanced authentication and authorization monitoring for API endpoints with token validation and rate limiting.',
    color: '#ef4444'
  },
  {
    id: '7',
    title: 'Privilege Escalation Detection',
    description: 'Monitor and prevent unauthorized privilege elevation attempts across systems with real-time permission tracking.',
    color: '#10b981'
  },
  {
    id: '8',
    title: 'Phishing Detection & Response',
    description: 'AI-powered email and website analysis to identify and block phishing attempts including spear-phishing campaigns.',
    color: '#6366f1'
  },
  {
    id: '9',
    title: 'Man-in-the-Middle Attack Prevention',
    description: 'Secure communication monitoring and encryption verification to prevent MITM attacks and traffic interception.',
    color: '#ec4899'
  },
  {
    id: '10',
    title: 'Insider Threat Detection',
    description: 'Behavioral analytics to identify malicious or negligent insider activities before data breaches occur.',
    color: '#14b8a6'
  },
  {
    id: '11',
    title: 'Cryptojacking Prevention',
    description: 'Detect and block unauthorized cryptocurrency mining activities on systems and browsers through resource monitoring.',
    color: '#f97316'
  },
  {
    id: '12',
    title: 'Remote Code Execution (RCE) Defense',
    description: 'Prevent unauthorized code execution through input validation, sandboxing, and command injection detection.',
    color: '#8b5cf6'
  },
  {
    id: '13',
    title: 'Data Exfiltration Prevention',
    description: 'Monitor and block unauthorized data transfers and sensitive information leaks across all communication channels.',
    color: '#06b6d4'
  },
  {
    id: '14',
    title: 'Brute Force Attack Protection',
    description: 'Intelligent rate limiting and lockout mechanisms to prevent credential attacks with adaptive CAPTCHA challenges.',
    color: '#a855f7'
  },
  {
    id: '15',
    title: 'XML External Entity (XXE) Protection',
    description: 'Secure XML parsing to prevent XXE injection attacks and data exposure through entity validation.',
    color: '#f59e0b'
  },
  {
    id: '16',
    title: 'Server-Side Request Forgery (SSRF) Prevention',
    description: 'Validate and restrict server-side requests to prevent SSRF exploitation and internal resource access.',
    color: '#ef4444'
  },
  {
    id: '17',
    title: 'Session Hijacking Prevention',
    description: 'Secure session management with continuous validation and anomaly detection to prevent session theft.',
    color: '#10b981'
  },
  {
    id: '18',
    title: 'DNS Tunneling Detection',
    description: 'Identify and block data exfiltration and C&C communications via DNS protocol through query pattern analysis.',
    color: '#3b82f6'
  },
  {
    id: '19',
    title: 'Business Logic Flaw Detection',
    description: 'Identify and prevent exploitation of application business logic vulnerabilities through workflow monitoring.',
    color: '#8b5cf6'
  },
  {
    id: '20',
    title: 'Container Escape Prevention',
    description: 'Monitor and prevent container breakout attempts in containerized environments with syscall monitoring.',
    color: '#06b6d4'
  }
]

function init3DGallery() {
  if (!galleryContainer.value || !canvas.value) return

  const container = galleryContainer.value
  const canvasElement = canvas.value

  // Scene setup
  scene = new THREE.Scene()
  
  // Camera setup
  camera = new THREE.PerspectiveCamera(
    50, 
    container.offsetWidth / container.offsetHeight, 
    0.1, 
    1000
  )
  camera.position.set(0, 1, 12)
  camera.lookAt(0, 0, 0)
  
  // Renderer setup
  renderer = new THREE.WebGLRenderer({ 
    canvas: canvasElement,
    antialias: true, 
    alpha: true 
  })
  renderer.setSize(container.offsetWidth, container.offsetHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  
  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.8)
  scene.add(ambientLight)
  
  const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.6)
  directionalLight1.position.set(10, 10, 10)
  directionalLight1.castShadow = true
  directionalLight1.shadow.mapSize.width = 1024
  directionalLight1.shadow.mapSize.height = 1024
  scene.add(directionalLight1)
  
  const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.4)
  directionalLight2.position.set(-10, -10, 10)
  scene.add(directionalLight2)
  
  // Raycaster for mouse interaction
  raycaster = new THREE.Raycaster()
  mouse = new THREE.Vector2()
  
  createCards()
  setupEventListeners()
  animate()
}

function createCards() {
  const cardWidth = 8
  const cardHeight = 5
  const totalCards = examples.length

  examples.forEach((example, index) => {
    // Card geometry - large cards
    const geometry = new THREE.PlaneGeometry(cardWidth, cardHeight)
    
    // Create canvas texture for card with text
    const canvasTexture = createCardTexture(example)
    
    // Card material with canvas texture
    const material = new THREE.MeshLambertMaterial({
      map: canvasTexture,
      transparent: true,
      opacity: 0.95,
      side: THREE.DoubleSide
    })
    
    // Create mesh
    const cardMesh = new THREE.Mesh(geometry, material)
    
    // Position cards stacked one after another with heavy tilt in center
    // Create a cascading/stacked effect
    const centerOffset = (index - totalCards / 2) * 0.3
    const x = centerOffset
    const y = -index * 0.15 // Slight vertical offset for stacking
    const z = -index * 0.8 - 2 // Cards go deeper into the scene
    
    // Heavy tilt - each card tilted more as it goes back
    const rotationY = -0.25 + index * 0.01 // Tilt sideways
    const rotationX = -0.2 - index * 0.02 // Tilt downward
    
    cardMesh.position.set(x, y, z)
    cardMesh.rotation.set(rotationX, rotationY, 0)
    cardMesh.userData = { 
      index, 
      example,
      originalPosition: { x, y, z },
      originalRotation: { x: rotationX, y: rotationY, z: 0 },
      isHovered: false
    }
    
    // Add shadow
    cardMesh.castShadow = true
    cardMesh.receiveShadow = true
    
    scene.add(cardMesh)
    cardMeshes.push(cardMesh)
  })
}

function createCardTexture(example) {
  const canvas = document.createElement('canvas')
  canvas.width = 1600
  canvas.height = 1000
  const ctx = canvas.getContext('2d')
  
  // More transparent black background
  ctx.fillStyle = 'rgba(0, 0, 0, 0.75)'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  
  // Subtle gradient overlay from accent color
  const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height)
  gradient.addColorStop(0, example.color + '30') // More transparent
  gradient.addColorStop(0.6, 'rgba(15, 15, 25, 0.4)')
  gradient.addColorStop(1, 'rgba(5, 5, 10, 0.7)')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  
  // Border
  ctx.strokeStyle = example.color
  ctx.lineWidth = 8
  ctx.strokeRect(20, 20, canvas.width - 40, canvas.height - 40)
  
  // Hexagonal pattern in background (abstract tech pattern)
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)'
  ctx.lineWidth = 1
  for (let y = 0; y < canvas.height; y += 80) {
    for (let x = 0; x < canvas.width; x += 140) {
      drawHexagon(ctx, x, y, 35)
    }
  }
  
  // Security Icon (shield) - top left
  drawShieldIcon(ctx, 80, 80, 60, example.color)
  
  // Severity Badge - top right
  const severity = getSeverity(example.id)
  drawSeverityBadge(ctx, canvas.width - 250, 70, severity)
  
  // Title with shadow
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 64px Arial, sans-serif'
  ctx.textAlign = 'left'
  ctx.shadowColor = 'rgba(0, 0, 0, 0.9)'
  ctx.shadowBlur = 20
  ctx.shadowOffsetX = 4
  ctx.shadowOffsetY = 4
  
  const titleLines = wrapText(ctx, example.title, canvas.width - 180)
  let currentY = 200
  titleLines.forEach((line, i) => {
    ctx.fillText(line, 80, currentY + i * 80)
  })
  
  // Reset shadow
  ctx.shadowColor = 'transparent'
  ctx.shadowBlur = 0
  ctx.shadowOffsetX = 0
  ctx.shadowOffsetY = 0
  
  // Description
  ctx.fillStyle = '#e0e0e0'
  ctx.font = '38px Arial, sans-serif'
  ctx.shadowColor = 'rgba(0, 0, 0, 0.7)'
  ctx.shadowBlur = 10
  ctx.shadowOffsetX = 2
  ctx.shadowOffsetY = 2
  
  const descLines = wrapText(ctx, example.description, canvas.width - 180)
  const startY = currentY + titleLines.length * 80 + 50
  descLines.slice(0, 4).forEach((line, i) => {
    ctx.fillText(line, 80, startY + i * 55)
  })
  
  ctx.shadowColor = 'transparent'
  ctx.shadowBlur = 0
  
  // Statistics Section (empty space utilization)
  const statsY = startY + 250
  
  // Detection Time
  drawStatBox(ctx, 80, statsY, 'Detection Time', '< 50ms', example.color)
  
  // Attacks Blocked
  drawStatBox(ctx, 420, statsY, 'Blocked', '250K+', '#00b090')
  
  // Success Rate
  drawStatBox(ctx, 760, statsY, 'Success Rate', '99.5%', '#10b981')
  
  // Threat Level Progress Bar
  drawThreatLevel(ctx, 80, statsY + 140, canvas.width - 160, getThreatLevel(example.id), example.color)
  
  // "Click to learn more" hint at bottom
  ctx.fillStyle = '#00b090'
  ctx.font = 'bold 36px Arial, sans-serif'
  ctx.textAlign = 'center'
  ctx.shadowColor = 'rgba(0, 0, 0, 0.8)'
  ctx.shadowBlur = 12
  ctx.fillText('Click to learn more →', canvas.width / 2, canvas.height - 70)
  
  const texture = new THREE.CanvasTexture(canvas)
  texture.minFilter = THREE.LinearFilter
  texture.magFilter = THREE.LinearFilter
  return texture
}

// Helper function to draw hexagon pattern
function drawHexagon(ctx, x, y, size) {
  ctx.beginPath()
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i
    const hx = x + size * Math.cos(angle)
    const hy = y + size * Math.sin(angle)
    if (i === 0) ctx.moveTo(hx, hy)
    else ctx.lineTo(hx, hy)
  }
  ctx.closePath()
  ctx.stroke()
}

// Helper function to draw shield icon
function drawShieldIcon(ctx, x, y, size, color) {
  ctx.save()
  ctx.fillStyle = color + '40'
  ctx.strokeStyle = color
  ctx.lineWidth = 3
  
  // Shield shape
  ctx.beginPath()
  ctx.moveTo(x, y)
  ctx.lineTo(x - size/2, y + size/4)
  ctx.lineTo(x - size/2, y + size/1.5)
  ctx.quadraticCurveTo(x - size/2, y + size, x, y + size * 1.2)
  ctx.quadraticCurveTo(x + size/2, y + size, x + size/2, y + size/1.5)
  ctx.lineTo(x + size/2, y + size/4)
  ctx.closePath()
  ctx.fill()
  ctx.stroke()
  
  // Checkmark
  ctx.strokeStyle = '#ffffff'
  ctx.lineWidth = 4
  ctx.beginPath()
  ctx.moveTo(x - size/4, y + size/2)
  ctx.lineTo(x - size/8, y + size/1.5)
  ctx.lineTo(x + size/3, y + size/3)
  ctx.stroke()
  
  ctx.restore()
}

// Helper function to draw severity badge
function drawSeverityBadge(ctx, x, y, severity) {
  const colors = {
    'Critical': '#ef4444',
    'High': '#f97316',
    'Medium': '#eab308',
    'Low': '#10b981'
  }
  
  ctx.save()
  ctx.fillStyle = colors[severity] || '#6b7280'
  ctx.font = 'bold 28px Arial, sans-serif'
  
  const text = severity.toUpperCase()
  const metrics = ctx.measureText(text)
  const padding = 20
  
  // Background
  ctx.globalAlpha = 0.9
  ctx.fillRect(x - padding, y - 30, metrics.width + padding * 2, 50)
  
  // Text
  ctx.globalAlpha = 1
  ctx.fillStyle = '#ffffff'
  ctx.fillText(text, x, y)
  
  ctx.restore()
}

// Helper function to draw stat boxes
function drawStatBox(ctx, x, y, label, value, color) {
  ctx.save()
  
  // Box background
  ctx.fillStyle = 'rgba(0, 0, 0, 0.4)'
  ctx.fillRect(x, y, 280, 100)
  
  // Border
  ctx.strokeStyle = color
  ctx.lineWidth = 2
  ctx.strokeRect(x, y, 280, 100)
  
  // Label
  ctx.fillStyle = '#a0a0a0'
  ctx.font = '22px Arial, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText(label, x + 20, y + 35)
  
  // Value
  ctx.fillStyle = color
  ctx.font = 'bold 32px VT323, monospace'
  ctx.fillText(value, x + 20, y + 75)
  
  ctx.restore()
}

// Helper function to draw threat level bar
function drawThreatLevel(ctx, x, y, width, level, color) {
  ctx.save()
  
  // Label
  ctx.fillStyle = '#ffffff'
  ctx.font = '26px Arial, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('Threat Level Detected:', x, y - 10)
  
  // Background bar
  ctx.fillStyle = 'rgba(255, 255, 255, 0.1)'
  ctx.fillRect(x, y + 10, width, 30)
  
  // Progress bar
  const progressWidth = (width * level) / 100
  const barGradient = ctx.createLinearGradient(x, 0, x + progressWidth, 0)
  barGradient.addColorStop(0, color)
  barGradient.addColorStop(1, '#00b090')
  ctx.fillStyle = barGradient
  ctx.fillRect(x, y + 10, progressWidth, 30)
  
  // Percentage text
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 24px Arial, sans-serif'
  ctx.textAlign = 'right'
  ctx.fillText(level + '%', x + width + 80, y + 35)
  
  ctx.restore()
}

// Get severity based on vulnerability ID
function getSeverity(id) {
  const severities = ['Critical', 'High', 'Medium', 'Low']
  const criticalIds = ['1', '3', '4', '5', '12', '20']
  const highIds = ['2', '6', '7', '8', '9', '10', '13', '16', '17', '19']
  
  if (criticalIds.includes(id)) return 'Critical'
  if (highIds.includes(id)) return 'High'
  return Math.random() > 0.5 ? 'Medium' : 'Low'
}

// Get threat level percentage
function getThreatLevel(id) {
  const levels = {
    '1': 95, '2': 88, '3': 92, '4': 97, '5': 94,
    '6': 85, '7': 89, '8': 86, '9': 83, '10': 78,
    '11': 72, '12': 91, '13': 87, '14': 75, '15': 82,
    '16': 84, '17': 88, '18': 70, '19': 80, '20': 96
  }
  return levels[id] || 80
}

function wrapText(ctx, text, maxWidth) {
  const words = text.split(' ')
  const lines = []
  let currentLine = ''
  
  words.forEach(word => {
    const testLine = currentLine ? `${currentLine} ${word}` : word
    const metrics = ctx.measureText(testLine)
    
    if (metrics.width > maxWidth && currentLine) {
      lines.push(currentLine)
      currentLine = word
    } else {
      currentLine = testLine
    }
  })
  
  if (currentLine) {
    lines.push(currentLine)
  }
  
  return lines
}

function setupEventListeners() {
  const container = galleryContainer.value
  
  // Mouse move for interaction
  container.addEventListener('mousemove', onMouseMove)
  container.addEventListener('click', onMouseClick)
  container.addEventListener('mouseleave', onMouseLeave)
  
  // Resize handler
  window.addEventListener('resize', onWindowResize)
}

function onMouseMove(event) {
  const container = galleryContainer.value
  const rect = container.getBoundingClientRect()
  
  // Calculate mouse position in normalized device coordinates
  mouse.x = ((event.clientX - rect.left) / container.offsetWidth) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / container.offsetHeight) * 2 + 1
  
  // Update raycaster
  raycaster.setFromCamera(mouse, camera)
  
  // Check for intersections
  const intersects = raycaster.intersectObjects(cardMeshes)
  
  // Reset previously hovered card
  if (hoveredCardMesh && hoveredCardMesh.userData.isHovered) {
    hoveredCardMesh.userData.isHovered = false
    animateCardOut(hoveredCardMesh)
    hoveredCardMesh = null
  }
  
  // Hover effect - only pop out card
  if (intersects.length > 0) {
    const intersectedCard = intersects[0].object
    if (!intersectedCard.userData.isHovered) {
      intersectedCard.userData.isHovered = true
      hoveredCardMesh = intersectedCard
      animateCardHover(intersectedCard)
    }
  }
  
  // Mouse parallax effect - rotate view based on mouse
  const mouseInfluenceX = 2.5
  const mouseInfluenceY = 1.5
  camera.position.x = mouse.x * mouseInfluenceX
  camera.position.y = 1 + mouse.y * mouseInfluenceY
  camera.lookAt(0, -2, 0)
}

function onMouseClick(event) {
  const intersects = raycaster.intersectObjects(cardMeshes)
  if (intersects.length > 0) {
    const clickedCard = intersects[0].object
    const vulnerabilityId = clickedCard.userData.example.id
    
    // Navigate to vulnerability detail page
    router.push(`/vulnerability/${vulnerabilityId}`)
  }
}

function onMouseLeave() {
  hoveredCard.value = null
  cardMeshes.forEach(mesh => {
    if (mesh.userData.isHovered) {
      mesh.userData.isHovered = false
      animateCardOut(mesh)
    }
  })
}

function animateCardHover(cardMesh) {
  // Move card forward and scale up
  gsap.to(cardMesh.position, {
    z: cardMesh.userData.originalPosition.z + 2.5,
    duration: 0.4,
    ease: "power2.out"
  })
  
  gsap.to(cardMesh.scale, {
    x: 1.1,
    y: 1.1,
    z: 1.1,
    duration: 0.4,
    ease: "power2.out"
  })
  
  // Slightly adjust rotation for better view
  gsap.to(cardMesh.rotation, {
    x: cardMesh.userData.originalRotation.x + 0.05,
    duration: 0.4,
    ease: "power2.out"
  })
}

function animateCardOut(cardMesh) {
  gsap.to(cardMesh.position, {
    z: cardMesh.userData.originalPosition.z,
    duration: 0.4,
    ease: "power2.out"
  })
  
  gsap.to(cardMesh.scale, {
    x: 1,
    y: 1,
    z: 1,
    duration: 0.4,
    ease: "power2.out"
  })
  
  gsap.to(cardMesh.rotation, {
    x: cardMesh.userData.originalRotation.x,
    duration: 0.4,
    ease: "power2.out"
  })
}

// Navigation functions removed - mouse-driven only

function onWindowResize() {
  const container = galleryContainer.value
  if (!container) return
  
  camera.aspect = container.offsetWidth / container.offsetHeight
  camera.updateProjectionMatrix()
  renderer.setSize(container.offsetWidth, container.offsetHeight)
}

function animate() {
  animationId = requestAnimationFrame(animate)
  
  // Gentle floating animation
  cardMeshes.forEach((mesh, index) => {
    const time = Date.now() * 0.001
    mesh.position.y = Math.sin(time + index * 0.5) * 0.1
  })
  
  renderer.render(scene, camera)
}

onMounted(() => {
  setTimeout(() => {
    init3DGallery()
  }, 100)
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  if (renderer) {
    renderer.dispose()
  }
  window.removeEventListener('resize', onWindowResize)
})
</script>

<style scoped>
.examples-gallery-3d {
  width: 100%;
  height: 700px;
  position: relative;
  background: linear-gradient(135deg, #0f0f23, #1a1b2e);
  overflow: hidden;
  border-radius: 20px;
  margin: 4rem 0;
}

.gallery-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.gallery-canvas {
  width: 100%;
  height: 100%;
  cursor: pointer;
}

/* No overlay styles needed - all styling is in card texture */

/* Responsive Design */
@media (max-width: 768px) {
  .examples-gallery-3d {
    height: 400px;
  }
  
  .gallery-info {
    top: 1rem;
    left: 1rem;
    right: 1rem;
    max-width: none;
    padding: 1rem;
  }
  
  .gallery-controls {
    bottom: 1rem;
    padding: 0.75rem;
  }
}
</style>