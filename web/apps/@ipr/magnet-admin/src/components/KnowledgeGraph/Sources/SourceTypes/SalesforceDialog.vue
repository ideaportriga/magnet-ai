<template>
  <kg-dialog-source-base
    :show-dialog="dialogOpen"
    :source="props.source || null"
    :title="isEditMode ? m.knowledgeGraph_sf_editTitle() : m.knowledgeGraph_sf_connectTitle()"
    :confirm-label="isEditMode ? m.knowledgeGraph_saveChanges() : m.common_connect()"
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
      :title="m.knowledgeGraph_sf_sectionProviderTitle()"
      :description="m.knowledgeGraph_sf_sectionProviderDesc()"
      icon="key"
    >
      <q-select
        v-model="selectedProvider"
        :options="providerOptions"
        option-label="name"
        option-value="id"
        emit-value
        map-options
        :placeholder="m.knowledgeGraph_sf_providerPlaceholder()"
        outlined
        dense
        :loading="loadingProviders"
        :no-options-label="loadingProviders ? m.knowledgeGraph_sf_loadingProviders() : m.knowledgeGraph_sf_noProvidersFound()"
        @update:model-value="clearError"
      />
      <div v-if="!loadingProviders && providerOptions.length === 0" class="text-caption text-negative q-mt-xs">
        {{ m.knowledgeGraph_sf_noProvidersFoundMsg() }}
      </div>
    </kg-dialog-section>

    <kg-dialog-section
      :title="m.knowledgeGraph_sf_sectionObjectApiNameTitle()"
      :description="m.knowledgeGraph_sf_sectionObjectApiNameDesc()"
      icon="data_object"
    >
      <km-input
        v-model="objectApiName"
        height="36px"
        :placeholder="m.knowledgeGraph_sf_objectApiNamePlaceholder()"
        @update:model-value="clearError"
      />
    </kg-dialog-section>

    <kg-dialog-section
      :title="m.knowledgeGraph_sf_sectionArticleIdFieldTitle()"
      :description="m.knowledgeGraph_sf_sectionArticleIdFieldDesc()"
      icon="fingerprint"
    >
      <km-input
        v-model="articleIdField"
        height="36px"
        :placeholder="m.knowledgeGraph_sf_articleIdFieldPlaceholder()"
        @update:model-value="clearError"
      />
    </kg-dialog-section>

    <kg-dialog-section
      :title="m.knowledgeGraph_sf_sectionTitleFieldTitle()"
      :description="m.knowledgeGraph_sf_sectionTitleFieldDesc()"
      icon="title"
    >
      <km-input
        v-model="titleField"
        height="36px"
        :placeholder="m.knowledgeGraph_sf_titleFieldPlaceholder()"
        @update:model-value="clearError"
      />
    </kg-dialog-section>

    <kg-dialog-section
      :title="m.knowledgeGraph_sf_sectionMetadataTitle()"
      :description="m.knowledgeGraph_sf_sectionMetadataDesc()"
      icon="label"
    >
      <km-input
        v-model="metadataFields"
        height="36px"
        :placeholder="m.knowledgeGraph_sf_metadataPlaceholder()"
        @update:model-value="clearError"
      />
    </kg-dialog-section>

    <kg-dialog-section
      :title="m.knowledgeGraph_sf_sectionOutputConfigTitle()"
      :description="m.knowledgeGraph_sf_sectionOutputConfigDesc()"
      icon="article"
    >
      <q-input
        v-model="outputConfig"
        outlined
        dense
        autogrow
        type="textarea"
        :placeholder="m.knowledgeGraph_sf_outputConfigPlaceholder()"
        :input-style="{ 'min-height': '80px', 'font-family': 'var(--km-font-mono)' }"
        @update:model-value="clearError"
      />
    </kg-dialog-section>

    <kg-dialog-section
      :title="m.knowledgeGraph_sf_sectionExternalUrlTitle()"
      :description="m.knowledgeGraph_sf_sectionExternalUrlDesc()"
      icon="link"
    >
      <km-input
        v-model="externalUrlTemplate"
        height="36px"
        :placeholder="m.knowledgeGraph_sf_externalUrlPlaceholder()"
        @update:model-value="clearError"
      />
      <div class="text-caption text-grey-7 q-mt-xs">
        {{ m.knowledgeGraph_sf_externalUrlExample() }}
      </div>
    </kg-dialog-section>
  </kg-dialog-source-base>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { m } from '@/paraglide/messages'
import { computed, onMounted, ref, watch } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useNotify } from '@/composables/useNotify'
import { useEntityQueries } from '@/queries/entities'
import { KgDialogSection, KgDialogSourceBase, ScheduleFormState } from '../../common'
import type { SourceRow } from '../models'

type SalesforceSourceConfig = {
  ks_provider_id?: string
  object_api_name?: string
  output_config?: string
  article_id_field?: string
  title_field?: string
  metadata_fields?: string
  external_url_template?: string
}

type SalesforceSourceRecord = Omit<SourceRow, 'type' | 'config'> & {
  type: 'salesforce'
  config?: SalesforceSourceConfig | null
}

type ProviderOption = {
  id: string
  name: string
}

const DEFAULT_OBJECT_API_NAME = 'Knowledge__kav'
const DEFAULT_ARTICLE_ID_FIELD = 'ArticleNumber'
const DEFAULT_TITLE_FIELD = 'Title'
const DEFAULT_METADATA_FIELDS = 'Title, CreatedDate, LastModifiedDate'
const DEFAULT_OUTPUT_CONFIG = '{Summary}'

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

const appStore = useAppStore()
const { notifyError } = useNotify()
const queries = useEntityQueries()
const { data: providerListData } = queries.provider.useList()
const error = ref('')
const loading = ref(false)
const loadingProviders = ref(false)

const providerOptions = ref<ProviderOption[]>([])
const selectedProvider = ref<string>('')
const objectApiName = ref(DEFAULT_OBJECT_API_NAME)
const articleIdField = ref(DEFAULT_ARTICLE_ID_FIELD)
const titleField = ref(DEFAULT_TITLE_FIELD)
const metadataFields = ref(DEFAULT_METADATA_FIELDS)
const outputConfig = ref(DEFAULT_OUTPUT_CONFIG)
const externalUrlTemplate = ref('')

const isEditMode = computed(() => !!props.source)

const dialogOpen = computed(() => props.showDialog)

const isFormValid = computed(
  () => !!selectedProvider.value && !!outputConfig.value.trim()
)

// ------------------------------------------------------------------
// Provider loading
// ------------------------------------------------------------------

const loadProviders = async () => {
  loadingProviders.value = true
  try {
    const items: any[] = providerListData.value?.items || []
    providerOptions.value = items
      .filter((p: any) => p.category === 'knowledge' && p.type?.toLowerCase() === 'salesforce')
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
        objectApiName.value = props.source.config?.object_api_name || DEFAULT_OBJECT_API_NAME
        articleIdField.value = props.source.config?.article_id_field || DEFAULT_ARTICLE_ID_FIELD
        titleField.value = props.source.config?.title_field || DEFAULT_TITLE_FIELD
        metadataFields.value = props.source.config?.metadata_fields || DEFAULT_METADATA_FIELDS
        outputConfig.value = props.source.config?.output_config || DEFAULT_OUTPUT_CONFIG
        externalUrlTemplate.value = props.source.config?.external_url_template || ''
      } else {
        selectedProvider.value = ''
        objectApiName.value = DEFAULT_OBJECT_API_NAME
        articleIdField.value = DEFAULT_ARTICLE_ID_FIELD
        titleField.value = DEFAULT_TITLE_FIELD
        metadataFields.value = DEFAULT_METADATA_FIELDS
        outputConfig.value = DEFAULT_OUTPUT_CONFIG
        externalUrlTemplate.value = ''
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

  let msg = m.knowledgeGraph_failedToUpdateSyncSchedule()
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

const addSource = async (sourceName: string, schedule: ScheduleFormState) => {
  loading.value = true
  error.value = ''

  try {
    const endpoint = appStore.config.api.aiBridge.urlAdmin
    const payload = {
      type: 'salesforce',
      name: sourceName.trim() || null,
      config: {
        ks_provider_id: selectedProvider.value,
        object_api_name: objectApiName.value.trim() || DEFAULT_OBJECT_API_NAME,
        article_id_field: articleIdField.value.trim() || DEFAULT_ARTICLE_ID_FIELD,
        title_field: titleField.value.trim() || DEFAULT_TITLE_FIELD,
        metadata_fields: metadataFields.value.trim() || DEFAULT_METADATA_FIELDS,
        output_config: outputConfig.value.trim(),
        external_url_template: externalUrlTemplate.value.trim() || undefined,
      },
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
          notifyError(e?.message || m.knowledgeGraph_sourceCreatedScheduleFailed())
        }
      }
      emit('created', result)
    } else {
      const errorData = await response.json()
      error.value = errorData.detail || errorData.error || m.knowledgeGraph_sf_failedToConnect()
    }
  } catch (err: any) {

    error.value = err.message || m.knowledgeGraph_sf_failedToConnectRetry()
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
      config: {
        ks_provider_id: selectedProvider.value,
        object_api_name: objectApiName.value.trim() || DEFAULT_OBJECT_API_NAME,
        article_id_field: articleIdField.value.trim() || DEFAULT_ARTICLE_ID_FIELD,
        title_field: titleField.value.trim() || DEFAULT_TITLE_FIELD,
        metadata_fields: metadataFields.value.trim() || DEFAULT_METADATA_FIELDS,
        output_config: outputConfig.value.trim(),
        external_url_template: externalUrlTemplate.value.trim() || undefined,
      },
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
      error.value = errorData.detail || errorData.error || m.knowledgeGraph_sf_failedToSave()
    }
  } catch (err: any) {

    error.value = err.message || m.knowledgeGraph_sf_failedToSaveRetry()
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

watch([selectedProvider, outputConfig, objectApiName, articleIdField, titleField, metadataFields, externalUrlTemplate], () => {
  if (error.value) error.value = ''
})
</script>
