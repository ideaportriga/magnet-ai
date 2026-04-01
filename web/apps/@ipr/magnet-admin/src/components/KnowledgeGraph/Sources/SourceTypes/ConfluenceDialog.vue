<template>
  <kg-dialog-source-base
    :show-dialog="dialogOpen"
    :source="props.source || null"
    :title="isEditMode ? 'Edit Confluence Connection' : 'Connect to Confluence'"
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
      title="Provider"
      description="Select the Knowledge Source provider that holds your Confluence credentials."
      icon="key"
    >
      <q-select
        v-model="selectedProvider"
        :options="providerOptions"
        option-label="name"
        option-value="id"
        emit-value
        map-options
        placeholder="Select a Confluence provider"
        outlined
        dense
        :loading="loadingProviders"
        :no-options-label="loadingProviders ? 'Loading providers...' : 'No Confluence providers found'"
        @update:model-value="clearError"
      />
      <div v-if="!loadingProviders && providerOptions.length === 0" class="text-caption text-negative q-mt-xs">
        No Confluence Knowledge Source providers found. Create one in Knowledge Providers first.
      </div>
    </kg-dialog-section>

    <kg-dialog-section
      title="Space Key"
      description="The Confluence space key to synchronize, e.g. 'ENG' or 'KB'."
      icon="folder"
    >
      <km-input
        v-model="spaceKey"
        height="36px"
        placeholder="ENG"
        @update:model-value="clearError"
      />
    </kg-dialog-section>

    <kg-dialog-section
      title="Include Root Page Prefix"
      description="When enabled, each page title is prefixed with its root ancestor page title."
      icon="account_tree"
    >
      <q-toggle
        v-model="includeRootPrefix"
        label="Prepend root ancestor title"
        @update:model-value="clearError"
      />
    </kg-dialog-section>

    <kg-dialog-section
      title="Metadata Fields"
      description="Comma-separated list of metadata field keys to store on each document (for filtering/retrieval). E.g. title, version_when, created_date"
      icon="label"
    >
      <km-input
        v-model="metadataFields"
        height="36px"
        placeholder="title, version_when, created_date"
        @update:model-value="clearError"
      />
    </kg-dialog-section>
  </kg-dialog-source-base>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { computed, ref, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useNotify } from '@/composables/useNotify'
import { useEntityQueries } from '@/queries/entities'
import { KgDialogSection, KgDialogSourceBase, ScheduleFormState } from '../../common'
import type { SourceRow } from '../models'

type ConfluenceSourceConfig = {
  ks_provider_id?: string
  space_key?: string
  include_root_prefix?: boolean
  metadata_fields?: string
}

type ConfluenceSourceRecord = Omit<SourceRow, 'type' | 'config'> & {
  type: 'confluence'
  config?: ConfluenceSourceConfig | null
}

type ProviderOption = {
  id: string
  name: string
}

const DEFAULT_SPACE_KEY = ''
const DEFAULT_INCLUDE_ROOT_PREFIX = true
const DEFAULT_METADATA_FIELDS = 'title, version_when, created_date'

const props = defineProps<{
  showDialog: boolean
  graphId: string
  source?: ConfluenceSourceRecord | null
}>()

const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'created', result: any): void
  (e: 'update:showDialog', value: boolean): void
}>()

const appStore = useAppStore()
const { notifyError } = useNotify()
const queries = useEntityQueries()
const { data: providerListData } = queries.provider.useList()
const error = ref('')
const loading = ref(false)
const loadingProviders = ref(false)

const providerOptions = ref<ProviderOption[]>([])
const selectedProvider = ref<string>('')
const spaceKey = ref(DEFAULT_SPACE_KEY)
const includeRootPrefix = ref(DEFAULT_INCLUDE_ROOT_PREFIX)
const metadataFields = ref(DEFAULT_METADATA_FIELDS)

const isEditMode = computed(() => !!props.source)
const dialogOpen = computed(() => props.showDialog)

const isFormValid = computed(
  () => !!selectedProvider.value && !!spaceKey.value.trim()
)

// ------------------------------------------------------------------
// Provider loading
// ------------------------------------------------------------------

const loadProviders = async () => {
  loadingProviders.value = true
  try {
    const items: any[] = providerListData.value?.items || []
    providerOptions.value = items
      .filter((p: any) => p.category === 'knowledge' && p.type?.toLowerCase() === 'confluence')
      .map((p: any) => ({ id: p.id, name: p.name }))
  } catch (err) {

  } finally {
    loadingProviders.value = false
  }
}

// ------------------------------------------------------------------
// Form prefill / reset
// ------------------------------------------------------------------

watch(
  () => [props.showDialog, props.source] as const,
  async () => {
    if (props.showDialog) {
      await loadProviders()
      if (props.source) {
        selectedProvider.value = props.source.config?.ks_provider_id || ''
        spaceKey.value = props.source.config?.space_key || DEFAULT_SPACE_KEY
        includeRootPrefix.value = props.source.config?.include_root_prefix ?? DEFAULT_INCLUDE_ROOT_PREFIX
        metadataFields.value = props.source.config?.metadata_fields || DEFAULT_METADATA_FIELDS
      } else {
        selectedProvider.value = ''
        spaceKey.value = DEFAULT_SPACE_KEY
        includeRootPrefix.value = DEFAULT_INCLUDE_ROOT_PREFIX
        metadataFields.value = DEFAULT_METADATA_FIELDS
        error.value = ''
      }
    }
  },
  { immediate: true }
)

// ------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------

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

  const endpoint = appStore.config.api.aiBridge.urlAdmin
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

const clearError = () => {
  if (error.value) error.value = ''
}

// ------------------------------------------------------------------
// Create / Update
// ------------------------------------------------------------------

const buildConfig = () => ({
  ks_provider_id: selectedProvider.value,
  space_key: spaceKey.value.trim(),
  include_root_prefix: includeRootPrefix.value,
  metadata_fields: metadataFields.value.trim() || DEFAULT_METADATA_FIELDS,
})

const addSource = async (sourceName: string, schedule: ScheduleFormState) => {
  loading.value = true
  error.value = ''

  try {
    const endpoint = appStore.config.api.aiBridge.urlAdmin
    const payload = {
      type: 'confluence',
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
          notifyError(e?.message || 'Source created, but schedule could not be saved')
        }
      }
      emit('created', result)
    } else {
      const errorData = await response.json()
      error.value = errorData.detail || errorData.error || 'Failed to connect to Confluence'
    }
  } catch (err: any) {

    error.value = err.message || 'Failed to connect to Confluence. Please try again.'
  } finally {
    loading.value = false
  }
}

const updateSource = async (sourceName: string, schedule: ScheduleFormState) => {
  if (!props.source) return
  loading.value = true
  error.value = ''

  try {
    const endpoint = appStore.config.api.aiBridge.urlAdmin
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
      error.value = errorData.detail || errorData.error || 'Failed to save Confluence source'
    }
  } catch (err: any) {

    error.value = err.message || 'Failed to save Confluence source. Please try again.'
  } finally {
    loading.value = false
  }
}

const onConfirm = async (payload: { sourceName: string; schedule: ScheduleFormState }) => {
  if (isEditMode.value) {
    await updateSource(payload.sourceName, payload.schedule)
  } else {
    await addSource(payload.sourceName, payload.schedule)
  }
}

watch([selectedProvider, spaceKey, includeRootPrefix, metadataFields], () => {
  if (error.value) error.value = ''
})
</script>
