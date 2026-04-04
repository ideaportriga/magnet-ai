<template>
  <div class="q-px-md">
    <div class="row items-start q-col-gutter-md q-mb-md">
      <div class="col">
        <div class="km-heading-7">{{ m.knowledgeGraph_entityExtraction() }}</div>
        <div class="km-description text-secondary-text">
          {{ m.knowledgeGraph_entityExtractionDescription() }}
        </div>
      </div>
    </div>

    <q-separator class="q-my-md" />

    <div v-if="entities.length === 0" class="q-mt-md">
      <div class="text-center q-pa-lg">
        <q-icon name="o_category" size="64px" color="grey-5" />
        <div class="km-heading-7 text-grey-7 q-mt-md">{{ m.knowledgeGraph_noEntitiesYet() }}</div>
        <div class="km-description text-grey-6">{{ m.knowledgeGraph_createFirstEntityHint() }}</div>
        <q-btn no-caps unelevated color="primary" :label="m.knowledgeGraph_createFirstEntity()" class="q-mt-lg" :disable="saving" @click="openCreateDialog" />
      </div>
    </div>

    <div v-else>
      <kg-table-toolbar>
        <template #leading>
          <km-btn
            v-if="isExtractionActive || extractionStarting"
            :label="m.common_cancel()"
            size="sm"
            flat
            color="negative"
            :disable="cancelling || extractionStarting"
            @click="showCancelConfirmDialog = true"
          />
          <km-btn v-else :label="m.knowledgeGraph_runExtraction()" size="sm" :disable="!canRunExtraction || saving" @click="showRunConfirmDialog = true">
            <q-tooltip v-if="!canRunExtraction && !saving">{{ m.knowledgeGraph_configurePromptFirst() }}</q-tooltip>
          </km-btn>
        </template>

        <template #status>
          <!-- Progress area when running/starting -->
          <template v-if="isExtractionActive || extractionStarting">
            <q-linear-progress
              :value="progressFraction"
              :indeterminate="!hasProgress"
              color="primary"
              track-color="grey-3"
              rounded
              size="8px"
              style="width: 160px"
            />
            <span v-if="hasProgress" class="text-caption text-grey-7">{{ progressPercentText }}</span>
            <span class="text-caption text-grey-6">
              {{ extractionStatus.status === 'cancelling' ? m.knowledgeGraph_extractionCancelling() : m.knowledgeGraph_extractionRunning() }}
            </span>
          </template>

          <!-- Terminal status: completed / cancelled / error -->
          <span v-else-if="extractionStatus.status !== 'idle'" class="text-caption text-grey-7">
            {{ extractionStatusMessage }}
          </span>
        </template>

        <template #trailing>
          <km-btn flat icon="o_add_circle" :label="m.knowledgeGraph_newEntity()" size="sm" :disable="saving" @click="openCreateDialog" />
          <km-btn flat icon="settings" :label="m.common_settings()" size="sm" :disable="saving" @click="showExtractionDialog = true" />
          <km-btn flat icon="refresh" :label="m.common_refresh()" size="sm" :disable="saving" @click="emit('refresh')" />
        </template>
      </kg-table-toolbar>

      <q-table
        v-model:pagination="pagination"
        flat
        table-header-class="bg-primary-light"
        :rows="entities"
        :columns="columns"
        row-key="id"
        :loading="saving"
        :rows-per-page-options="[10]"
        :row-class="(row: EntityDefinition) => (row.enabled === false ? 'entity-row--disabled' : '')"
        @row-click="onRowClick"
      >
        <template #body-cell-name="slotScope">
          <q-td :props="slotScope">
            <div class="entity-name-cell">
              <span class="entity-name-text">{{ slotScope.row.name }}</span>
            </div>
          </q-td>
        </template>

        <template #body-cell-columns_count="slotScope">
          <q-td :props="slotScope">
            {{ slotScope.row.columns.length }}
          </q-td>
        </template>

        <template #body-cell-enabled="slotScope">
          <q-td :props="slotScope">
            <q-toggle
              :model-value="slotScope.row.enabled"
              dense
              :disable="saving"
              @update:model-value="toggleEntityEnabled(slotScope.row, $event)"
              @click.stop
            />
          </q-td>
        </template>

        <template #body-cell-menu="slotScope">
          <q-td :props="slotScope" class="text-right">
            <q-btn dense flat color="dark" icon="more_vert" :disable="saving" @click.stop>
              <q-menu class="entity-row-menu" anchor="bottom right" self="top right" auto-close>
                <q-list dense>
                  <q-item v-ripple="false" clickable :disable="saving" @click="editEntity(slotScope.row)">
                    <q-item-section thumbnail>
                      <q-icon name="edit" color="primary" size="20px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>{{ m.common_edit() }}</q-item-section>
                  </q-item>
                  <q-separator />
                  <q-item v-ripple="false" clickable :disable="saving" @click="confirmDelete(slotScope.row)">
                    <q-item-section thumbnail>
                      <q-icon name="delete" color="negative" size="20px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>{{ m.common_delete() }}</q-item-section>
                  </q-item>
                </q-list>
              </q-menu>
            </q-btn>
          </q-td>
        </template>
      </q-table>
    </div>

    <entity-dialog
      v-model="dialogOpen"
      :entity="selectedEntity"
      :existing-entity-names="existingEntityNames"
      :loading="saving"
      @cancel="onDialogCancel"
      @save="onDialogSave"
    />

    <entity-extraction-settings-dialog
      :show-dialog="showExtractionDialog"
      :settings="extractionSettings"
      :prompt-template-options="promptTemplateOptions"
      :loading-prompt-templates="loadingPromptTemplates"
      @update:show-dialog="showExtractionDialog = $event"
      @cancel="showExtractionDialog = false"
      @save="onExtractionSettingsSave"
    />

    <kg-confirm-dialog
      v-model="showDeleteDialog"
      :title="m.knowledgeGraph_deleteEntityTitle()"
      icon="delete_outline"
      :description="m.knowledgeGraph_deleteEntityConfirm({ name: selectedEntity?.name ?? '' })"
      :confirm-label="m.common_delete()"
      destructive
      :loading="saving"
      @confirm="performDelete"
    >
      <template #warning>
        {{ m.knowledgeGraph_deleteEntityWarning() }}
      </template>
    </kg-confirm-dialog>

    <kg-confirm-dialog
      v-model="showRunConfirmDialog"
      :title="m.knowledgeGraph_runExtractionTitle()"
      icon="o_play_arrow"
      icon-variant="info"
      :description="m.knowledgeGraph_runExtractionConfirm()"
      :confirm-label="m.knowledgeGraph_runExtraction()"
      @confirm="onConfirmRunExtraction"
    >
      <template #warning>{{ m.knowledgeGraph_runExtractionWarning() }}</template>
    </kg-confirm-dialog>

    <kg-confirm-dialog
      v-model="showCancelConfirmDialog"
      :title="m.knowledgeGraph_cancelExtractionTitle()"
      icon="o_cancel"
      icon-variant="warning"
      warning-variant="warning"
      :description="m.knowledgeGraph_cancelExtractionConfirm()"
      :confirm-label="m.knowledgeGraph_cancelExtraction()"
      destructive
      :loading="cancelling"
      @confirm="onConfirmCancelExtraction"
    >
      <template #warning>{{ m.knowledgeGraph_cancelExtractionWarning() }}</template>
    </kg-confirm-dialog>
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { m } from '@/paraglide/messages'
import type { QTableColumn } from 'quasar'
import { computed, ref, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useNotify } from '@/composables/useNotify'
import { KgConfirmDialog, KgTableToolbar } from '../common'
import type { KnowledgeGraphDetails } from '../types'
import EntityDialog from './EntityDialog.vue'
import EntityExtractionSettingsDialog from './EntityExtractionSettingsDialog.vue'
import {
  cloneEntityDefinitions,
  cloneEntityExtractionRunSettings,
  createDefaultEntityExtractionRunSettings,
  getEntityExtractionSettingsFromSettings,
  getExtractionStatusFromGraphDetails,
  withEntityDefinitions,
  withEntityExtractionRunSettings,
  type EntityDefinition,
  type EntityExtractionRunSettings,
  type EntityExtractionStatusInfo,
} from './models'

const props = defineProps<{
  graphId: string
  graphDetails: KnowledgeGraphDetails
}>()

const emit = defineEmits<{
  refresh: []
}>()

const appStore = useAppStore()
const { notifySuccess, notifyError, notifyWarning } = useNotify()

const entities = ref<EntityDefinition[]>([])
const extractionSettings = ref<EntityExtractionRunSettings>(createDefaultEntityExtractionRunSettings())
const selectedEntity = ref<EntityDefinition | null>(null)
const dialogOpen = ref(false)
const showDeleteDialog = ref(false)
const showExtractionDialog = ref(false)
const pagination = ref({ rowsPerPage: 10, page: 1 })
const saving = ref(false)
const loadingPromptTemplates = ref(false)
const promptTemplateOptions = ref<any[]>([])
const baseSettings = ref<KnowledgeGraphDetails['settings']>({})

const columns: QTableColumn<EntityDefinition>[] = [
  {
    name: 'name',
    label: m.knowledgeGraph_entityLabel(),
    field: 'name',
    align: 'left',
    sortable: true,
  },
  {
    name: 'description',
    label: m.common_description(),
    field: 'description',
    align: 'left',
    sortable: false,
    style: 'max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis',
  },
  {
    name: 'columns_count',
    label: m.knowledgeGraph_columns(),
    field: (row) => row.columns.length,
    align: 'left',
    sortable: true,
  },
  {
    name: 'identifier',
    label: m.knowledgeGraph_identifier(),
    field: (row) => row.columns.find((column) => column.is_identifier)?.name || '',
    align: 'left',
    sortable: false,
  },
  {
    name: 'enabled',
    label: m.common_active(),
    field: 'enabled',
    align: 'center',
  },
  {
    name: 'menu',
    label: '',
    field: 'id',
  },
]

const canRunExtraction = computed(() => {
  return !!String(extractionSettings.value.prompt_template_system_name || '').trim() && entities.value.length > 0 && !loadingPromptTemplates.value
})

const extractionStatus = computed<EntityExtractionStatusInfo>(() => {
  return getExtractionStatusFromGraphDetails(props.graphDetails)
})

const isExtractionActive = computed(() => {
  return extractionStatus.value.status === 'running' || extractionStatus.value.status === 'cancelling'
})

const hasProgress = computed(() => {
  const p = extractionStatus.value.progress
  return !!p && p.total > 0
})

const progressFraction = computed(() => {
  const p = extractionStatus.value.progress
  if (!p || p.total <= 0) return 0
  return Math.min(p.processed / p.total, 1)
})

const progressPercentText = computed(() => {
  return `${Math.round(progressFraction.value * 100)}%`
})

const extractionStatusMessage = computed(() => {
  const info = extractionStatus.value
  if (info.status === 'completed') {
    const ts = info.completed_at ? formatTimestamp(info.completed_at) : ''
    return ts ? `Completed ${ts}` : 'Completed'
  }
  if (info.status === 'cancelled') {
    const ts = info.completed_at ? formatTimestamp(info.completed_at) : ''
    return ts ? `Cancelled ${ts}` : 'Cancelled'
  }
  if (info.status === 'error') {
    const ts = info.completed_at ? formatTimestamp(info.completed_at) : ''
    return ts ? `Failed ${ts}` : 'Failed'
  }
  return ''
})

function formatTimestamp(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleString()
  } catch {
    return ''
  }
}

const existingEntityNames = computed(() => {
  const editingEntityId = selectedEntity.value?.id
  return entities.value.filter((entity) => entity.id !== editingEntityId).map((entity) => entity.name)
})

function cloneSettings(settings?: Record<string, any>) {
  try {
    return JSON.parse(JSON.stringify(settings || {})) as Record<string, any>
  } catch {
    return { ...(settings || {}) }
  }
}

function initializeFromSettings() {
  baseSettings.value = cloneSettings(props.graphDetails?.settings)
  const normalizedSettings = getEntityExtractionSettingsFromSettings(baseSettings.value)
  entities.value = cloneEntityDefinitions(normalizedSettings.entity_definitions)
  extractionSettings.value = cloneEntityExtractionRunSettings(normalizedSettings.extraction)
}

async function loadPromptTemplates() {
  loadingPromptTemplates.value = true
  try {
    const endpoint = appStore.config?.api?.aiBridge?.urlAdmin
    if (!endpoint) {
      promptTemplateOptions.value = []
      return
    }

    const response = await fetchData({
      endpoint,
      service: 'prompt_templates',
      method: 'GET',
      credentials: 'include',
    })

    if (response.ok) {
      const data = await response.json()
      promptTemplateOptions.value = Array.isArray(data?.items) ? data.items : []
    } else {
      promptTemplateOptions.value = []
    }
  } catch (error) {

    promptTemplateOptions.value = []
  } finally {
    loadingPromptTemplates.value = false
  }
}

function openCreateDialog() {
  if (saving.value) return
  selectedEntity.value = null
  dialogOpen.value = true
}

function editEntity(entity: EntityDefinition) {
  if (saving.value) return
  selectedEntity.value = cloneEntityDefinitions([entity])[0]
  dialogOpen.value = true
}

function onRowClick(_event: Event, row: EntityDefinition) {
  editEntity(row)
}

function onDialogCancel() {
  dialogOpen.value = false
  selectedEntity.value = null
}

async function getResponseErrorMessage(response: Response, fallbackMessage: string) {
  try {
    const errorData = await response.json()
    return errorData?.detail || errorData?.error || fallbackMessage
  } catch {
    return fallbackMessage
  }
}

async function persistEntityExtractionSettings(
  nextEntities: EntityDefinition[],
  nextExtractionSettings: EntityExtractionRunSettings,
  successMessage: string
) {
  if (saving.value) {
    return false
  }

  saving.value = true

  try {
    const endpoint = appStore.config?.api?.aiBridge?.urlAdmin
    if (!endpoint) {
      notifyError(m.knowledgeGraph_apiNotConfigured())
      return false
    }

    const nextSettings = withEntityExtractionRunSettings(withEntityDefinitions(baseSettings.value, nextEntities), nextExtractionSettings)

    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}`,
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        settings: nextSettings,
      }),
    })

    if (!response.ok) {
      const message = await getResponseErrorMessage(response, 'Failed to save entity extraction settings')
      notifyError(message)
      return false
    }

    baseSettings.value = cloneSettings(nextSettings)
    entities.value = cloneEntityDefinitions(nextEntities)
    extractionSettings.value = cloneEntityExtractionRunSettings(nextExtractionSettings)
    emit('refresh')
    notifySuccess(successMessage)

    return true
  } catch (error) {

    notifyError(m.knowledgeGraph_failedToSaveEntitySettings())
    return false
  } finally {
    saving.value = false
  }
}

async function onDialogSave(entity: EntityDefinition) {
  const nextEntity = cloneEntityDefinitions([entity])[0]
  const nextEntities = cloneEntityDefinitions(entities.value)
  const entityIndex = nextEntities.findIndex((existingEntity) => existingEntity.id === nextEntity.id)

  if (entityIndex >= 0) {
    nextEntities[entityIndex] = nextEntity
  } else {
    nextEntities.push(nextEntity)
  }

  const success = await persistEntityExtractionSettings(
    nextEntities,
    extractionSettings.value,
    entityIndex >= 0 ? m.knowledgeGraph_entityUpdated() : m.knowledgeGraph_entityCreated()
  )
  if (!success) {
    return
  }

  dialogOpen.value = false
  selectedEntity.value = null
}

async function onExtractionSettingsSave(nextSettings: EntityExtractionRunSettings) {
  const success = await persistEntityExtractionSettings(entities.value, nextSettings, m.knowledgeGraph_extractionSettingsUpdated())
  if (!success) {
    return
  }

  showExtractionDialog.value = false
}

function confirmDelete(entity: EntityDefinition) {
  if (saving.value) return
  selectedEntity.value = entity
  showDeleteDialog.value = true
}

async function performDelete() {
  if (!selectedEntity.value) return

  const remainingEntities = entities.value.filter((entity) => entity.id !== selectedEntity.value?.id)
  const success = await persistEntityExtractionSettings(remainingEntities, extractionSettings.value, m.knowledgeGraph_entityDeleted())
  if (!success) {
    return
  }

  showDeleteDialog.value = false
  selectedEntity.value = null
}

async function toggleEntityEnabled(entity: EntityDefinition, enabled: boolean) {
  const nextEntities = cloneEntityDefinitions(entities.value)
  const target = nextEntities.find((e) => e.id === entity.id)
  if (!target) return
  target.enabled = enabled
  await persistEntityExtractionSettings(nextEntities, extractionSettings.value, enabled ? m.knowledgeGraph_entityEnabled() : m.knowledgeGraph_entityDisabled())
}

const extractionStarting = ref(false)
const cancelling = ref(false)
const showRunConfirmDialog = ref(false)
const showCancelConfirmDialog = ref(false)

function onConfirmRunExtraction() {
  showRunConfirmDialog.value = false
  runExtraction()
}

function onConfirmCancelExtraction() {
  showCancelConfirmDialog.value = false
  cancelExtraction()
}

async function runExtraction() {
  if (!canRunExtraction.value || isExtractionActive.value || extractionStarting.value) return

  extractionStarting.value = true

  try {
    const endpoint = appStore.config?.api?.aiBridge?.urlAdmin
    if (!endpoint) {
      notifyError(m.knowledgeGraph_apiNotConfigured())
      return
    }

    const payload = {
      approach: extractionSettings.value.approach,
      prompt_template_system_name: String(extractionSettings.value.prompt_template_system_name || '').trim(),
      segment_size: extractionSettings.value.segment_size,
      segment_overlap: extractionSettings.value.segment_overlap,
    }

    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/entities/extract`,
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      const message = await getResponseErrorMessage(response, 'Failed to start entity extraction')
      notifyError(message)
      extractionStarting.value = false
      emit('refresh')
      return
    }

    emit('refresh')
  } catch (error) {

    notifyError(m.knowledgeGraph_errorStartingExtraction())
    extractionStarting.value = false
    emit('refresh')
  }
}

async function cancelExtraction() {
  if (cancelling.value) return
  cancelling.value = true
  try {
    const endpoint = appStore.config?.api?.aiBridge?.urlAdmin
    if (!endpoint) return
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/entities/extract/cancel`,
      method: 'POST',
      credentials: 'include',
    })
    if (!response.ok) {
      const message = await getResponseErrorMessage(response, 'Failed to cancel extraction')
      notifyError(message)
    }
    emit('refresh')
  } catch (error) {

    notifyError(m.knowledgeGraph_failedToCancelExtraction())
  } finally {
    cancelling.value = false
  }
}

watch(isExtractionActive, (active) => {
  if (active && extractionStarting.value) {
    extractionStarting.value = false
  }
})

watch(
  () => extractionStatus.value.status,
  (newStatus, oldStatus) => {
    if (oldStatus === 'running' || oldStatus === 'cancelling') {
      if (newStatus === 'completed') {
        notifySuccess(m.knowledgeGraph_extractionCompleted())
      } else if (newStatus === 'cancelled') {
        notifyWarning(m.knowledgeGraph_extractionCancelled())
      } else if (newStatus === 'error') {
        notifyError(m.knowledgeGraph_extractionFailed())
      }
    }
  }
)

watch(
  () => props.graphDetails,
  () => {
    if (saving.value) return
    initializeFromSettings()
  },
  { immediate: true, deep: true }
)

watch(
  () => props.graphId,
  () => {
    void loadPromptTemplates()
  },
  { immediate: true }
)

defineExpose({
  refresh: () => {
    initializeFromSettings()
    void loadPromptTemplates()
  },
})
</script>

<style scoped>
:deep(.q-table thead th) {
  font-size: var(--km-font-size-body);
  font-weight: 600;
}

:deep(.q-table tbody td) {
  height: 40px;
  padding: 2px 16px;
}

.entity-name-cell {
  display: flex;
  align-items: center;
}

.entity-name-text {
  font-weight: 600;
  color: var(--q-primary-text);
}

:deep(.entity-row--disabled) td:not(:last-child) {
  opacity: 0.45;
}

:deep(.entity-row-menu .q-focus-helper) {
  opacity: 0 !important;
}

:deep(.entity-row-menu .q-item.q-focusable:hover) {
  background: transparent !important;
}
</style>
