<template>
  <div class="px-md">
    <div class="cluster mb-md" data-gap="md" data-align="start">
      <div class="flex-1">
        <div class="km-heading-7">{{ m.knowledgeGraph_contentProfiles() }}</div>
        <div class="km-description text-secondary-text">{{ m.knowledgeGraph_contentProfilesDescription() }}</div>
      </div>
    </div>

    <km-separator class="my-md" />

    <div v-if="displayContentConfigs.length === 0" class="mt-md">
      <div class="text-center p-lg">
        <km-glyph name="folder-open" size="64px" tone="muted" />
        <div class="km-heading-7 text-grey-7 mt-md">{{ m.knowledgeGraph_noContentProfilesYet() }}</div>
        <div class="km-description text-grey-6">{{ m.knowledgeGraph_startByCreatingProfile() }}</div>
        <div class="mt-md">
          <km-btn :label="m.knowledgeGraph_createProfile()" @click="openContentConfigDialog()" />
        </div>
      </div>
    </div>

    <div v-else class="mt-md">
      <kg-table-toolbar>
        <template #trailing>
          <km-btn flat icon="add-circle" :label="m.knowledgeGraph_newProfile()" size="sm" :disable="saving" @click="openContentConfigDialog()" />
          <km-btn flat icon="refresh" :label="m.common_refresh()" size="sm" :disable="saving" @click="emit('refresh')" />
        </template>
      </kg-table-toolbar>

      <!-- §E.2.2 — km-data-table with named cell slots.
           row-click opens the edit dialog; click-bubbling from toggle/menu
           is suppressed locally via @click.stop inside the cells. -->
      <km-data-table
        :table="table"
        row-key="name"
        :loading="loadingContentConfigs || saving"
        hide-pagination
        @row-click="onRowClick"
      >
        <template #cell-order="{ row }">
          <div class="reorder-buttons" @click.stop>
            <km-btn
              flat
              dense
              round
              size="sm"
              icon="chevron-up"
              class="reorder-btn"
              :disable="!canMoveUp(row)"
              @click.stop="moveUp(row)"
            />
            <km-btn
              flat
              dense
              round
              size="sm"
              icon="chevron-down"
              class="reorder-btn"
              :disable="!canMoveDown(row)"
              @click.stop="moveDown(row)"
            />
          </div>
        </template>

        <template #cell-content_matching="{ row }">
          <span class="content-matching-cell">{{ contentMatchingLabel(row) }}</span>
        </template>

        <template #cell-chunk_strategy="{ row }">
          {{ chunkStrategyLabel(row) }}
        </template>

        <template #cell-enabled="{ row }">
          <km-toggle
            :model-value="row.enabled"
            dense
            :disable="saving || isProtectedProfile(row)"
            @update:model-value="onToggleEnabled(row, $event)"
            @click.stop
          />
        </template>

        <template #cell-menu="{ row }">
          <div v-if="!isProtectedProfile(row)" class="flex items-center justify-end no-wrap">
            <ds-dropdown-menu-root>
              <ds-dropdown-menu-trigger as-child>
                <km-btn dense flat tone="neutral" icon="more-vertical" @click.stop />
              </ds-dropdown-menu-trigger>
              <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
                <ds-dropdown-menu-item variant="destructive" :disabled="saving" @select="confirmDelete(row)">
                  <km-glyph name="delete" size="18px" /><span>{{ m.common_delete() }}</span>
                </ds-dropdown-menu-item>
              </ds-dropdown-menu-content>
            </ds-dropdown-menu-root>
          </div>
        </template>
      </km-data-table>
    </div>

    <!-- Delete Content Profile Dialog -->
    <kg-confirm-dialog
      v-model="showDeleteDialog"
      :title="m.knowledgeGraph_deleteContentConfig()"
      icon="delete"
      :description="m.knowledgeGraph_deleteContentConfigConfirm({ name: deletingProfile?.name ?? '' })"
      :confirm-label="m.common_delete()"
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
import { m } from '@/paraglide/messages'
import type { ColumnDef } from '@tanstack/vue-table'
import { computed, ref, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useNotify } from '@/composables/useNotify'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
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

// §E.2.2 — TanStack columns. order/menu/enabled have custom cell slots above;
// content_matching and chunk_strategy are rendered via helper functions.
const contentConfigTableColumns: ColumnDef<ContentConfigRow, unknown>[] = [
  {
    id: 'order',
    header: '',
    enableSorting: false,
    meta: { align: 'center', width: '72px' },
  },
  {
    id: 'name',
    accessorKey: 'name',
    header: m.common_name(),
    enableSorting: true,
    meta: { align: 'left' },
  },
  {
    id: 'content_matching',
    header: m.knowledgeGraph_contentMatching(),
    enableSorting: false,
    meta: { align: 'left', width: '360px' },
  },
  {
    id: 'chunk_strategy',
    accessorFn: (row: ContentConfigRow) => row?.chunker?.strategy,
    header: m.knowledgeGraph_chunkStrategy(),
    enableSorting: true,
    meta: { align: 'left' },
  },
  {
    id: 'enabled',
    accessorKey: 'enabled',
    header: m.common_active(),
    enableSorting: false,
    meta: { align: 'center', width: '80px' },
  },
  {
    id: 'menu',
    header: '',
    enableSorting: false,
    meta: { align: 'right', width: '80px' },
  },
]

const { table } = useLocalDataTable<ContentConfigRow>(displayContentConfigs, contentConfigTableColumns, {
  defaultPageSize: 100,
})

function contentMatchingLabel(row: ContentConfigRow): string {
  return getContentMatchingSentence(row, sources.value) || ''
}

function chunkStrategyLabel(row: ContentConfigRow): string {
  const strategy = row?.chunker?.strategy
  if (!strategy) return '-'
  return chunkingStrategyOptions.find((o) => o.value === strategy)?.label || String(strategy)
}

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

// §E.2.2 — km-data-table emits a single-arg `row-click(row)`. Cells that
// should NOT trigger the dialog (toggle, menu, reorder) stop propagation
// locally via @click.stop inside their templates.
const onRowClick = (row: ContentConfigRow) => {
  if (saving.value) return
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
:deep(.sticky-col) {
  position: sticky;
  inset-inline-end: 0;
  z-index: 1;
  background: var(--ds-color-white);
}

:deep(tr:hover .sticky-col) {
  background: var(--ds-color-white);
}

:deep(thead th:last-child) {
  position: sticky;
  inset-inline-end: 0;
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
  inline-size: 28px;
  block-size: 28px;
}

:deep(tr:hover) .reorder-btn {
  opacity: 0.55;
}

.reorder-btn:hover:not([disabled]) {
  opacity: 1 !important;
  color: var(--ds-color-primary) !important;
}

.reorder-btn[disabled] {
  opacity: 0.08 !important;
}
</style>
