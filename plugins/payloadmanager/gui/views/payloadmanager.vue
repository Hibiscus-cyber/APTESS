<template>
  <div class="payloads-container">
    <!-- Header -->
    <div class="header-section">
      <h2>恶意载荷库</h2>
      <p>
        恶意载荷是可在攻击操作中使用的特定恶意文件或脚本。
        载荷按平台和ATT&CK战术组织，包含MD5哈希、文件类型、威胁等级
        和相关技术等元数据。
      </p>
    </div>
    <hr />

    <!-- Main Content -->
    <div class="columns">
      <!-- Filters Sidebar -->
      <div class="column is-2 filters">
        <button class="button is-primary is-small is-fullwidth mb-4" @click="createPayload">
          + 创建载荷
        </button>
        <button class="button is-info is-small is-fullwidth mb-2" @click="showImportModal = true">
          📥 导入
        </button>
        <button class="button is-success is-small is-fullwidth mb-2" @click="exportPayloads">
          📤 导出
        </button>
        
        <p class="has-text-weight-bold">筛选条件</p>
        <form>
          <div class="field">
            <label class="label is-small">搜索</label>
            <div class="control has-icons-left">
              <input 
                class="input is-small" 
                v-model="searchTerm" 
                type="text" 
                placeholder="搜索载荷..." 
                @keyup="filterPayloads"
              />
              <span class="icon is-small is-left">
                <i class="fas fa-search"></i>
              </span>
            </div>
          </div>
          
          <div class="field">
            <label class="label is-small">平台</label>
            <div class="control pl-3">
              <div v-for="platform in platforms" :key="platform">
                <label class="checkbox mb-2">
                  <input 
                    type="checkbox" 
                    v-model="selectedPlatforms[platform]" 
                    @change="filterPayloads"
                  />
                  <span>{{ getPlatformDisplayName(platform) }}</span>
                </label>
                <br />
              </div>
            </div>
          </div>
          
          <div class="field">
            <label class="label is-small">战术</label>
            <div class="control">
              <div class="select is-small is-fullwidth">
                <select v-model="selectedTactic" @change="filterPayloads">
                  <option value="">全部</option>
                  <option v-for="tactic in tactics" :key="tactic" :value="tactic">
                    {{ getTacticDisplayName(tactic) }}
                  </option>
                </select>
              </div>
            </div>
          </div>
          
          <div class="field">
            <label class="label is-small">威胁等级</label>
            <div class="control">
              <div class="select is-small is-fullwidth">
                <select v-model="selectedThreatLevel" @change="filterPayloads">
                  <option value="">全部</option>
                  <option v-for="level in threatLevels" :key="level" :value="level">
                    {{ getThreatLevelDisplayName(level) }}
                  </option>
                </select>
              </div>
            </div>
          </div>
        </form>
        
        <button 
          class="button is-small is-fullwidth mb-2" 
          v-show="searchTerm || selectedTactic || selectedThreatLevel" 
          @click="clearFilters"
        >
          清除筛选
        </button>
        
        <p class="has-text-centered">
          <strong>{{ filteredPayloads.length }}</strong>
          /
          <span>{{ payloads.length }}</span>&nbsp;
          个载荷
        </p>
      </div>

      <!-- Payloads Grid -->
      <div class="column is-10 payloads-grid">
        <div v-show="!isLoaded">
          <p>正在加载，请稍候...</p>
        </div>
        
        <div 
          v-for="payload in filteredPayloads" 
          :key="payload.payload_id"
          class="box mb-2 mr-2 p-3 payload-card" 
          @click="selectPayload(payload)"
        >
          <div class="level is-mobile">
            <div class="level-left">
              <div class="level-item">
                <span 
                  class="tag" 
                  :class="getThreatLevelColor(payload.threat_level)"
                >
                  {{ payload.threat_level }}
                </span>
              </div>
            </div>
            <div class="level-right">
              <div class="level-item">
                <span class="tag is-light">{{ payload.file_type }}</span>
              </div>
            </div>
          </div>
          
          <p>
            <span class="has-text-weight-bold">{{ payload.name }}</span>
          </p>
          <p class="help mb-1">{{ payload.description }}</p>
          
          <div class="tags">
            <span 
              v-for="platform in payload.platforms" 
              :key="platform"
              class="tag is-small"
            >
              {{ platform }}
            </span>
            <span 
              v-for="tactic in payload.tactics" 
              :key="tactic"
              class="tag is-small is-info"
            >
              {{ tactic }}
            </span>
          </div>
          
          <div class="is-size-7 has-text-grey mt-2">
            <div class="level is-mobile">
              <div class="level-left">
                <div class="level-item">
                  <span>{{ getFileSizeDisplay(payload.file_size) }}</span>
                </div>
              </div>
              <div class="level-right">
                <div class="level-item">
                  <span v-show="payload.md5">
                    MD5: <code>{{ payload.md5.substring(0, 8) }}</code>
                  </span>
                </div>
              </div>
            </div>
            <div v-show="payload.payload_file" class="mt-1">
              <div class="level is-mobile">
                <div class="level-left">
                  <div class="level-item">
                    <span class="has-text-weight-bold">文件位置:</span>
                  </div>
                </div>
                <div class="level-right">
                  <div class="level-item">
                    <code class="is-size-7">{{ payload.payload_file }}</code>
                  </div>
                </div>
              </div>
            </div>
            <div v-show="payload.file_type" class="mt-1">
              <div class="level is-mobile">
                <div class="level-left">
                  <div class="level-item">
                    <span class="has-text-weight-bold">文件类型:</span>
                  </div>
                </div>
                <div class="level-right">
                  <div class="level-item">
                    <span class="tag is-small is-info">{{ payload.file_type }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal - 内联实现 -->
    <div class="modal" :class="{ 'is-active': showPayloadModal }">
      <div class="modal-background" @click="showPayloadModal = false"></div>
      <div class="modal-card wide">
        <header class="modal-card-head">
          <p class="modal-card-title">
            {{ isCreatingPayload ? '创建' : '编辑' }}载荷
          </p>
        </header>
        
        <section class="modal-card-body">
          <div class="content">
            <form @submit.prevent="handleSavePayload">
              <!-- Name Field -->
              <div class="field is-horizontal">
                <div class="field-label is-small">
                  <label class="label">名称</label>
                </div>
                <div class="field-body">
                  <div class="field">
                    <div class="control">
                      <input 
                        class="input is-small" 
                        v-model="formData.name"
                        placeholder="载荷名称"
                        required
                      />
                    </div>
                  </div>
                </div>
              </div>

              <!-- Description Field -->
              <div class="field is-horizontal">
                <div class="field-label is-small">
                  <label class="label">描述</label>
                </div>
                <div class="field-body">
                  <div class="field">
                    <div class="control">
                      <textarea 
                        class="textarea is-small" 
                        v-model="formData.description"
                        placeholder="载荷描述"
                        required
                      ></textarea>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Platforms Field -->
              <div class="field is-horizontal">
                <div class="field-label is-small">
                  <label class="label">平台</label>
                </div>
                <div class="field-body">
                  <div class="field">
                    <div class="control pl-3">
                      <div v-for="platform in allPlatforms" :key="platform">
                        <label class="checkbox mb-2">
                          <input 
                            type="checkbox" 
                            :value="platform"
                            v-model="formData.platforms"
                          />
                          <span>{{ getPlatformDisplayName(platform) }}</span>
                        </label>
                        <br />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Tactics Field -->
              <div class="field is-horizontal">
                <div class="field-label is-small">
                  <label class="label">战术</label>
                </div>
                <div class="field-body">
                  <div class="field">
                    <div class="control pl-3">
                      <div v-for="tactic in allTactics" :key="tactic">
                        <label class="checkbox mb-2">
                          <input 
                            type="checkbox" 
                            :value="tactic"
                            v-model="formData.tactics"
                          />
                          <span>{{ getTacticDisplayName(tactic) }}</span>
                        </label>
                        <br />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Threat Level Field -->
              <div class="field is-horizontal">
                <div class="field-label is-small">
                  <label class="label">威胁等级</label>
                </div>
                <div class="field-body">
                  <div class="field">
                    <div class="control">
                      <div class="select is-small">
                        <select v-model="formData.threat_level" required>
                          <option value="">选择威胁等级...</option>
                          <option v-for="level in allThreatLevels" :key="level" :value="level">
                            {{ getThreatLevelDisplayName(level) }}
                          </option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- File Type Field -->
              <div class="field is-horizontal">
                <div class="field-label is-small">
                  <label class="label">文件类型</label>
                </div>
                <div class="field-body">
                  <div class="field">
                    <div class="control">
                      <input 
                        class="input is-small" 
                        v-model="formData.file_type"
                        placeholder="exe, dll, ps1, sh等"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <!-- File Information Section -->
              <div v-show="!isCreatingPayload && formData.payload_file" class="field is-horizontal">
                <div class="field-label is-small">
                  <label class="label">文件信息</label>
                </div>
                <div class="field-body">
                  <div class="field">
                    <div class="box is-light">
                      <div class="content is-small">
                        <div class="level is-mobile">
                          <div class="level-left">
                            <div class="level-item">
                              <strong>文件位置:</strong>
                            </div>
                          </div>
                          <div class="level-right">
                            <div class="level-item">
                              <code>{{ formData.payload_file }}</code>
                            </div>
                          </div>
                        </div>
                        <div class="level is-mobile">
                          <div class="level-left">
                            <div class="level-item">
                              <strong>文件大小:</strong>
                            </div>
                          </div>
                          <div class="level-right">
                            <div class="level-item">
                              <span>{{ getFileSizeDisplay(formData.file_size) }}</span>
                            </div>
                          </div>
                        </div>
                        <div v-show="formData.md5" class="level is-mobile">
                          <div class="level-left">
                            <div class="level-item">
                              <strong>MD5值:</strong>
                            </div>
                          </div>
                          <div class="level-right">
                            <div class="level-item">
                              <code>{{ formData.md5 }}</code>
                            </div>
                          </div>
                        </div>
                        <div v-show="formData.file_type" class="level is-mobile">
                          <div class="level-left">
                            <div class="level-item">
                              <strong>文件类型:</strong>
                            </div>
                          </div>
                          <div class="level-right">
                            <div class="level-item">
                              <span class="tag is-info">{{ formData.file_type }}</span>
                            </div>
                          </div>
                        </div>
                        <div v-show="formData.cve_references && formData.cve_references.length > 0" class="level is-mobile">
                          <div class="level-left">
                            <div class="level-item">
                              <strong>CVE引用:</strong>
                            </div>
                          </div>
                          <div class="level-right">
                            <div class="level-item">
                              <div class="tags">
                                <span v-for="cve in formData.cve_references" :key="cve" class="tag is-small is-danger">
                                  {{ cve }}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                        <div v-show="formData.apt_groups && formData.apt_groups.length > 0" class="level is-mobile">
                          <div class="level-left">
                            <div class="level-item">
                              <strong>APT组织:</strong>
                            </div>
                          </div>
                          <div class="level-right">
                            <div class="level-item">
                              <div class="tags">
                                <span v-for="apt in formData.apt_groups" :key="apt" class="tag is-small is-warning">
                                  {{ apt }}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                        <div v-show="formData.tags && formData.tags.length > 0" class="level is-mobile">
                          <div class="level-left">
                            <div class="level-item">
                              <strong>标签:</strong>
                            </div>
                          </div>
                          <div class="level-right">
                            <div class="level-item">
                              <div class="tags">
                                <span v-for="tag in formData.tags" :key="tag" class="tag is-small is-light">
                                  {{ tag }}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </section>

        <footer class="modal-card-foot">
          <nav class="level">
            <div class="level-left">
              <div class="level-item">
                <button 
                  type="button"
                  class="button is-primary is-small" 
                  @click="handleDeletePayload"
                  v-show="!isCreatingPayload"
                >
                  <span class="icon">
                    <i class="fas fa-trash"></i>
                  </span>
                  <span>删除载荷</span>
                </button>
              </div>
            </div>
            <div class="level-right">
              <div class="level-item">
                <button type="button" class="button is-small" @click="showPayloadModal = false">
                  关闭
                </button>
              </div>
              <div class="level-item">
                <button type="button" class="button is-primary is-small" @click="handleSavePayload">
                  <span class="icon">
                    <i class="fas fa-save"></i>
                  </span>
                  <span>保存</span>
                </button>
              </div>
            </div>
          </nav>
        </footer>
      </div>
    </div>

    <!-- Import Modal - 内联实现 -->
    <div class="modal" :class="{ 'is-active': showImportModal }">
      <div class="modal-background" @click="showImportModal = false"></div>
      <div class="modal-card">
        <header class="modal-card-head">
          <p class="modal-card-title">导入载荷</p>
        </header>
        
        <section class="modal-card-body">
          <div class="file is-boxed">
            <label class="file-label">
              <input 
                class="file-input" 
                type="file" 
                @change="handleFileSelect"
                accept=".zip"
              />
              <span class="file-cta">
                <span class="file-icon">
                  <i class="fas fa-upload"></i>
                </span>
                <span class="file-label">选择ZIP文件...</span>
              </span>
            </label>
          </div>
          
          <p class="help mt-3">
            上传包含载荷YAML文件和载荷文件的ZIP文件。
          </p>
          
          <div v-if="selectedFile" class="notification is-info mt-3">
            <p><strong>已选择文件:</strong> {{ selectedFile.name }}</p>
            <p><strong>大小:</strong> {{ formatFileSize(selectedFile.size) }}</p>
          </div>
        </section>
        
        <footer class="modal-card-foot">
          <button 
            type="button"
            class="button is-small" 
            @click="showImportModal = false"
          >
            取消
          </button>
          <button 
            type="button"
            class="button is-primary is-small" 
            @click="handleImport"
            :disabled="!selectedFile"
          >
            导入
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

// Reactive data
const payloads = ref([])
const filteredPayloads = ref([])
const searchTerm = ref('')
const selectedPlatforms = reactive({})
const selectedTactic = ref('')
const selectedThreatLevel = ref('')
const isLoaded = ref(false)
const showPayloadModal = ref(false)
const showImportModal = ref(false)
const selectedPayload = ref(null)
const isCreatingPayload = ref(false)
const selectedFile = ref(null)

// Form data
const formData = reactive({
  payload_id: '',
  name: '',
  description: '',
  platforms: [],
  tactics: [],
  threat_level: '',
  file_type: '',
  md5: '',
  file_size: null,
  payload_file: '',
  cve_references: [],
  apt_groups: [],
  tags: []
})

// Filter options
const platforms = ref([])
const tactics = ref([])
const threatLevels = ref([])

// Constants
const allPlatforms = ['windows', 'linux', 'darwin']
const allTactics = [
  'discovery', 'execution', 'persistence', 'privilege-escalation',
  'defense-evasion', 'credential-access', 'collection',
  'command-and-control', 'exfiltration', 'impact', 'lateral-movement'
]
const allThreatLevels = ['Low', 'Medium', 'High', 'Critical']

// Methods
const initPage = async () => {
  try {
    console.log('Loading payloads...')
    const response = await fetch('/api/v2/payloads')
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    payloads.value = data
    console.log('Loaded payloads:', data)
    filterPayloads()
    isLoaded.value = true
  } catch (error) {
    console.error('Error loading payloads:', error)
    // 使用示例数据作为后备
    payloads.value = [
      {
        payload_id: '550e8400-e29b-41d4-a716-446655440001',
        name: 'Mimikatz',
        description: 'Credential dumping tool for Windows',
        platforms: ['windows'],
        tactics: ['credential-access'],
        threat_level: 'High',
        file_type: 'exe',
        md5: 'a1b2c3d4e5f6',
        file_size: 1024000,
        payload_file: 'plugins/stockpile/payloads/invoke-mimi.ps1.xored'
      },
      {
        payload_id: '550e8400-e29b-41d4-a716-446655440002',
        name: 'Basic Scanner',
        description: 'Network scanning tool for Linux',
        platforms: ['linux'],
        tactics: ['discovery'],
        threat_level: 'Medium',
        file_type: 'sh',
        md5: 'b2c3d4e5f6a1',
        file_size: 2048,
        payload_file: 'plugins/access/data/payloads/scanner.sh'
      },
      {
        payload_id: '550e8400-e29b-41d4-a716-446655440003',
        name: 'PowerShell Scanner',
        description: 'Advanced network scanner for Windows',
        platforms: ['windows'],
        tactics: ['discovery'],
        threat_level: 'Medium',
        file_type: 'ps1',
        md5: 'c3d4e5f6a1b2',
        file_size: 15360,
        payload_file: 'plugins/stockpile/payloads/basic_scanner.ps1'
      },
      {
        payload_id: '550e8400-e29b-41d4-a716-446655440004',
        name: 'macOS Bookmark',
        description: 'macOS bookmark manipulation tool',
        platforms: ['darwin'],
        tactics: ['persistence'],
        threat_level: 'Low',
        file_type: 'scpt',
        md5: 'd4e5f6a1b2c3',
        file_size: 1024,
        payload_file: 'plugins/stockpile/payloads/bookmark.scpt'
      }
    ]
    filterPayloads()
    isLoaded.value = true
  }
}

const getFilterOptions = () => {
  platforms.value = []
  tactics.value = []
  threatLevels.value = []

  payloads.value.forEach((payload) => {
    payload.platforms.forEach(platform => {
      if (!platforms.value.includes(platform)) {
        platforms.value.push(platform)
      }
    })
    payload.tactics.forEach(tactic => {
      if (!tactics.value.includes(tactic)) {
        tactics.value.push(tactic)
      }
    })
    if (!threatLevels.value.includes(payload.threat_level)) {
      threatLevels.value.push(payload.threat_level)
    }
  })

  platforms.value.sort()
  tactics.value.sort()
  threatLevels.value.sort()

  platforms.value.forEach((platform) => {
    if (selectedPlatforms[platform] === undefined) {
      selectedPlatforms[platform] = true
    }
  })
}

const filterPayloads = () => {
  filteredPayloads.value = payloads.value.filter((payload) => {
    const lcSearchTerm = searchTerm.value.toLowerCase()
    const matchesSearch = (
      payload.name.toLowerCase().includes(lcSearchTerm) ||
      payload.description.toLowerCase().includes(lcSearchTerm) ||
      payload.file_type.toLowerCase().includes(lcSearchTerm)
    )
    const matchesPlatform = Object.keys(selectedPlatforms).some(platform => 
      selectedPlatforms[platform] && payload.platforms.includes(platform)
    )
    const matchesTactic = (!selectedTactic.value || payload.tactics.includes(selectedTactic.value))
    const matchesThreatLevel = (!selectedThreatLevel.value || payload.threat_level === selectedThreatLevel.value)

    return matchesSearch && matchesPlatform && matchesTactic && matchesThreatLevel
  })
  getFilterOptions()
}

const clearFilters = () => {
  searchTerm.value = ''
  selectedTactic.value = ''
  selectedThreatLevel.value = ''
  platforms.value.forEach((platform) => selectedPlatforms[platform] = true)
  getFilterOptions()
  filterPayloads()
}

const getThreatLevelColor = (level) => {
  const colors = {
    'Low': 'is-info',
    'Medium': 'is-warning',
    'High': 'is-danger',
    'Critical': 'is-dark'
  }
  return colors[level] || 'is-light'
}

const getFileSizeDisplay = (size) => {
  if (!size) return '未知'
  
  let fileSize = size
  let units = ['B', 'KB', 'MB', 'GB']
  let unitIndex = 0
  
  while (fileSize >= 1024 && unitIndex < units.length - 1) {
    fileSize /= 1024
    unitIndex++
  }
  
  return `${fileSize.toFixed(1)} ${units[unitIndex]}`
}

const getPlatformDisplayName = (platform) => {
  const platformNames = {
    'windows': 'Windows',
    'linux': 'Linux',
    'darwin': 'macOS'
  }
  return platformNames[platform] || platform
}

const getTacticDisplayName = (tactic) => {
  const tacticNames = {
    'discovery': '发现',
    'execution': '执行',
    'persistence': '持久化',
    'privilege-escalation': '权限提升',
    'defense-evasion': '防御规避',
    'credential-access': '凭据访问',
    'collection': '数据收集',
    'command-and-control': '命令控制',
    'exfiltration': '数据渗出',
    'impact': '影响',
    'lateral-movement': '横向移动'
  }
  return tacticNames[tactic] || tactic
}

const getThreatLevelDisplayName = (level) => {
  const levelNames = {
    'Low': '低',
    'Medium': '中',
    'High': '高',
    'Critical': '严重'
  }
  return levelNames[level] || level
}

const selectPayload = (payload) => {
  isCreatingPayload.value = false
  selectedPayload.value = payload
  Object.assign(formData, payload)
  showPayloadModal.value = true
}

const createPayload = () => {
  console.log('Creating new payload...')
  isCreatingPayload.value = true
  selectedPayload.value = null
  Object.assign(formData, {
    payload_id: generateUUID(),
    name: '',
    description: '',
    platforms: [],
    tactics: [],
    threat_level: '',
    file_type: '',
    md5: '',
    file_size: null,
    payload_file: '',
    cve_references: [],
    apt_groups: [],
    tags: []
  })
  showPayloadModal.value = true
}

const handleSavePayload = async () => {
  try {
    console.log('Saving payload:', formData)
    
    if (isCreatingPayload.value) {
      // 创建新载荷
      const newPayload = { ...formData }
      payloads.value.push(newPayload)
      console.log('Created new payload:', newPayload)
    } else {
      // 更新现有载荷
      const index = payloads.value.findIndex(p => p.payload_id === formData.payload_id)
      if (index !== -1) {
        payloads.value[index] = { ...formData }
        console.log('Updated payload:', formData)
      }
    }
    
    filterPayloads()
    showPayloadModal.value = false
  } catch (error) {
    console.error('Error saving payload:', error)
  }
}

const handleDeletePayload = async () => {
  if (confirm('确定要删除这个载荷吗？')) {
    try {
      payloads.value = payloads.value.filter(p => p.payload_id !== formData.payload_id)
      filterPayloads()
      showPayloadModal.value = false
    } catch (error) {
      console.error('Error deleting payload:', error)
    }
  }
}

const handleFileSelect = (event) => {
  selectedFile.value = event.target.files[0]
}

const handleImport = async () => {
  try {
    console.log('Importing file:', selectedFile.value)
    // 这里可以添加实际的导入逻辑
    alert('导入功能将在此处实现')
    showImportModal.value = false
  } catch (error) {
    console.error('Error importing payloads:', error)
  }
}

const exportPayloads = () => {
  console.log('导出载荷...')
  alert('导出功能将在此处实现')
}

const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = Math.random() * 16 | 0
    const v = c == 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Lifecycle
onMounted(() => {
  console.log('PayloadManager component mounted')
  initPage()
})
</script>

<style scoped>
.payloads-container {
  padding: 1rem;
}

.header-section {
  margin-bottom: 1rem;
}

.filters {
  border-right: 1px solid rgb(97, 97, 97);
  padding-right: 1rem;
}

.payloads-grid {
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
}

.payload-card {
  position: relative;
  cursor: pointer;
  border: 1px solid transparent;
  background-color: #272727;
  width: 48%;
  margin-right: 1rem;
  margin-bottom: 0.5rem;
}

.payload-card:hover {
  border: 1px solid #474747;
}

.wide {
  width: 90%;
  max-width: 1200px;
}

.modal-card-body {
  overflow-x: hidden;
}

@media (max-width: 1200px) {
  .payload-card {
    width: 98%;
  }
}
</style>