<template>
  <div class="q-px-md">
    <div class="row items-start q-col-gutter-md q-mb-md">
      <div class="col">
        <div class="km-heading-7">Content Profiles</div>
        <div class="km-description text-secondary-text">Configure how different content types are processed and chunked</div>
      </div>
    </div>

    <q-separator class="q-my-md" />

    <div v-if="displayContentConfigs.length === 0" class="q-mt-md">
      <div class="text-center q-pa-lg">
        <q-icon name="folder_open" size="64px" color="grey-5" />
        <div class="km-heading-7 text-grey-7 q-mt-md">No content profiles added yet</div>
        <div class="km-description text-grey-6">Start by creating a new content profile</div>
        <div class="q-mt-md">
          <km-btn label="Create Profile" @click="openContentConfigDialog()" />
        </div>
      </div>
    </div>

    <div v-else class="q-mt-md">
      <kg-table-toolbar>
        <template #trailing>
          <km-btn flat icon="o_add_circle" label="New Profile" size="sm" :disable="saving" @click="openContentConfigDialog()" />
          <km-btn flat icon="refresh" label="Refresh" size="sm" :disable="saving" @click="emit('refresh')" />
        </template>
      </kg-table-toolbar>

      <q-table
        :rows="displayContentConfigs"
        :columns="contentConfigTableColumns"
        row-key="name"
        flat
        table-header-class="bg-primary-light"
        :loading="loadingContentConfigs || saving"
        :rows-per-page-options="[10]"
        @row-click="onCellClick"
      >
        <template #body-cell-order="slotProps">
          <q-td :props="slotProps" class="reorder-cell" @click.stop>
            <div class="reorder-buttons">
              <q-btn
                flat
                dense
                round
                size="sm"
                icon="expand_less"
                class="reorder-btn"
                :disable="!canMoveUp(slotProps.row)"
                @click.stop="moveUp(slotProps.row)"
              />
              <q-btn
                flat
                dense
                round
                size="sm"
                icon="expand_more"
                class="reorder-btn"
                :disable="!canMoveDown(slotProps.row)"
                @click.stop="moveDown(slotProps.row)"
              />
            </div>
          </q-td>
        </template>
        <template #body-cell-enabled="slotProps">
          <q-td :props="slotProps">
            <q-toggle
              :model-value="slotProps.row.enabled"
              dense
              :disable="saving || isProtectedProfile(slotProps.row)"
              @update:model-value="onToggleEnabled(slotProps.row, $event)"
            />
          </q-td>
        </template>
        <template #body-cell-menu="slotScope">
          <q-td :props="slotScope" class="sticky-col">
            <div v-if="!isProtectedProfile(slotScope.row)" class="flex items-center justify-end no-wrap">
              <q-btn dense flat color="dark" icon="more_vert" @click.stop>
                <q-menu anchor="bottom right" self="top right" auto-close>
                  <q-list dense>
                    <q-item clickable :disable="saving" @click="confirmDelete(slotScope.row)">
                      <q-item-section thumbnail>
                        <q-icon name="delete" color="negative" size="20px" class="q-ml-sm" />
                      </q-item-section>
                      <q-item-section>Delete</q-item-section>
                    </q-item>
                  </q-list>
                </q-menu>
              </q-btn>
            </div>
          </q-td>
        </template>
      </q-table>
    </div>

    <!-- Delete Content Profile Dialog -->
    <kg-confirm-dialog
      v-model="showDeleteDialog"
      title="Delete content configuration"
      icon="delete_outline"
      :description="`Are you sure you want to delete '${deletingProfile?.name}'?`"
      confirm-label="Delete"
      destructive
      @confirm="performDelete"
    />

    <!-- Content Config Dialog -->
    <ContentConfigDialog
      :config="editingContentConfig"
      :show-dialog="showContentConfigDialog"
      :sources="sources"
      :existing-configs="displayContentConfigs"
      @update:show-dialog="showContentConfigDialog = $event"
      @save="upsertContentConfig"
    />
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { QTableColumn } from 'quasar'
import { computed, ref, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useNotify } from '@/composables/useNotify'
import { KgConfirmDialog, KgTableToolbar } from '../common'
import { fetchKnowledgeGraphSources } from '../Sources/api'
import type { SourceRow } from '../Sources/models'
import type { KnowledgeGraphDetails } from '../types'
import ContentConfigDialog from './ContentConfigDialog.vue'
import {
  ContentConfigRow,
  chunkingStrategyOptions,
  getContentMatchingSentence,
  isProtectedContentProfile,
  isVirtualFallbackContentProfile,
} from './models'

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

const apiReady = computed(() => Boolean(appStore.config?.api?.aiBridge?.urlAdmin))

const saving = ref(false)
const contentConfigs = ref<any[]>([])
const virtualFallbackConfig = ref<ContentConfigRow | null>(null)
const loadingContentConfigs = ref(false)
const showContentConfigDialog = ref(false)
const editingContentConfig = ref<any>(null)
const sources = ref<SourceRow[]>([])

const originalContentConfigs = ref<any[]>([])

const cloneContentConfigs = (configs: any[]) => JSON.parse(JSON.stringify(configs || []))
const isProtectedProfile = (config?: any) => isProtectedContentProfile(config)
const getPersistedConfigIndex = (config?: ContentConfigRow | null) => contentConfigs.value.findIndex((item) => item.name === config?.name)
const displayContentConfigs = computed<ContentConfigRow[]>(() => [
  ...contentConfigs.value,
  ...(virtualFallbackConfig.value ? [virtualFallbackConfig.value] : []),
])

const contentConfigTableColumns: QTableColumn<ContentConfigRow>[] = [
  {
    name: 'order',
    label: '',
    field: 'name',
    align: 'center' as const,
    style: 'width: 72px; padding: 0 4px',
    headerStyle: 'width: 72px; padding: 0 4px',
    sortable: false,
  },
  {
    name: 'name',
    label: 'Name',
    field: 'name',
    align: 'left' as const,
  },
  {
    name: 'content_matching',
    label: 'Content Matching',
    field: (row) => getContentMatchingSentence(row, sources.value),
    align: 'left' as const,
    sortable: false,
    style: 'white-space: normal; min-width: 320px; max-width: 420px',
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
    label: 'Active',
    field: 'enabled',
    align: 'center' as const,
  },
  {
    name: 'menu',
    label: '',
    field: 'name',
    style: 'width: 80px',
    headerStyle: 'width: 80px',
  },
]

const initializeForm = () => {
  loadContentConfigs()
}

const fetchSources = async () => {
  try {
    const endpoint = appStore.config?.api?.aiBridge?.urlAdmin
    if (!endpoint) return
    sources.value = await fetchKnowledgeGraphSources({
      endpoint,
      graphId: props.graphId,
    })
  } catch (error) {

  }
}

const loadContentConfigs = async () => {
  loadingContentConfigs.value = true
  try {
    // Prefer configs already present in graphDetails if provided
    const fromGraph = props.graphDetails?.settings?.chunking?.content_settings
    if (Array.isArray(fromGraph)) {
      const clonedConfigs = cloneContentConfigs(fromGraph)
      const nextVirtualFallback = clonedConfigs.find((config) => isVirtualFallbackContentProfile(config))
      const persistedConfigs = clonedConfigs.filter((config) => !isVirtualFallbackContentProfile(config))

      virtualFallbackConfig.value = nextVirtualFallback ? cloneContentConfigs([nextVirtualFallback])[0] : null
      originalContentConfigs.value = cloneContentConfigs(persistedConfigs)
      contentConfigs.value = cloneContentConfigs(persistedConfigs)
      return
    }
    // Fallback: initialize empty list (new graphs are created with defaults)
    originalContentConfigs.value = []
    contentConfigs.value = []
    virtualFallbackConfig.value = null
  } catch (error) {

  } finally {
    loadingContentConfigs.value = false
  }
}

const showDeleteDialog = ref(false)
const deletingProfile = ref<ContentConfigRow | null>(null)

const confirmDelete = (row: ContentConfigRow) => {
  if (isProtectedProfile(row)) return
  deletingProfile.value = row
  showDeleteDialog.value = true
}

const performDelete = () => {
  if (deletingProfile.value) {
    if (isProtectedProfile(deletingProfile.value)) {
      deletingProfile.value = null
      showDeleteDialog.value = false
      return
    }
    onDeleteContentConfig(deletingProfile.value.name)
    deletingProfile.value = null
    showDeleteDialog.value = false
  }
}

const openContentConfigDialog = (config?: any) => {
  if (saving.value) return
  editingContentConfig.value = config || null
  showContentConfigDialog.value = true
}

const getResponseErrorMessage = async (response: Response, fallbackMessage: string) => {
  try {
    const errorData = await response.json()
    return errorData?.detail || errorData?.error || fallbackMessage
  } catch {
    return fallbackMessage
  }
}

const persistContentConfigs = async (nextConfigs: any[], errorMessage = 'Failed to save content profiles') => {
  const previousConfigs = cloneContentConfigs(contentConfigs.value)
  const previousOriginalConfigs = cloneContentConfigs(originalContentConfigs.value)
  const clonedNextConfigs = cloneContentConfigs(nextConfigs)

  contentConfigs.value = clonedNextConfigs
  saving.value = true

  try {
    const endpoint = appStore.config.api.aiBridge.urlAdmin
    const payload = {
      content_configs: clonedNextConfigs,
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
      const responseErrorMessage = await getResponseErrorMessage(res, errorMessage)
      contentConfigs.value = previousConfigs
      originalContentConfigs.value = previousOriginalConfigs
      notifyError(responseErrorMessage)
      return false
    }

    originalContentConfigs.value = cloneContentConfigs(clonedNextConfigs)
    emit('refresh')
    return true
  } catch (error) {

    contentConfigs.value = previousConfigs
    originalContentConfigs.value = previousOriginalConfigs
    notifyError(errorMessage)
    return false
  } finally {
    saving.value = false
  }
}

const canMoveUp = (config: ContentConfigRow) => {
  if (saving.value || isVirtualFallbackContentProfile(config)) return false
  return getPersistedConfigIndex(config) > 0
}

const canMoveDown = (config: ContentConfigRow) => {
  if (saving.value || isVirtualFallbackContentProfile(config)) return false
  const index = getPersistedConfigIndex(config)
  return index !== -1 && index < contentConfigs.value.length - 1
}

const moveUp = async (config: ContentConfigRow) => {
  const index = getPersistedConfigIndex(config)
  if (!canMoveUp(config)) return
  const items = cloneContentConfigs(contentConfigs.value)
  ;[items[index - 1], items[index]] = [items[index], items[index - 1]]
  await persistContentConfigs(items)
}

const moveDown = async (config: ContentConfigRow) => {
  const index = getPersistedConfigIndex(config)
  if (!canMoveDown(config)) return
  const items = cloneContentConfigs(contentConfigs.value)
  ;[items[index], items[index + 1]] = [items[index + 1], items[index]]
  await persistContentConfigs(items)
}

const onToggleEnabled = async (config: ContentConfigRow, enabled: boolean) => {
  if (saving.value) return
  if (isProtectedProfile(config)) return
  const index = getPersistedConfigIndex(config)
  const items = cloneContentConfigs(contentConfigs.value)
  if (!items[index]) return
  if (isProtectedProfile(items[index])) return
  items[index].enabled = enabled
  await persistContentConfigs(items)
}

const onDeleteContentConfig = async (configName: string) => {
  if (saving.value) return
  const items = cloneContentConfigs(contentConfigs.value)
  const idx = items.findIndex((c) => c.name === configName)
  if (idx !== -1) {
    if (isProtectedProfile(items[idx])) return
    items.splice(idx, 1)
    await persistContentConfigs(items)
  }
}

const upsertContentConfig = async (cfg: any) => {
  if (isVirtualFallbackContentProfile(cfg)) return
  const items = cloneContentConfigs(contentConfigs.value)
  const idx = items.findIndex((c) => c.name === cfg.name)
  if (idx !== -1) {
    items[idx] = cfg
  } else {
    items.unshift(cfg)
  }
  await persistContentConfigs(items)
}

const onCellClick = (_evt: any, row: any, col: any) => {
  if (saving.value) return
  if (col?.name === 'enabled') return
  openContentConfigDialog(row)
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

watch(
  apiReady,
  (ready) => {
    if (!ready) return
    fetchSources()
  },
  { immediate: true }
)
</script>

<style scoped>
:deep(.q-table thead th) {
  font-size: var(--km-body-sm-size, 14px);
  font-weight: 600;
}

:deep(.q-table tbody td) {
  height: 40px;
  padding: 2px 16px;
}

:deep(.sticky-col) {
  position: sticky;
  right: 0;
  z-index: 1;
  background: var(--q-white);
}

:deep(tr:hover .sticky-col) {
  background: var(--q-white);
}

:deep(thead th:last-child) {
  position: sticky;
  right: 0;
  z-index: 2;
  background: inherit;
}

.reorder-cell {
  cursor: default;
}

.reorder-buttons {
  display: inline-flex;
  flex-direction: row;
  align-items: center;
  gap: 2px;
}

.reorder-btn {
  opacity: 0.3;
  transition:
    opacity 0.15s ease,
    color 0.15s ease,
    background-color 0.15s ease;
  width: 28px;
  height: 28px;
}

:deep(tr:hover) .reorder-btn {
  opacity: 0.55;
}

.reorder-btn:hover:not([disabled]) {
  opacity: 1 !important;
  color: var(--q-primary) !important;
}

.reorder-btn[disabled] {
  opacity: 0.08 !important;
}
</style>
