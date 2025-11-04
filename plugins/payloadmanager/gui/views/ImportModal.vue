<template>
  <div class="modal" :class="{ 'is-active': show }">
    <div class="modal-background" @click="$emit('close')"></div>
    <div class="modal-card">
      <header class="modal-card-head">
        <p class="modal-card-title">Import Payloads</p>
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
              <span class="file-label">Choose ZIP file...</span>
            </span>
          </label>
        </div>
        
        <p class="help mt-3">
          Upload a ZIP file containing payload YAML files and payload files.
        </p>
        
        <div v-if="selectedFile" class="notification is-info mt-3">
          <p><strong>Selected file:</strong> {{ selectedFile.name }}</p>
          <p><strong>Size:</strong> {{ formatFileSize(selectedFile.size) }}</p>
        </div>
        
        <div v-if="importing" class="notification is-warning mt-3">
          <p>Importing payloads, please wait...</p>
        </div>
      </section>
      
      <footer class="modal-card-foot">
        <button 
          type="button"
          class="button is-small" 
          @click="$emit('close')"
          :disabled="importing"
        >
          Cancel
        </button>
        <button 
          type="button"
          class="button is-primary is-small" 
          @click="handleImport"
          :disabled="!selectedFile || importing"
        >
          <span v-show="!importing">Import</span>
          <span v-show="importing">Importing...</span>
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  show: Boolean
})

const emit = defineEmits(['close', 'import'])

const selectedFile = ref(null)
const importing = ref(false)

const handleFileSelect = (event) => {
  selectedFile.value = event.target.files[0]
}

const handleImport = async () => {
  if (!selectedFile.value) return
  
  importing.value = true
  
  try {
    await emit('import', selectedFile.value)
    // Reset form
    selectedFile.value = null
    importing.value = false
  } catch (error) {
    console.error('Import error:', error)
    importing.value = false
  }
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>
