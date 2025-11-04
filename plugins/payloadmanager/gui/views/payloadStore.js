import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const usePayloadStore = defineStore('payload', () => {
  // State
  const payloads = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const payloadCount = computed(() => payloads.value.length)
  
  const payloadsByPlatform = computed(() => {
    const grouped = {}
    payloads.value.forEach(payload => {
      payload.platforms.forEach(platform => {
        if (!grouped[platform]) {
          grouped[platform] = []
        }
        grouped[platform].push(payload)
      })
    })
    return grouped
  })

  const payloadsByTactic = computed(() => {
    const grouped = {}
    payloads.value.forEach(payload => {
      payload.tactics.forEach(tactic => {
        if (!grouped[tactic]) {
          grouped[tactic] = []
        }
        grouped[tactic].push(payload)
      })
    })
    return grouped
  })

  const payloadsByThreatLevel = computed(() => {
    const grouped = {}
    payloads.value.forEach(payload => {
      const level = payload.threat_level
      if (!grouped[level]) {
        grouped[level] = []
      }
      grouped[level].push(payload)
    })
    return grouped
  })

  // Actions
  const fetchPayloads = async () => {
    loading.value = true
    error.value = null
    
    try {
      const response = await fetch('/api/v2/payloads')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      payloads.value = data
    } catch (err) {
      error.value = err.message
      console.error('Error fetching payloads:', err)
    } finally {
      loading.value = false
    }
  }

  const fetchPayload = async (payloadId) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await fetch(`/api/v2/payloads/${payloadId}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      return data
    } catch (err) {
      error.value = err.message
      console.error('Error fetching payload:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const createPayload = async (payloadData) => {
    loading.value = true
    error.value = null
    
    try {
      const formData = new FormData()
      
      // Add file if present
      if (payloadData.file) {
        formData.append('file', payloadData.file)
      }
      
      // Add payload data
      const { file, ...data } = payloadData
      formData.append('data', JSON.stringify(data))
      
      const response = await fetch('/api/v2/payloads', {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const newPayload = await response.json()
      payloads.value.push(newPayload)
      return newPayload
    } catch (err) {
      error.value = err.message
      console.error('Error creating payload:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const updatePayload = async (payloadId, payloadData) => {
    loading.value = true
    error.value = null
    
    try {
      const formData = new FormData()
      
      // Add file if present
      if (payloadData.file) {
        formData.append('file', payloadData.file)
      }
      
      // Add payload data
      const { file, ...data } = payloadData
      formData.append('data', JSON.stringify(data))
      
      const response = await fetch(`/api/v2/payloads/${payloadId}`, {
        method: 'PATCH',
        body: formData
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const updatedPayload = await response.json()
      const index = payloads.value.findIndex(p => p.payload_id === payloadId)
      if (index !== -1) {
        payloads.value[index] = updatedPayload
      }
      return updatedPayload
    } catch (err) {
      error.value = err.message
      console.error('Error updating payload:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const deletePayload = async (payloadId) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await fetch(`/api/v2/payloads/${payloadId}`, {
        method: 'DELETE'
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      payloads.value = payloads.value.filter(p => p.payload_id !== payloadId)
    } catch (err) {
      error.value = err.message
      console.error('Error deleting payload:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const importPayloads = async (file) => {
    loading.value = true
    error.value = null
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch('/api/v2/payloads/import', {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      
      // Refresh payloads after import
      await fetchPayloads()
      
      return result
    } catch (err) {
      error.value = err.message
      console.error('Error importing payloads:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const exportPayloads = async (payloadIds = [], includeFiles = true) => {
    try {
      const params = new URLSearchParams()
      if (payloadIds.length > 0) {
        params.append('payload_ids', payloadIds.join(','))
      }
      params.append('include_files', includeFiles.toString())
      
      const response = await fetch(`/api/v2/payloads/export?${params}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'payloads_export.zip'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      error.value = err.message
      console.error('Error exporting payloads:', err)
      throw err
    }
  }

  const getFilterOptions = async () => {
    try {
      const response = await fetch('/api/v2/payloads/filters')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (err) {
      error.value = err.message
      console.error('Error fetching filter options:', err)
      throw err
    }
  }

  return {
    // State
    payloads,
    loading,
    error,
    
    // Getters
    payloadCount,
    payloadsByPlatform,
    payloadsByTactic,
    payloadsByThreatLevel,
    
    // Actions
    fetchPayloads,
    fetchPayload,
    createPayload,
    updatePayload,
    deletePayload,
    importPayloads,
    exportPayloads,
    getFilterOptions
  }
})
