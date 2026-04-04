<template>
  <km-popup-confirm
    :visible="showDialog"
    :title="m.knowledgeGraph_createKnowledgeGraph()"
    :confirm-button-label="m.knowledgeGraph_createGraph()"
    :cancel-button-label="m.common_cancel()"
    :loading="loading"
    :disable-confirm="!graphName"
    @confirm="createGraph"
    @cancel="$emit('cancel')"
  >
    <div class="km-field text-secondary-text q-pb-xs q-pl-8 q-mb-md">
      {{ m.knowledgeGraph_graphNameLabel() }}
      <km-input v-model="graphName" height="36px" :placeholder="m.knowledgeGraph_graphNamePlaceholder()" border-radius="8px" @keyup.enter="createGraph" />
      <div class="km-description text-secondary-text q-py-8">{{ m.knowledgeGraph_graphNameHint() }}</div>
    </div>

    <div class="km-field text-secondary-text q-pb-xs q-pl-8">
      {{ m.knowledgeGraph_descriptionOptional() }}
      <q-input v-model="description" outlined dense type="textarea" :placeholder="m.knowledgeGraph_graphDescPlaceholder()" rows="3" />
      <div class="km-description text-secondary-text q-py-8">{{ m.knowledgeGraph_graphDescHint() }}</div>
    </div>

    <div v-if="error" class="q-mt-md text-negative">{{ error }}</div>
  </km-popup-confirm>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { m } from '@/paraglide/messages'
import { ref } from 'vue'
import { useAppStore } from '@/stores/appStore'

defineProps<{
  showDialog: boolean
}>()

const emit = defineEmits<{
  cancel: []
  created: [result: any]
}>()

const appStore = useAppStore()
const graphName = ref('')
const description = ref('')
const loading = ref(false)
const error = ref('')

const createGraph = async () => {
  if (!graphName.value.trim()) {
    error.value = m.knowledgeGraph_graphNameRequired()
    return
  }

  loading.value = true
  error.value = ''

  try {
    const endpoint = appStore.config.api.aiBridge.urlAdmin
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

      emit('created', result)
    } else {
      const errorData = await response.json()
      error.value = errorData.detail || errorData.error || m.knowledgeGraph_failedToCreate()
    }
  } catch (err) {

    error.value = m.knowledgeGraph_failedToCreateRetry()
  } finally {
    loading.value = false
  }
}
</script>
