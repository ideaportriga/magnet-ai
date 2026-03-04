<template>
  <kg-dialog-source-base
    :show-dialog="dialogOpen"
    :source="props.source || null"
    :title="isEditMode ? 'Edit Salesforce Connection' : 'Connect to Salesforce'"
    :confirm-label="isEditMode ? 'Save Changes' : 'Connect'"
    :loading="loading"
    :disable-confirm="loading || !isFormValid"
    :error="error"
    size="md"
    syncable
    @update:show-dialog="(v: boolean) => emit('update:showDialog', v)"
    @cancel="emit('cancel')"
    @confirm="onConfirm"
    @changed="clearError"
  >
    <kg-dialog-section
      title="Connection"
      description="Salesforce Knowledge Article View object to sync. Must end with __kav (e.g. ServiceArticle__kav)."
      icon="link"
    >
      <div class="q-mb-md">
        <div class="km-input-label q-pb-xs">Object API Name <span class="text-negative">*</span></div>
        <km-input
          ref="objectApiNameRef"
          v-model="objectApiName"
          height="36px"
          placeholder="ServiceArticle__kav"
          :rules="objectApiNameRules"
          required
        />
      </div>
    </kg-dialog-section>

    <kg-dialog-section
      title="Credentials"
      description="Select the Salesforce Knowledge Source Provider that holds the connection credentials for this source."
      icon="key"
    >
      <div class="q-mb-md">
        <div class="km-input-label q-pb-xs">Provider <span class="text-negative">*</span></div>
        <q-select
          v-model="providerSystemName"
          outlined
          dense
          emit-value
          map-options
          :options="knowledgeProviderOptions"
          option-value="system_name"
          option-label="name"
          placeholder="Select a Knowledge Source Provider"
          clearable
        >
          <template #no-option>
            <q-item>
              <q-item-section class="text-grey">No Knowledge Source Providers configured</q-item-section>
            </q-item>
          </template>
        </q-select>
      </div>
    </kg-dialog-section>

    <kg-dialog-section
      title="Content Template"
      description="A Python format-string that defines the content of each document. Use {FieldName} placeholders for Salesforce fields. For Q&amp;A articles use e.g. 'question: {Question__c}\nanswer: {Answer__c}'."
      icon="description"
    >
      <div class="q-mb-md">
        <div class="km-input-label q-pb-xs">Template <span class="text-negative">*</span></div>
        <q-input
          v-model="contentTemplate"
          outlined
          dense
          autogrow
          type="textarea"
          placeholder="question: {Question__c}&#10;answer: {Answer__c}"
          :rules="contentTemplateRules"
        />
      </div>
    </kg-dialog-section>

    <kg-dialog-section
      title="Metadata Fields"
      description="Salesforce fields to include as document metadata. Standard Knowledge Article fields are pre-selected. Add custom fields from your KAV object as needed."
      icon="label"
    >
      <q-select
        v-model="metadataFields"
        multiple
        outlined
        dense
        use-input
        use-chips
        input-debounce="0"
        new-value-mode="add-unique"
        :options="metadataFieldOptions"
        @filter="filterMetadataFields"
        @new-value="addMetadataField"
      >
        <template #no-option>
          <q-item>
            <q-item-section class="text-grey">
              Type a field name and press Enter to add it
            </q-item-section>
          </q-item>
        </template>
      </q-select>
      <div class="text-grey-7 text-caption q-mt-xs">
        Type a field name and press <kbd>Enter</kbd> to add custom fields.
      </div>
    </kg-dialog-section>
  </kg-dialog-source-base>
</template>

<script setup lang="ts">
import { fetchData, useChroma } from '@shared'
import { useQuasar } from 'quasar'
import { computed, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { KgDialogSection, KgDialogSourceBase, ScheduleFormState } from '../../common'
import type { SourceRow } from '../models'

// Standard Salesforce Knowledge Article View fields available on all __kav objects
const SALESFORCE_DEFAULT_METADATA_FIELDS: string[] = [
  'Title',
  'ArticleNumber',
  'UrlName',
  'Summary',
  'Language',
  'LastPublishedDate',
  'PublishStatus',
  'KnowledgeArticleId',
]

type SalesforceSourceConfig = {
  object_api_name?: string
  content_template?: string
  provider_system_name?: string | null
  metadata_fields?: string[] | null
}

type SalesforceSourceRecord = Omit<SourceRow, 'type' | 'config'> & {
  type: 'salesforce'
  config?: SalesforceSourceConfig | null
}

const props = defineProps<{
  showDialog: boolean
  graphId: string
  source?: SalesforceSourceRecord | null
}>()

const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'created', result: any): void
  (e: 'update:showDialog', value: boolean): void
}>()

const store = useStore()
const $q = useQuasar()

// Providers (for knowledge-category provider dropdown)
const { items: allProviders } = useChroma('provider')
const knowledgeProviderOptions = computed(() =>
  (allProviders.value || []).filter((p: any) => p.category === 'knowledge'),
)

// Form fields
const objectApiName = ref('')
const contentTemplate = ref('')
const providerSystemName = ref<string | null>(null)
const metadataFields = ref<string[]>([...SALESFORCE_DEFAULT_METADATA_FIELDS])

// Metadata field selector state
const allMetadataFieldOptions = ref<string[]>([...SALESFORCE_DEFAULT_METADATA_FIELDS])
const metadataFieldOptions = ref<string[]>([...SALESFORCE_DEFAULT_METADATA_FIELDS])

// UI state
const loading = ref(false)
const error = ref('')

// Refs for field-level validation
const objectApiNameRef = ref<any>(null)

// Validation
const objectApiNameRules = [
  (val: string) => !!(val && val.trim()) || 'Object API name is required',
  (val: string) =>
    /^[a-zA-Z][a-zA-Z0-9]*(?:_[a-zA-Z0-9]+)*__kav$/.test(val || '') ||
    'Must be a valid Knowledge Article View name (e.g. ServiceArticle__kav)',
]

const contentTemplateRules = [
  (val: string) => !!(val && val.trim()) || 'Content template is required',
  (val: string) =>
    /\{[^}]+\}/.test(val || '') || 'Template must reference at least one field using {FieldName} syntax',
]

const isFormValid = computed(
  () =>
    !!objectApiName.value.trim() &&
    !!contentTemplate.value.trim() &&
    /\{[^}]+\}/.test(contentTemplate.value) &&
    !!providerSystemName.value,
)

const isEditMode = computed(() => !!props.source)
const dialogOpen = computed(() => props.showDialog)

// Prefill or reset when dialog opens
watch(
  () => [props.showDialog, props.source] as const,
  () => {
    if (props.showDialog) {
      if (props.source) {
        try {
          const cfg = (props.source?.config || {}) as SalesforceSourceConfig
          objectApiName.value = cfg.object_api_name || ''
          contentTemplate.value = cfg.content_template || ''
          providerSystemName.value = cfg.provider_system_name || null
          metadataFields.value =
            Array.isArray(cfg.metadata_fields) && cfg.metadata_fields.length
              ? [...cfg.metadata_fields]
              : [...SALESFORCE_DEFAULT_METADATA_FIELDS]
        } catch {
          // ignore prefill errors
        }
      } else {
        // Create mode — clean slate with sensible defaults
        objectApiName.value = ''
        contentTemplate.value = ''
        providerSystemName.value = null
        metadataFields.value = [...SALESFORCE_DEFAULT_METADATA_FIELDS]
      }

      // Ensure any custom fields from config are available as options
      const combined = new Set([...SALESFORCE_DEFAULT_METADATA_FIELDS, ...metadataFields.value])
      allMetadataFieldOptions.value = Array.from(combined)
      metadataFieldOptions.value = [...allMetadataFieldOptions.value]
    }
  },
  { immediate: true },
)

function filterMetadataFields(val: string, update: (fn: () => void) => void) {
  update(() => {
    if (!val.trim()) {
      metadataFieldOptions.value = allMetadataFieldOptions.value.filter(
        (o) => !metadataFields.value.includes(o),
      )
    } else {
      const needle = val.toLowerCase()
      metadataFieldOptions.value = allMetadataFieldOptions.value.filter(
        (o) => o.toLowerCase().includes(needle) && !metadataFields.value.includes(o),
      )
    }
  })
}

function addMetadataField(val: string, done: (v?: string, mode?: string) => void) {
  const trimmed = val.trim()
  if (trimmed && !allMetadataFieldOptions.value.includes(trimmed)) {
    allMetadataFieldOptions.value = [...allMetadataFieldOptions.value, trimmed]
  }
  done(trimmed, 'add-unique')
}

function buildCron(schedule: ScheduleFormState) {
  if (schedule.interval === 'none') return null
  if (schedule.interval === 'hourly') return { minute: 0, hour: '*' }
  if (schedule.interval === 'daily') return { minute: 0, hour: schedule.hour }
  return { minute: 0, hour: schedule.hour, day_of_week: schedule.day }
}

async function applySchedule(sourceId: string, schedule: ScheduleFormState) {
  const shouldCall =
    schedule.interval !== 'none' ||
    (props.source?.schedule !== null && props.source?.schedule !== undefined)
  if (!shouldCall) return

  const endpoint = store.getters.config.api.aiBridge.urlAdmin
  const payload: any = { interval: schedule.interval }
  if (schedule.interval !== 'none') {
    payload.timezone = schedule.timezone
    payload.cron = buildCron(schedule)
  }

  const response = await fetchData({
    endpoint,
    service: `knowledge_graphs/${props.graphId}/sources/${sourceId}/schedule_sync`,
    method: 'POST',
    credentials: 'include',
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
  })

  if (response.ok) return

  let msg = 'Failed to update sync schedule'
  try {
    const err = await response.json()
    msg = err?.detail || err?.error || msg
  } catch {
    // ignore parse errors
  }
  throw new Error(msg)
}

function clearError() {
  if (error.value) error.value = ''
}

function buildConfig(): SalesforceSourceConfig {
  return {
    object_api_name: objectApiName.value.trim(),
    content_template: contentTemplate.value.trim(),
    provider_system_name: providerSystemName.value || null,
    metadata_fields: metadataFields.value.length ? metadataFields.value : null,
  }
}

async function addSource(sourceName: string, schedule: ScheduleFormState) {
  const nameOk = await (objectApiNameRef.value?.validate?.() ?? true)
  if (!nameOk) return

  loading.value = true
  error.value = ''

  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin

    const payload = {
      type: 'salesforce',
      name: sourceName.trim() || null,
      config: buildConfig(),
    }

    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/sources`,
      method: 'POST',
      credentials: 'include',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    })

    if (response.ok) {
      const result = await response.json()
      if (schedule.interval !== 'none') {
        try {
          await applySchedule(result.id, schedule)
        } catch (e: any) {
          $q.notify({
            type: 'negative',
            message: e?.message || 'Source created, but schedule could not be saved',
            position: 'top',
          })
        }
      }
      emit('created', result)
    } else {
      const errorData = await response.json()
      error.value = errorData.detail || errorData.error || 'Failed to connect to Salesforce'
    }
  } catch (err) {
    console.error('Salesforce connection error:', err)
    error.value = 'Failed to connect to Salesforce. Please try again.'
  } finally {
    loading.value = false
  }
}

async function updateSource(sourceName: string, schedule: ScheduleFormState) {
  if (!props.source) return
  const nameOk = await (objectApiNameRef.value?.validate?.() ?? true)
  if (!nameOk) return

  loading.value = true
  error.value = ''

  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const payload = {
      name: sourceName.trim() || null,
      config: buildConfig(),
    }

    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/sources/${props.source.id}`,
      method: 'PATCH',
      credentials: 'include',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    })

    if (response.ok) {
      const result = await response.json()
      await applySchedule(props.source.id, schedule)
      emit('created', result)
    } else {
      const errorData = await response.json()
      error.value = errorData.detail || errorData.error || 'Failed to save Salesforce source'
    }
  } catch (err) {
    console.error('Salesforce update error:', err)
    error.value = 'Failed to save Salesforce source. Please try again.'
  } finally {
    loading.value = false
  }
}

async function onConfirm(payload: { sourceName: string; schedule: ScheduleFormState }) {
  if (isEditMode.value) {
    await updateSource(payload.sourceName, payload.schedule)
  } else {
    await addSource(payload.sourceName, payload.schedule)
  }
}

// Clear error when user edits any field
watch([objectApiName, contentTemplate, providerSystemName, metadataFields], () => {
  if (error.value) error.value = ''
})
</script>
