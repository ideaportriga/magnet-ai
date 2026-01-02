<template>
  <div class="q-px-md">
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="km-heading-7">Content Profiles</div>
        <div class="km-description text-secondary-text">Configure how different content types are processed and chunked</div>
      </div>
      <div v-if="hasChanges" class="col-auto">
        <div class="row q-gutter-sm">
          <km-btn label="Cancel" flat color="grey-7" @click="resetForm" />
          <km-btn label="Save Changes" :loading="saving" :disable="!hasChanges" @click="saveSettings" />
        </div>
      </div>
    </div>

    <q-separator class="q-my-md" />

    <div v-if="contentConfigs.length === 0" class="q-mt-md">
      <div class="text-center q-pa-lg">
        <q-icon name="folder_open" size="64px" color="grey-5" />
        <div class="km-heading-7 text-grey-7 q-mt-md">No content profiles added yet</div>
        <div class="km-description text-grey-6">Start by creating a new content profile</div>
      </div>
    </div>

    <div v-else class="q-mt-md">
      <q-table
        :rows="contentConfigs"
        :columns="contentConfigTableColumns"
        row-key="name"
        flat
        table-header-class="bg-primary-light"
        :loading="loadingContentConfigs"
        :rows-per-page-options="[10]"
        @row-click="onCellClick"
      >
        <template #body-cell-enabled="slotProps">
          <q-td :props="slotProps">
            <q-toggle v-model="slotProps.row.enabled" dense />
          </q-td>
        </template>
      </q-table>
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

const saving = ref(false)
const contentConfigs = ref<any[]>([])
const loadingContentConfigs = ref(false)
const showContentConfigDialog = ref(false)
const editingContentConfig = ref<any>(null)

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
  return currentStr !== originalStr
})

const resetForm = () => {
  initializeForm()
}

const saveSettings = async () => {
  saving.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const payload = {
      content_configs: contentConfigs.value,
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
      $q.notify({ type: 'negative', message: 'Failed to save content profiles' })
      return
    }

    // Immediately clear local "unsaved" state; parent refresh will reconcile server values.
    originalContentConfigs.value = JSON.parse(JSON.stringify(contentConfigs.value))
    emit('refresh')
  } catch (error) {
    console.error('Error saving content profiles:', error)
    $q.notify({
      type: 'negative',
      message: 'Error saving content profiles',
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
  font-size: 0.8rem;
  font-weight: 600;
}
</style>
