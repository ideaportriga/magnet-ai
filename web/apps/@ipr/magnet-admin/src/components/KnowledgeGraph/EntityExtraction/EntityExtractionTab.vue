<template>
  <div class="q-px-md">
    <div class="row items-start q-col-gutter-md q-mb-md">
      <div class="col">
        <div class="km-heading-7">Entity Extraction</div>
        <div class="km-description text-secondary-text">
          Define entity schemas, configure the extraction prompt, and run AI-powered extraction against this knowledge graph
        </div>
      </div>
    </div>

    <q-separator class="q-my-md" />

    <div v-if="entities.length === 0" class="q-mt-md">
      <div class="text-center q-pa-lg">
        <q-icon name="o_category" size="64px" color="grey-5" />
        <div class="km-heading-7 text-grey-7 q-mt-md">No entities defined yet</div>
        <div class="km-description text-grey-6">Create at least one entity definition so the prompt knows what to extract.</div>
        <div class="q-mt-lg q-gutter-sm">
          <q-btn no-caps unelevated color="primary" label="Create First Entity" :disable="saving" @click="openCreateDialog" />
          <q-btn no-caps flat color="primary" label="Import" icon="o_file_upload" :disable="saving" @click="triggerImport" />
        </div>
      </div>
    </div>

    <div v-else>
      <kg-table-toolbar>
        <template #leading>
          <km-btn
            v-if="isExtractionActive || extractionStarting"
            label="Cancel"
            size="sm"
            flat
            color="negative"
            :disable="cancelling || extractionStarting"
            @click="showCancelConfirmDialog = true"
          />
          <km-btn v-else label="Run Extraction" size="sm" :disable="!canRunExtraction || saving" @click="showRunConfirmDialog = true">
            <q-tooltip v-if="!canRunExtraction && !saving">Configure a prompt template in extraction settings first</q-tooltip>
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
              {{ extractionStatus.status === 'cancelling' ? 'Cancelling...' : 'Running...' }}
            </span>
          </template>

          <!-- Terminal status: completed / cancelled / error -->
          <span v-else-if="extractionStatus.status !== 'idle'" class="text-caption text-grey-7">
            {{ extractionStatusMessage }}
          </span>
        </template>

        <template #trailing>
          <km-btn flat icon="o_add_circle" label="New Entity" size="sm" :disable="saving" @click="openCreateDialog" />
          <km-btn flat icon="o_file_upload" label="Import" size="sm" :disable="saving" @click="triggerImport" />
          <km-btn
            flat
            icon="o_file_download"
            :label="exportButtonLabel"
            size="sm"
            :disable="saving || entities.length === 0"
            @click="exportEntitiesFromToolbar"
          />
          <km-btn flat icon="settings" label="Settings" size="sm" :disable="saving" @click="showExtractionDialog = true" />
          <km-btn flat icon="refresh" label="Refresh" size="sm" :disable="saving" @click="emit('refresh')" />
        </template>
      </kg-table-toolbar>

      <input ref="fileInputRef" type="file" accept="application/json,.json" class="hidden-file-input" @change="onImportFileChange">

      <q-table
        v-model:pagination="pagination"
        v-model:selected="selected"
        flat
        selection="multiple"
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
                    <q-item-section>Edit</q-item-section>
                  </q-item>
                  <q-separator />
                  <q-item v-ripple="false" clickable :disable="saving" @click="exportEntities([slotScope.row])">
                    <q-item-section thumbnail>
                      <q-icon name="o_file_download" color="primary" size="20px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>Export</q-item-section>
                  </q-item>
                  <q-separator />
                  <q-item v-ripple="false" clickable :disable="saving" @click="confirmDelete(slotScope.row)">
                    <q-item-section thumbnail>
                      <q-icon name="delete" color="negative" size="20px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>Delete</q-item-section>
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
      :performance-tuning="performanceTuning"
      :prompt-template-options="promptTemplateOptions"
      :loading-prompt-templates="loadingPromptTemplates"
      @update:show-dialog="showExtractionDialog = $event"
      @cancel="showExtractionDialog = false"
      @save="onExtractionSettingsSave"
    />

    <kg-confirm-dialog
      v-model="showDeleteDialog"
      title="Delete entity"
      icon="delete_outline"
      :description="`Are you sure you want to delete '${selectedEntity?.name}'?`"
      confirm-label="Delete"
      destructive
      :loading="saving"
      @confirm="performDelete"
    >
      <template #warning>
        This removes the entity definition from the extraction schema. Existing extracted rows are not deleted automatically.
      </template>
    </kg-confirm-dialog>

    <kg-confirm-dialog
      v-model="showRunConfirmDialog"
      title="Run entity extraction"
      icon="o_play_arrow"
      icon-variant="info"
      description="Are you sure you want to run entity extraction? This will process all documents in the knowledge graph."
      confirm-label="Run Extraction"
      @confirm="onConfirmRunExtraction"
    >
      <template #warning>Running extraction may take a while depending on the number of documents.</template>
    </kg-confirm-dialog>

    <kg-confirm-dialog
      v-model="showCancelConfirmDialog"
      title="Cancel extraction"
      icon="o_cancel"
      icon-variant="warning"
      warning-variant="warning"
      description="Are you sure you want to cancel the running extraction?"
      confirm-label="Cancel Extraction"
      destructive
      :loading="cancelling"
      @confirm="onConfirmCancelExtraction"
    >
      <template #warning>Entities already extracted will be kept, but the remaining documents will not be processed.</template>
    </kg-confirm-dialog>

    <kg-confirm-dialog
      v-model="showImportConfirmDialog"
      title="Import entity definitions"
      icon="o_file_upload"
      icon-variant="info"
      :description="importDialogDescription"
      confirm-label="Import"
      :loading="saving"
      :disable-confirm="!pendingImport || (pendingImport.added.length === 0 && pendingImport.overwritten.length === 0)"
      @update:model-value="onImportDialogToggle"
      @confirm="onConfirmImport"
    >
      <template v-if="pendingImport && (pendingImport.overwritten.length > 0 || pendingImport.warnings.length > 0)" #default>
        <div v-if="pendingImport.overwritten.length > 0" class="km-description text-secondary-text">
          <div class="text-weight-medium q-mb-xs">Will overwrite:</div>
          <div>{{ formatNameList(pendingImport.overwritten) }}</div>
        </div>
        <div v-if="pendingImport.warnings.length > 0" class="km-description text-warning q-mt-sm">
          <div class="text-weight-medium q-mb-xs">Warnings:</div>
          <ul class="q-my-none q-pl-md">
            <li v-for="(warning, i) in pendingImport.warnings" :key="i">{{ warning }}</li>
          </ul>
        </div>
      </template>
      <template v-if="pendingImport && pendingImport.overwritten.length > 0" #warning>
        Overwriting an entity replaces its definition. Existing extracted rows are not deleted automatically.
      </template>
    </kg-confirm-dialog>
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import type { QTableColumn } from 'quasar'
import { useQuasar } from 'quasar'
import { computed, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { KgConfirmDialog, KgTableToolbar } from '../common'
import EntityDialog from './EntityDialog.vue'
import EntityExtractionSettingsDialog from './EntityExtractionSettingsDialog.vue'
import {
  cloneEntityDefinitions,
  cloneEntityExtractionPerformanceTuningSettings,
  cloneEntityExtractionRunSettings,
  createDefaultEntityExtractionRunSettings,
  createDefaultPerformanceTuningSettings,
  getEntityExtractionSettingsFromSettings,
  getExtractionStatusFromGraphDetails,
  mergeEntityDefinitions,
  parseEntityDefinitionsFromImport,
  serializeEntityDefinitionsForExport,
  withEntityDefinitions,
  withEntityExtractionPerformanceTuning,
  withEntityExtractionRunSettings,
  type EntityDefinition,
  type EntityDefinitionsMergeResult,
  type EntityExtractionPerformanceTuningSettings,
  type EntityExtractionRunSettings,
  type EntityExtractionStatusInfo,
} from './models'
import type { EntityExtractionDialogPayload } from './EntityExtractionSettingsDialog.vue'

const props = defineProps<{
  graphId: string
  graphDetails: Record<string, any>
}>()

const emit = defineEmits<{
  refresh: []
}>()

const store = useStore()
const $q = useQuasar()

const entities = ref<EntityDefinition[]>([])
const extractionSettings = ref<EntityExtractionRunSettings>(createDefaultEntityExtractionRunSettings())
const performanceTuning = ref<EntityExtractionPerformanceTuningSettings>(createDefaultPerformanceTuningSettings())
const selectedEntity = ref<EntityDefinition | null>(null)
const selected = ref<EntityDefinition[]>([])
const dialogOpen = ref(false)
const showDeleteDialog = ref(false)
const showExtractionDialog = ref(false)
const pagination = ref({ rowsPerPage: 10, page: 1 })
const saving = ref(false)
const loadingPromptTemplates = ref(false)
const promptTemplateOptions = ref<any[]>([])
const baseSettings = ref<Record<string, any>>({})

const fileInputRef = ref<HTMLInputElement | null>(null)
const showImportConfirmDialog = ref(false)
const pendingImport = ref<(EntityDefinitionsMergeResult & { warnings: string[] }) | null>(null)

const exportButtonLabel = computed(() => (selected.value.length > 0 ? `Export (${selected.value.length})` : 'Export'))

const importDialogDescription = computed(() => {
  if (!pendingImport.value) return ''
  const parts: string[] = []
  if (pendingImport.value.added.length > 0) {
    parts.push(`${pendingImport.value.added.length} new`)
  }
  if (pendingImport.value.overwritten.length > 0) {
    parts.push(`${pendingImport.value.overwritten.length} to overwrite`)
  }
  if (parts.length === 0) {
    return 'No entity definitions to import.'
  }
  return `About to import: ${parts.join(', ')}.`
})

const columns: QTableColumn<EntityDefinition>[] = [
  {
    name: 'name',
    label: 'Entity',
    field: 'name',
    align: 'left',
    sortable: true,
  },
  {
    name: 'description',
    label: 'Description',
    field: 'description',
    align: 'left',
    sortable: false,
    style: 'max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis',
  },
  {
    name: 'columns_count',
    label: 'Columns',
    field: (row) => row.columns.length,
    align: 'left',
    sortable: true,
  },
  {
    name: 'identifier',
    label: 'Identifier',
    field: (row) => row.columns.find((column) => column.is_identifier)?.name || '',
    align: 'left',
    sortable: false,
  },
  {
    name: 'enabled',
    label: 'Active',
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
  const mode = extractionSettings.value.mode
  let promptsConfigured: boolean
  if (mode === 'reflective') {
    promptsConfigured = !!String(extractionSettings.value.reflective_prompt_template_system_name || '').trim()
  } else if (mode === 'self-tuning') {
    promptsConfigured =
      !!String(extractionSettings.value.self_tuning_prompt_template_system_name || '').trim() &&
      !!String(extractionSettings.value.self_tuning_analysis_prompt_template_system_name || '').trim()
  } else {
    promptsConfigured = !!String(extractionSettings.value.prompt_template_system_name || '').trim()
  }
  return promptsConfigured && entities.value.length > 0 && !loadingPromptTemplates.value
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
  performanceTuning.value = cloneEntityExtractionPerformanceTuningSettings(normalizedSettings.advanced_settings)
  if (selected.value.length > 0) {
    const validIds = new Set(entities.value.map((entity) => entity.id))
    selected.value = selected.value.filter((entity) => validIds.has(entity.id))
  }
}

async function loadPromptTemplates() {
  loadingPromptTemplates.value = true
  try {
    const endpoint = store.getters.config?.api?.aiBridge?.urlAdmin
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
    console.error('Error loading prompt templates:', error)
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
  successMessage: string,
  nextPerformanceTuning: EntityExtractionPerformanceTuningSettings = performanceTuning.value
) {
  if (saving.value) {
    return false
  }

  saving.value = true

  try {
    const endpoint = store.getters.config?.api?.aiBridge?.urlAdmin
    if (!endpoint) {
      $q.notify({ type: 'negative', message: 'Knowledge graph API is not configured', position: 'top' })
      return false
    }

    const nextSettings = withEntityExtractionPerformanceTuning(
      withEntityExtractionRunSettings(withEntityDefinitions(baseSettings.value, nextEntities), nextExtractionSettings),
      nextPerformanceTuning
    )

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
      $q.notify({ type: 'negative', message, position: 'top' })
      return false
    }

    baseSettings.value = cloneSettings(nextSettings)
    entities.value = cloneEntityDefinitions(nextEntities)
    extractionSettings.value = cloneEntityExtractionRunSettings(nextExtractionSettings)
    performanceTuning.value = cloneEntityExtractionPerformanceTuningSettings(nextPerformanceTuning)
    emit('refresh')
    $q.notify({
      type: 'positive',
      message: successMessage,
      position: 'top',
      textColor: 'black',
      timeout: 1500,
    })

    return true
  } catch (error) {
    console.error('Error saving entity extraction settings:', error)
    $q.notify({ type: 'negative', message: 'Failed to save entity extraction settings', position: 'top' })
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
    entityIndex >= 0 ? 'Entity updated' : 'Entity created'
  )
  if (!success) {
    return
  }

  dialogOpen.value = false
  selectedEntity.value = null
}

async function onExtractionSettingsSave(payload: EntityExtractionDialogPayload) {
  const success = await persistEntityExtractionSettings(
    entities.value,
    payload.extraction,
    'Entity extraction settings updated',
    payload.advanced_settings
  )
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
  const success = await persistEntityExtractionSettings(remainingEntities, extractionSettings.value, 'Entity deleted')
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
  await persistEntityExtractionSettings(nextEntities, extractionSettings.value, enabled ? 'Entity enabled' : 'Entity disabled')
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
    const endpoint = store.getters.config?.api?.aiBridge?.urlAdmin
    if (!endpoint) {
      $q.notify({ type: 'negative', message: 'Knowledge graph API is not configured', position: 'top' })
      return
    }

    const payload = {
      approach: extractionSettings.value.approach,
      mode: extractionSettings.value.mode,
      schema_format: performanceTuning.value.schema_format,
      prompt_template_system_name: String(extractionSettings.value.prompt_template_system_name || '').trim(),
      reflective_prompt_template_system_name: String(extractionSettings.value.reflective_prompt_template_system_name || '').trim(),
      segment_size: extractionSettings.value.segment_size,
      segment_overlap: extractionSettings.value.segment_overlap,
      max_extraction_iterations: performanceTuning.value.max_extraction_iterations,
      relevance_filter_prompt_template_system_name: String(performanceTuning.value.relevance_filter.prompt_template_system_name || '').trim(),
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
      $q.notify({ type: 'negative', message, position: 'top' })
      extractionStarting.value = false
      emit('refresh')
      return
    }

    emit('refresh')
  } catch (error) {
    console.error('Error starting entity extraction:', error)
    $q.notify({ type: 'negative', message: 'Error starting entity extraction', position: 'top' })
    extractionStarting.value = false
    emit('refresh')
  }
}

async function cancelExtraction() {
  if (cancelling.value) return
  cancelling.value = true
  try {
    const endpoint = store.getters.config?.api?.aiBridge?.urlAdmin
    if (!endpoint) return
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/entities/extract/cancel`,
      method: 'POST',
      credentials: 'include',
    })
    if (!response.ok) {
      const message = await getResponseErrorMessage(response, 'Failed to cancel extraction')
      $q.notify({ type: 'negative', message, position: 'top' })
    }
    emit('refresh')
  } catch (error) {
    console.error('Error cancelling extraction:', error)
    $q.notify({ type: 'negative', message: 'Failed to cancel extraction', position: 'top' })
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
        $q.notify({ type: 'positive', message: 'Entity extraction completed', position: 'top', textColor: 'black', timeout: 2000 })
      } else if (newStatus === 'cancelled') {
        $q.notify({ type: 'warning', message: 'Entity extraction cancelled', position: 'top', timeout: 2000 })
      } else if (newStatus === 'error') {
        $q.notify({ type: 'negative', message: 'Entity extraction failed', position: 'top', timeout: 3000 })
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

function slugifyName(value: string): string {
  return (value || '')
    .toString()
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function buildExportFilename(list: EntityDefinition[]): string {
  if (list.length === 1) {
    const slug = slugifyName(list[0].name) || 'entity'
    return `kg-entity-${slug}.json`
  }
  const graphSlug = slugifyName(props.graphDetails?.name) || 'graph'
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  const stamp =
    `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}` + `-${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`
  return `kg-entities-${graphSlug}-${stamp}.json`
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function exportEntities(list: EntityDefinition[]) {
  if (list.length === 0) {
    $q.notify({ type: 'warning', message: 'No entities to export', position: 'top' })
    return
  }
  const json = serializeEntityDefinitionsForExport(list)
  const blob = new Blob([json], { type: 'application/json' })
  triggerDownload(blob, buildExportFilename(list))
}

function exportEntitiesFromToolbar() {
  const list = selected.value.length > 0 ? selected.value : entities.value
  exportEntities(list)
}

function triggerImport() {
  if (saving.value) return
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
    fileInputRef.value.click()
  }
}

function formatNameList(names: string[], max = 8): string {
  if (names.length <= max) return names.join(', ')
  return `${names.slice(0, max).join(', ')} and ${names.length - max} more`
}

async function onImportFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  try {
    const text = await file.text()
    const parsed = parseEntityDefinitionsFromImport(text)

    if (parsed.entities.length === 0) {
      const message = parsed.warnings.length > 0 ? parsed.warnings[0] : 'No valid entity definitions found in file'
      $q.notify({ type: 'negative', message, position: 'top' })
      return
    }

    const merge = mergeEntityDefinitions(entities.value, parsed.entities)
    pendingImport.value = { ...merge, warnings: parsed.warnings }
    showImportConfirmDialog.value = true
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to parse import file'
    $q.notify({ type: 'negative', message, position: 'top' })
  } finally {
    if (input) input.value = ''
  }
}

function onImportDialogToggle(value: boolean) {
  showImportConfirmDialog.value = value
  if (!value) {
    pendingImport.value = null
  }
}

async function onConfirmImport() {
  if (!pendingImport.value) return
  const success = await persistEntityExtractionSettings(pendingImport.value.merged, extractionSettings.value, 'Entity definitions imported')
  if (!success) return

  selected.value = []
  showImportConfirmDialog.value = false
  pendingImport.value = null
}

defineExpose({
  refresh: () => {
    initializeFromSettings()
    void loadPromptTemplates()
  },
})
</script>

<style scoped>
:deep(.q-table thead th) {
  font-size: 14px;
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
  color: #1a1a2e;
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

.hidden-file-input {
  display: none;
}
</style>
