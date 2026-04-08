<template>
  <div class="q-px-md">
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="km-heading-7">Graph Settings</div>
        <div class="km-description text-secondary-text">Configure the embedding model used for ingestion and graph building</div>
      </div>
      <div v-if="hasChanges" class="col-auto">
        <div class="row q-gutter-sm">
          <km-btn label="Cancel" flat color="grey-7" @click="resetForm" />
          <km-btn label="Save Changes" :loading="saving" :disable="!hasChanges" @click="saveSettings" />
        </div>
      </div>
    </div>

    <q-separator class="q-my-md" />

    <div class="q-mt-md">
      <q-form @submit="saveSettings">
        <km-section title="Indexing" sub-title="Select the embedding model used to create vector representations of content">
          <div class="column q-gap-16">
            <div class="col">
              <div class="row items-center q-gutter-xs q-mb-xs">
                <span class="km-input-label">Embedding model</span>
                <q-icon v-if="!embeddingModel" name="o_warning" color="red" size="xs" />
              </div>
              <kg-dropdown-field
                v-model="embeddingModel"
                :options="embeddingModelOptions"
                placeholder="Select embedding model"
                no-options-label="No embedding models available"
                option-value="system_name"
                option-label="display_name"
                :option-meta="formatVectorSize"
                :show-error="true"
                :clearable="true"
              />
            </div>
          </div>
        </km-section>

        <q-separator class="q-my-lg" />

        <km-section title="Logging" sub-title="Configure tracing detail level for sync operations">
          <div class="column q-gap-16">
            <div class="col">
              <div class="row items-center q-gutter-xs q-mb-xs">
                <span class="km-input-label">Tracing level</span>
              </div>
              <kg-dropdown-field
                v-model="tracingLevel"
                :options="tracingLevelOptions"
                placeholder="Select tracing level"
                option-value="value"
                option-label="label"
              />
              <div class="km-description text-secondary-text q-mt-xs">{{ tracingLevelDescription }}</div>
            </div>
          </div>
        </km-section>

        <q-separator class="q-my-lg" />
      </q-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { useQuasar } from 'quasar'
import { computed, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { KgDropdownField } from '../common'

interface Props {
  graphId: string
  graphDetails: Record<string, any>
}

const props = defineProps<Props>()
const emit = defineEmits<{
  refresh: []
}>()

const store = useStore()
const $q = useQuasar()

const embeddingModel = ref<string>('')
const tracingLevel = ref<string>('totals_only')
const saving = ref(false)

const tracingLevelOptions = [
  { value: 'off', label: 'Off' },
  { value: 'totals_only', label: 'Totals only' },
  { value: 'full', label: 'Full' },
]

const tracingLevelDescriptions: Record<string, string> = {
  off: 'No tracing at all — spans are completely skipped',
  totals_only: 'Individual step spans are not stored but contribute to cost and usage totals (default)',
  full: 'All individual step spans are stored for detailed inspection',
}

const tracingLevelDescription = computed(() => tracingLevelDescriptions[tracingLevel.value] ?? '')

const embeddingModelOptions = computed(() => {
  return (store.getters['chroma/model']?.items || []).filter((el: any) => el.type === 'embeddings')
})

const formatVectorSize = (opt: any): string | undefined => {
  const size = opt?.configs?.vector_size ?? 1536
  return size ? `${size} size vector` : undefined
}

const originalValues = ref<Record<string, any>>({})

const initializeForm = () => {
  embeddingModel.value = props.graphDetails.settings?.indexing?.embedding_model ?? ''
  tracingLevel.value = props.graphDetails.settings?.logging?.tracing_level ?? 'totals_only'

  originalValues.value = {
    embeddingModel: embeddingModel.value,
    tracingLevel: tracingLevel.value,
  }
}

const hasChanges = computed(() => {
  return (
    embeddingModel.value !== originalValues.value.embeddingModel ||
    tracingLevel.value !== originalValues.value.tracingLevel
  )
})

const resetForm = () => {
  initializeForm()
}

const saveSettings = async () => {
  saving.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin

    const currentSettings = props.graphDetails?.settings && typeof props.graphDetails.settings === 'object' ? props.graphDetails.settings : {}
    const currentIndexing = currentSettings?.indexing && typeof currentSettings.indexing === 'object' ? currentSettings.indexing : {}
    const currentLogging = currentSettings?.logging && typeof currentSettings.logging === 'object' ? currentSettings.logging : {}

    const payload = {
      settings: {
        ...currentSettings,
        indexing: { ...currentIndexing, embedding_model: embeddingModel.value || null },
        logging: { ...currentLogging, tracing_level: tracingLevel.value },
      },
    }
    const res = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}`,
      method: 'PATCH',
      credentials: 'include',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    })

    if (!res.ok) {
      $q.notify({ type: 'negative', message: 'Failed to save settings' })
      return
    }

    // Immediately clear local "unsaved" state; parent refresh will reconcile server values.
    originalValues.value = { embeddingModel: embeddingModel.value, tracingLevel: tracingLevel.value }
    emit('refresh')
  } catch (error) {
    console.error('Error saving settings:', error)
    $q.notify({
      type: 'negative',
      message: 'Error saving configuration',
    })
  } finally {
    saving.value = false
  }
}

watch(
  () => props.graphDetails,
  () => {
    if (props.graphDetails) {
      initializeForm()
    }
  },
  { immediate: true, deep: true }
)
</script>
