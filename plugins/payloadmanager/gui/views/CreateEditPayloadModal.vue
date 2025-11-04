<template>
  <div class="modal" :class="{ 'is-active': show }">
    <div class="modal-background" @click="$emit('close')"></div>
    <div class="modal-card wide">
      <header class="modal-card-head">
        <p class="modal-card-title">
          {{ isCreating ? 'Create' : 'Edit' }} a Payload
        </p>
      </header>
      
      <section class="modal-card-body">
        <div class="content">
          <form @submit.prevent="handleSave">
            <!-- ID Field -->
            <div class="field is-horizontal">
              <div class="field-label is-small">
                <label class="label">ID</label>
              </div>
              <div class="field-body">
                <div class="field has-addons">
                  <div class="control is-expanded">
                    <input 
                      class="input is-small" 
                      v-model="formData.payload_id" 
                      disabled
                    />
                  </div>
                  <div class="control">
                    <button 
                      type="button"
                      class="button is-small" 
                      @click="formData.payload_id = generateUUID()"
                      title="Generate New ID"
                    >
                      <span class="icon is-small">
                        <i class="fas fa-sync"></i>
                      </span>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Name Field -->
            <div class="field is-horizontal">
              <div class="field-label is-small">
                <label class="label">Name</label>
              </div>
              <div class="field-body">
                <div class="field">
                  <div class="control">
                    <input 
                      class="input is-small" 
                      :class="{ 'is-danger': errors.name }"
                      v-model="formData.name"
                      required
                    />
                    <p v-show="errors.name" class="help is-danger">
                      This field is required.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Description Field -->
            <div class="field is-horizontal">
              <div class="field-label is-small">
                <label class="label">Description</label>
              </div>
              <div class="field-body">
                <div class="field">
                  <div class="control">
                    <textarea 
                      class="textarea is-small" 
                      :class="{ 'is-danger': errors.description }"
                      v-model="formData.description"
                      required
                    ></textarea>
                    <p v-show="errors.description" class="help is-danger">
                      This field is required.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Platforms Field -->
            <div class="field is-horizontal">
              <div class="field-label is-small">
                <label class="label">Platforms</label>
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
                        <span>{{ platform }}</span>
                      </label>
                      <br />
                    </div>
                    <p v-show="errors.platforms" class="help is-danger">
                      At least one platform is required.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Tactics Field -->
            <div class="field is-horizontal">
              <div class="field-label is-small">
                <label class="label">Tactics</label>
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
                        <span>{{ tactic }}</span>
                      </label>
                      <br />
                    </div>
                    <p v-show="errors.tactics" class="help is-danger">
                      At least one tactic is required.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Threat Level Field -->
            <div class="field is-horizontal">
              <div class="field-label is-small">
                <label class="label">Threat Level</label>
              </div>
              <div class="field-body">
                <div class="field">
                  <div class="control">
                    <div class="select is-small">
                      <select 
                        v-model="formData.threat_level"
                        :class="{ 'is-danger': errors.threat_level }"
                        required
                      >
                        <option value="">Select threat level...</option>
                        <option v-for="level in allThreatLevels" :key="level" :value="level">
                          {{ level }}
                        </option>
                      </select>
                    </div>
                    <p v-show="errors.threat_level" class="help is-danger">
                      This field is required.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- File Type Field -->
            <div class="field is-horizontal">
              <div class="field-label is-small">
                <label class="label">File Type</label>
              </div>
              <div class="field-body">
                <div class="field">
                  <div class="control">
                    <input 
                      class="input is-small" 
                      v-model="formData.file_type"
                      placeholder="exe, dll, ps1, etc."
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- File Upload Field -->
            <div class="field is-horizontal">
              <div class="field-label is-small">
                <label class="label">File Upload</label>
              </div>
              <div class="field-body">
                <div class="field">
                  <div class="file is-small">
                    <label class="file-label">
                      <input 
                        class="file-input" 
                        type="file" 
                        @change="handleFileUpload"
                        accept="*/*"
                      />
                      <span class="file-cta">
                        <span class="file-icon">
                          <i class="fas fa-upload"></i>
                        </span>
                        <span class="file-label">Choose file...</span>
                      </span>
                    </label>
                  </div>
                  <p v-show="uploadedFile" class="help is-success">
                    File uploaded: {{ uploadedFile.name }}
                  </p>
                </div>
              </div>
            </div>

            <!-- CVE References Field -->
            <div class="field is-horizontal">
              <div class="field-label is-small">
                <label class="label">CVE References</label>
              </div>
              <div class="field-body">
                <div class="field">
                  <div class="control">
                    <input 
                      class="input is-small" 
                      v-model="cveInput"
                      placeholder="CVE-2021-1234"
                      @keyup.enter="addCVE"
                    />
                    <p class="help">Press Enter to add CVE reference</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- CVE Tags -->
            <div class="field is-horizontal" v-show="formData.cve_references.length > 0">
              <div class="field-label is-small">
                <label class="label"></label>
              </div>
              <div class="field-body">
                <div class="field">
                  <div class="tags">
                    <span 
                      v-for="(cve, index) in formData.cve_references" 
                      :key="index"
                      class="tag is-link"
                    >
                      <span>{{ cve }}</span>
                      <button 
                        type="button"
                        class="delete is-small" 
                        @click="removeCVE(index)"
                      ></button>
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- APT Groups Field -->
            <div class="field is-horizontal">
              <div class="field-label is-small">
                <label class="label">APT Groups</label>
              </div>
              <div class="field-body">
                <div class="field">
                  <div class="control">
                    <input 
                      class="input is-small" 
                      v-model="aptInput"
                      placeholder="APT29"
                      @keyup.enter="addAPT"
                    />
                    <p class="help">Press Enter to add APT group</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- APT Tags -->
            <div class="field is-horizontal" v-show="formData.apt_groups.length > 0">
              <div class="field-label is-small">
                <label class="label"></label>
              </div>
              <div class="field-body">
                <div class="field">
                  <div class="tags">
                    <span 
                      v-for="(apt, index) in formData.apt_groups" 
                      :key="index"
                      class="tag is-warning"
                    >
                      <span>{{ apt }}</span>
                      <button 
                        type="button"
                        class="delete is-small" 
                        @click="removeAPT(index)"
                      ></button>
                    </span>
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
                @click="handleDelete"
                v-show="!isCreating"
              >
                <span class="icon">
                  <i class="fas fa-trash"></i>
                </span>
                <span>Delete Payload</span>
              </button>
            </div>
          </div>
          <div class="level-right">
            <div class="level-item">
              <button type="button" class="button is-small" @click="$emit('close')">
                Close
              </button>
            </div>
            <div class="level-item">
              <button type="button" class="button is-primary is-small" @click="handleSave">
                <span class="icon">
                  <i class="fas fa-save"></i>
                </span>
                <span>Save</span>
              </button>
            </div>
          </div>
        </nav>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'

const props = defineProps({
  show: Boolean,
  payload: Object,
  isCreating: Boolean
})

const emit = defineEmits(['close', 'save', 'delete'])

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

// Form inputs
const cveInput = ref('')
const aptInput = ref('')
const uploadedFile = ref(null)

// Validation errors
const errors = reactive({
  name: false,
  description: false,
  platforms: false,
  tactics: false,
  threat_level: false
})

// Constants
const allPlatforms = ['windows', 'linux', 'darwin']
const allTactics = [
  'discovery', 'execution', 'persistence', 'privilege-escalation',
  'defense-evasion', 'credential-access', 'collection',
  'command-and-control', 'exfiltration', 'impact', 'lateral-movement'
]
const allThreatLevels = ['Low', 'Medium', 'High', 'Critical']

// Watch for payload changes
watch(() => props.payload, (newPayload) => {
  if (newPayload) {
    Object.assign(formData, newPayload)
  }
}, { immediate: true })

// Methods
const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = Math.random() * 16 | 0
    const v = c == 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

const validateForm = () => {
  // Reset errors
  Object.keys(errors).forEach(key => errors[key] = false)
  
  let isValid = true
  
  if (!formData.name.trim()) {
    errors.name = true
    isValid = false
  }
  
  if (!formData.description.trim()) {
    errors.description = true
    isValid = false
  }
  
  if (formData.platforms.length === 0) {
    errors.platforms = true
    isValid = false
  }
  
  if (formData.tactics.length === 0) {
    errors.tactics = true
    isValid = false
  }
  
  if (!formData.threat_level) {
    errors.threat_level = true
    isValid = false
  }
  
  return isValid
}

const handleSave = () => {
  if (!validateForm()) {
    return
  }
  
  const payloadData = { ...formData }
  if (uploadedFile.value) {
    payloadData.file = uploadedFile.value
  }
  
  emit('save', payloadData)
}

const handleDelete = () => {
  if (confirm('Are you sure you want to delete this payload?')) {
    emit('delete', formData.payload_id)
  }
}

const handleFileUpload = (event) => {
  uploadedFile.value = event.target.files[0]
}

const addCVE = () => {
  if (cveInput.value.trim()) {
    formData.cve_references.push(cveInput.value.trim())
    cveInput.value = ''
  }
}

const removeCVE = (index) => {
  formData.cve_references.splice(index, 1)
}

const addAPT = () => {
  if (aptInput.value.trim()) {
    formData.apt_groups.push(aptInput.value.trim())
    aptInput.value = ''
  }
}

const removeAPT = (index) => {
  formData.apt_groups.splice(index, 1)
}
</script>

<style scoped>
.wide {
  width: 90%;
  max-width: 1200px;
}

.modal-card-body {
  overflow-x: hidden;
}
</style>
