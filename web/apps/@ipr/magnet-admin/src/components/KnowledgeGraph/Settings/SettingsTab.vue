<template>
  <div class="px-md">
    <div class="cluster mb-md">
      <div class="flex-1">
        <div class="km-heading-7">{{ m.knowledgeGraph_graphSettings() }}</div>
        <div class="km-description text-secondary-text">{{ m.knowledgeGraph_graphSettingsDesc() }}</div>
      </div>
      <div v-if="hasChanges" class="flex-none">
        <div class="cluster" data-gap="sm">
          <km-btn :label="m.common_cancel()" flat tone="weak" @click="resetForm" />
          <km-btn :label="m.common_saveChanges()" :loading="saving" :disable="!hasChanges" @click="saveSettings" />
        </div>
      </div>
    </div>

    <km-separator class="my-md" />

    <div class="mt-md">
      <form class="km-form" @submit="saveSettings">
        <km-section :title="m.knowledgeGraph_indexingSection()" :sub-title="m.knowledgeGraph_indexingSectionDesc()">
          <div class="stack" data-gap="lg">
            <div class="flex-1">
              <div class="cluster mb-xs" data-gap="xs">
                <span class="km-input-label">{{ m.knowledgeGraph_embeddingModelLabel() }}</span>
                <km-glyph v-if="!embeddingModel" name="warning" tone="danger" size="xs" />
              </div>
              <kg-dropdown-field
                v-model="embeddingModel"
                :options="embeddingModelOptions"
                :placeholder="m.knowledgeGraph_selectEmbeddingModel()"
                :no-options-label="m.knowledgeGraph_noEmbeddingModels()"
                option-value="system_name"
                option-label="display_name"
                :option-meta="formatVectorSize"
                :show-error="true"
                :clearable="true"
              />
            </div>
          </div>
        </km-section>

        <km-separator class="my-lg" />
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { m } from '@/paraglide/messages'
import { computed, ref, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useNotify } from '@/composables/useNotify'
import { KgDropdownField } from '../common'
import type { KnowledgeGraphDetails } from '../types'
import { useEntityQueries } from '@/queries/entities'

interface Props {
  graphId: string
  graphDetails: KnowledgeGraphDetails
}

const props = defineProps<Props>()
const emit = defineEmits<{
  refresh: []
}>()

const appStore = useAppStore()
const { notifyError } = useNotify()

const queries = useEntityQueries()
const { data: modelListData } = queries.model.useList()

const embeddingModel = ref<string>('')
const saving = ref(false)

const embeddingModelOptions = computed(() => {
  return (modelListData.value?.items ?? []).filter((el: any) => el.type === 'embeddings')
})

const formatVectorSize = (opt: any): string | undefined => {
  const size = opt?.configs?.vector_size ?? 1536
  return size ? `${size} size vector` : undefined
}

const originalValues = ref<KnowledgeGraphDetails['settings']>({})

const initializeForm = () => {
  embeddingModel.value = props.graphDetails.settings?.indexing?.embedding_model ?? ''

  originalValues.value = {
    embeddingModel: embeddingModel.value,
  }
}

const hasChanges = computed(() => {
  return embeddingModel.value !== originalValues.value.embeddingModel
})

const resetForm = () => {
  initializeForm()
}

const saveSettings = async () => {
  saving.value = true
  try {
    const endpoint = appStore.config.api.aiBridge.urlAdmin

    const currentSettings = props.graphDetails?.settings && typeof props.graphDetails.settings === 'object' ? props.graphDetails.settings : {}
    const currentIndexing = currentSettings?.indexing && typeof currentSettings.indexing === 'object' ? currentSettings.indexing : {}

    const payload = {
      settings: {
        ...currentSettings,
        indexing: { ...currentIndexing, embedding_model: embeddingModel.value || null },
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
      notifyError(m.knowledgeGraph_failedToSaveSettings())
      return
    }

    // Immediately clear local "unsaved" state; parent refresh will reconcile server values.
    originalValues.value = { embeddingModel: embeddingModel.value }
    emit('refresh')
  } catch (error) {

    notifyError(m.knowledgeGraph_errorSavingConfiguration())
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
