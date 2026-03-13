<template>
  <div class="q-px-md">
    <div class="row items-start q-col-gutter-md q-mb-md">
      <div class="col">
        <div class="km-heading-7">Entity Extraction</div>
        <div class="km-description text-secondary-text">
          Define entity schemas, configure the extraction prompt, and run AI-powered extraction against this knowledge graph
        </div>
      </div>
      <div class="col-auto row q-gutter-sm">
        <km-btn flat label="Extraction Settings" icon="settings" size="sm" :disable="saving" @click="showExtractionDialog = true" />
        <km-btn
          label="Run Extraction"
          icon="auto_awesome"
          size="sm"
          :disable="!canRunExtraction || saving"
          :loading="runningExtraction"
          @click="runExtraction"
        />
        <km-btn label="New Entity" icon="add" size="sm" :disable="saving" @click="openCreateDialog" />
      </div>
    </div>

    <q-separator class="q-my-md" />

    <div v-if="entities.length === 0" class="q-mt-md">
      <div class="text-center q-pa-lg">
        <q-icon name="o_category" size="64px" color="grey-5" />
        <div class="km-heading-7 text-grey-7 q-mt-md">No entities defined yet</div>
        <div class="km-description text-grey-6">Create at least one entity definition so the prompt knows what to extract.</div>
        <q-btn
          no-caps
          unelevated
          color="primary"
          label="Create First Entity"
          class="q-mt-lg"
          icon="add"
          :disable="saving"
          @click="openCreateDialog"
        />
      </div>
    </div>

    <div v-else class="q-mt-md">
      <q-table
        v-model:pagination="pagination"
        flat
        table-header-class="bg-primary-light"
        :rows="entities"
        :columns="columns"
        row-key="id"
        :loading="saving || runningExtraction"
        :rows-per-page-options="[10]"
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

        <template #body-cell-identifier="slotScope">
          <q-td :props="slotScope">
            <div v-if="getIdentifierColumn(slotScope.row)" class="row items-center q-gap-4">
              <q-icon name="o_key" size="14px" color="amber-8" />
              <span class="entity-identifier-name">{{ getIdentifierColumn(slotScope.row)?.name }}</span>
            </div>
            <span v-else class="text-grey-5 italic text-caption">None set</span>
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
      <template #warning>This removes the entity definition from the extraction schema. Existing extracted rows are not deleted automatically.</template>
    </kg-confirm-dialog>
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import type { QTableColumn } from 'quasar'
import { useQuasar } from 'quasar'
import { computed, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { KgConfirmDialog } from '../common'
import EntityDialog from './EntityDialog.vue'
import EntityExtractionSettingsDialog from './EntityExtractionSettingsDialog.vue'
import {
  cloneEntityDefinitions,
  cloneEntityExtractionRunSettings,
  createDefaultEntityExtractionRunSettings,
  getEntityExtractionSettingsFromSettings,
  withEntityDefinitions,
  withEntityExtractionRunSettings,
  type EntityDefinition,
  type EntityExtractionRunSettings,
} from './models'

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
const selectedEntity = ref<EntityDefinition | null>(null)
const dialogOpen = ref(false)
const showDeleteDialog = ref(false)
const showExtractionDialog = ref(false)
const pagination = ref({ rowsPerPage: 10, page: 1 })
const saving = ref(false)
const runningExtraction = ref(false)
const loadingPromptTemplates = ref(false)
const promptTemplateOptions = ref<any[]>([])
const baseSettings = ref<Record<string, any>>({})

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
    name: 'menu',
    label: '',
    field: 'id',
  },
]

const canRunExtraction = computed(() => {
  return !!String(extractionSettings.value.prompt_template_system_name || '').trim() && entities.value.length > 0 && !loadingPromptTemplates.value
})

const existingEntityNames = computed(() => {
  const editingEntityId = selectedEntity.value?.id
  return entities.value.filter((entity) => entity.id !== editingEntityId).map((entity) => entity.name)
})

function getIdentifierColumn(entity: EntityDefinition) {
  return entity.columns.find((column) => column.is_identifier) || null
}

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
  successMessage: string
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

    const nextSettings = withEntityExtractionRunSettings(
      withEntityDefinitions(baseSettings.value, nextEntities),
      nextExtractionSettings
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

async function onExtractionSettingsSave(nextSettings: EntityExtractionRunSettings) {
  const success = await persistEntityExtractionSettings(entities.value, nextSettings, 'Entity extraction settings updated')
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

async function runExtraction() {
  if (!canRunExtraction.value) return

  runningExtraction.value = true
  try {
    const endpoint = store.getters.config?.api?.aiBridge?.urlAdmin
    if (!endpoint) {
      $q.notify({ type: 'negative', message: 'Knowledge graph API is not configured', position: 'top' })
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
      $q.notify({ type: 'negative', message, position: 'top' })
      return
    }

    const data: Record<string, any> = await response.json().catch(() => ({}))
    const processedDocuments = Number(data?.processed_documents || 0)
    const processedChunks = Number(data?.processed_chunks || 0)
    const upsertedRecords = Number(data?.upserted_records || 0)
    const errors = Number(data?.errors || 0)
    const approach = String(data?.approach || extractionSettings.value.approach)
    const message =
      approach === 'chunks'
        ? `Entity extraction completed: ${upsertedRecords} records merged from ${processedChunks} chunks across ${processedDocuments} documents${errors ? ` (${errors} errors)` : ''}.`
        : `Entity extraction completed: ${upsertedRecords} records merged from ${processedDocuments} documents${errors ? ` (${errors} errors)` : ''}.`

    $q.notify({
      type: 'positive',
      message,
      position: 'top',
      textColor: 'black',
      timeout: 3000,
    })

    emit('refresh')
  } catch (error) {
    console.error('Error running entity extraction:', error)
    $q.notify({ type: 'negative', message: 'Error running entity extraction', position: 'top' })
  } finally {
    runningExtraction.value = false
  }
}

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
  font-size: 14px;
  font-weight: 600;
}

.entity-name-cell {
  display: flex;
  align-items: center;
}

.entity-name-text {
  font-weight: 600;
  color: #1a1a2e;
}

.entity-identifier-name {
  font-size: 13px;
  font-weight: 500;
  color: #b8860b;
  font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
}

:deep(.entity-row-menu .q-focus-helper) {
  opacity: 0 !important;
}

:deep(.entity-row-menu .q-item.q-focusable:hover) {
  background: transparent !important;
}
</style>
