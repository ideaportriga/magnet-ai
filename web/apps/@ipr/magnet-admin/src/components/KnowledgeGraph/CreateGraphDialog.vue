<template>
  <km-popup-confirm
    :visible="showDialog"
    title="Create Knowledge Graph"
    confirm-button-label="Create"
    cancel-button-label="Cancel"
    :loading="loading"
    :disable-confirm="!graphName"
    @confirm="createGraph"
    @cancel="$emit('cancel')"
  >
    <div class="km-field text-secondary-text q-pb-xs q-pl-8 q-mb-md">
      Graph Name
      <km-input v-model="graphName" height="36px" placeholder="Enter graph name" border-radius="8px" @keyup.enter="createGraph" />
      <div class="km-description text-secondary-text q-py-8">A unique name for your knowledge graph</div>
    </div>

    <div class="km-field text-secondary-text q-pb-xs q-pl-8">
      Description (Optional)
      <q-input v-model="description" outlined dense type="textarea" placeholder="Describe the purpose of this knowledge graph" rows="3" />
      <div class="km-description text-secondary-text q-py-8">Brief description of what documents this graph will contain</div>
    </div>

    <div v-if="error" class="q-mt-md text-negative">{{ error }}</div>
  </km-popup-confirm>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { ref } from 'vue'
import { useStore } from 'vuex'

defineProps<{
  showDialog: boolean
}>()

const emit = defineEmits<{
  cancel: []
  created: [result: any]
}>()

const store = useStore()
const graphName = ref('')
const description = ref('')
const loading = ref(false)
const error = ref('')

const createGraph = async () => {
  if (!graphName.value.trim()) {
    error.value = 'Graph name is required'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const params = new URLSearchParams()
    params.set('name', graphName.value.trim())
    if (description.value.trim()) {
      params.set('description', description.value.trim())
    }

    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/`,
      method: 'POST',
      credentials: 'include',
      body: JSON.stringify({
        name: graphName.value.trim(),
        description: description.value.trim(),
      }),
    })

    if (response.ok) {
      const result = await response.json()
      console.log('Graph created:', result)
      emit('created', result)
    } else {
      const errorData = await response.json()
      error.value = errorData.detail || errorData.error || 'Failed to create graph'
    }
  } catch (err) {
    console.error('Create graph error:', err)
    error.value = 'Failed to create graph. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>
