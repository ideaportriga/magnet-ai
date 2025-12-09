<template>
  <div class="q-px-md">
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="km-heading-7">Graph Settings</div>
        <div class="km-description text-secondary-text">Configure content processing profiles and embedding model for ingestion and graph building</div>
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
        <km-section title="Content Profiles" sub-title="Configure how different content types are processed and chunked">
          <div class="column q-gap-16">
            <div class="col">
              <div class="row justify-start items-center q-mb-sm">
                <km-btn label="Create New Profile" size="sm" flat @click="openContentConfigDialog()" />
              </div>
              <q-table
                :rows="contentConfigs"
                :columns="contentConfigTableColumns"
                row-key="name"
                flat
                bordered
                hide-pagination
                table-header-class="bg-primary-light"
                :loading="loadingContentConfigs"
                @row-click="onCellClick"
              >
                <template #body-cell-enabled="slotProps">
                  <q-td :props="slotProps">
                    <q-toggle v-model="slotProps.row.enabled" dense />
                  </q-td>
                </template>
              </q-table>
            </div>
          </div>
        </km-section>

        <q-separator class="q-my-lg" />

        <km-section title="Indexing" sub-title="Select the embedding model used to create vector representations of content">
          <div class="column q-gap-16">
            <div class="col">
              <div class="row items-center q-gutter-xs q-mb-xs">
                <span class="km-input-label">Embedding model</span>
                <q-icon v-if="!embeddingModel" name="o_warning" color="red" size="xs" />
              </div>
              <StyledSelect
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
      </q-form>
    </div>

    <!-- Content Config Dialog -->
    <ContentConfigDialog
      :config="editingContentConfig"
      :show-dialog="showContentConfigDialog"
      @update:show-dialog="showContentConfigDialog = $event"
      @save="upsertContentConfig"
      @delete="onDeleteContentConfig"
    />
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { QTableColumn, useQuasar } from 'quasar'
import { computed, ref, watch } from 'vue'
import { useStore } from 'vuex'
import StyledSelect from '../StyledSelect.vue'
import ContentConfigDialog from './ContentConfigDialog.vue'
import { ContentConfigRow, chunkingStrategyOptions, readerOptions } from './models'

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
const saving = ref(false)
const contentConfigs = ref<any[]>([])
const loadingContentConfigs = ref(false)
const showContentConfigDialog = ref(false)
const editingContentConfig = ref<any>(null)

const embeddingModelOptions = computed(() => {
  return (store.getters['chroma/model']?.items || []).filter((el: any) => el.type === 'embeddings')
})

const formatVectorSize = (opt: any): string | undefined => {
  console.log(opt)
  const size = opt?.configs?.vector_size ?? 1536
  return size ? `${size} size vector` : undefined
}

const originalValues = ref<Record<string, any>>({})
const originalContentConfigs = ref<any[]>([])

const contentConfigTableColumns: QTableColumn<ContentConfigRow>[] = [
  {
    name: 'name',
    label: 'Name',
    field: 'name',
    align: 'left' as const,
  },
  {
    name: 'content_reader',
    label: 'Content Reader',
    field: (row) => row.reader?.name,
    format: (value) => readerOptions.find((o) => o.value === value)?.label || value || '-',
    align: 'left' as const,
  },
  {
    name: 'chunk_strategy',
    label: 'Chunk Strategy',
    field: (row) => row?.chunker?.strategy,
    format: (value) => chunkingStrategyOptions.find((o) => o.value === value)?.label || value || '-',
    align: 'left' as const,
  },
  {
    name: 'enabled',
    label: 'Enabled',
    field: 'enabled',
    align: 'center' as const,
  },
]

const initializeForm = () => {
  embeddingModel.value = props.graphDetails.settings?.indexing?.embedding_model ?? ''

  originalValues.value = {
    embeddingModel: embeddingModel.value,
  }

  loadContentConfigs()
}

const loadContentConfigs = async () => {
  loadingContentConfigs.value = true
  try {
    // Prefer configs already present in graphDetails if provided
    const fromGraph = props.graphDetails?.settings?.chunking?.content_settings
    if (Array.isArray(fromGraph)) {
      originalContentConfigs.value = JSON.parse(JSON.stringify(fromGraph))
      contentConfigs.value = JSON.parse(JSON.stringify(fromGraph))
      return
    }
    // Fallback: initialize empty list (new graphs are created with defaults)
    originalContentConfigs.value = []
    contentConfigs.value = []
  } catch (error) {
    console.error('Error loading content configs:', error)
  } finally {
    loadingContentConfigs.value = false
  }
}

const openContentConfigDialog = (config?: any) => {
  editingContentConfig.value = config || null
  showContentConfigDialog.value = true
}

const onDeleteContentConfig = (configName: string) => {
  const idx = contentConfigs.value.findIndex((c) => c.name === configName)
  if (idx !== -1) {
    contentConfigs.value.splice(idx, 1)
  }
}

const upsertContentConfig = (cfg: any) => {
  const idx = contentConfigs.value.findIndex((c) => c.name === cfg.name)
  if (idx !== -1) {
    contentConfigs.value[idx] = cfg
  } else {
    contentConfigs.value.push(cfg)
  }
}

const onCellClick = (_evt: any, row: any, col: any) => {
  if (col?.name === 'enabled') return
  openContentConfigDialog(row)
}

const hasChanges = computed(() => {
  const settingsChanged = embeddingModel.value !== originalValues.value.embeddingModel

  const normalize = (arr: any[]) =>
    (arr || [])
      .map((c) => ({
        ...c, // ensure deterministic order of splitters
        chunker: {
          ...c.chunker,
          options: {
            ...c.chunker?.options,
            splitters: Array.isArray(c.chunker?.options?.splitters) ? [...c.chunker.options.splitters] : [],
          },
        },
      }))
      .sort((a, b) => a.name.localeCompare(b.name))

  const currentStr = JSON.stringify(normalize(contentConfigs.value))
  const originalStr = JSON.stringify(normalize(originalContentConfigs.value))
  const contentChanged = currentStr !== originalStr

  return settingsChanged || contentChanged
})

const resetForm = () => {
  initializeForm()
}

const saveSettings = async () => {
  saving.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    // Single PATCH: include settings and content configurations
    const payload = {
      settings: {
        indexing: {
          embedding_model: embeddingModel.value || null,
        },
        chunking: {
          content_settings: contentConfigs.value,
        },
      },
    }
    const res = await fetchData({
      endpoint,
      service: `knowledge_graphs//${props.graphId}`,
      method: 'PATCH',
      credentials: 'include',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    })

    if (!res.ok) {
      $q.notify({ type: 'negative', message: 'Failed to save settings' })
      return
    }

    emit('refresh')
    initializeForm()
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

<style scoped>
:deep(.q-table__card .q-table thead tr, .q-table__card thead tr) {
  background-color: #f5f5f5;
}

:deep(.q-table__card .q-table thead th, .q-table__card thead th) {
  padding: 16px 12px;
  color: #1a1a1a;
  border-bottom: none;
  font-size: 0.8rem;
  font-weight: 600;
}
</style>
