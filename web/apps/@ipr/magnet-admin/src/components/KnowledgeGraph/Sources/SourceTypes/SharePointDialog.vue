<template>
  <kg-dialog-source-base
    :show-dialog="dialogOpen"
    :source="props.source || null"
    :title="isEditMode ? 'Edit SharePoint Connection' : 'Connect to SharePoint'"
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
    <kg-dialog-section title="Connection" description="Enter the SharePoint site URL to connect. Use the full site URL." icon="link">
      <km-input
        ref="siteUrlRef"
        v-model="siteUrl"
        height="36px"
        placeholder="https://your-domain.sharepoint.com/sites/your-site"
        :rules="siteUrlRules"
        required
      />
    </kg-dialog-section>

    <kg-dialog-section title="Scope" description="Optionally configure which content to sync from SharePoint." icon="folder">
      <kg-field-row :cols="2">
        <div>
          <div class="km-input-label q-pb-xs">Library</div>
          <km-input v-model="library" height="36px" placeholder="Documents" />
        </div>
        <div>
          <div class="km-input-label q-pb-xs">Folder Path</div>
          <km-input v-model="folderPath" height="36px" placeholder="Shared Documents/MyFolder" />
        </div>
      </kg-field-row>

      <kg-toggle-field
        v-model="includeSubfolders"
        title="Include Subfolders"
        description="Sync all nested folders under the selected path"
        class="q-mt-lg"
      />
    </kg-dialog-section>

    <kg-dialog-section
      title="Metadata"
      description="Add custom metadata that will be applied to all documents from this source. Press Enter to add multiple values."
      icon="label"
    >
      <div class="metadata-entries">
        <div v-for="(entry, index) in metadataEntries" :key="index" class="metadata-entry">
          <div class="metadata-entry__key">
            <div class="km-input-label q-pb-xs">Key</div>
            <km-input :model-value="entry.key" height="36px" placeholder="Metadata key" @update:model-value="updateMetadataKey(index, $event)" />
          </div>
          <div class="metadata-entry__values">
            <div class="km-input-label q-pb-xs">Values</div>
            <q-select
              :model-value="entry.values"
              use-input
              use-chips
              multiple
              hide-dropdown-icon
              input-debounce="0"
              new-value-mode="add-unique"
              placeholder="Type and press Enter"
              dense
              outlined
              class="metadata-values-select"
              @update:model-value="updateMetadataValues(index, $event)"
            >
              <template #selected-item="scope">
                <q-chip removable dense color="primary" text-color="white" class="q-my-xs" @remove="removeMetadataValue(index, scope.index)">
                  {{ scope.opt }}
                </q-chip>
              </template>
            </q-select>
          </div>
          <div class="metadata-entry__actions">
            <q-btn flat round dense color="negative" icon="close" size="sm" @click="removeMetadataEntry(index)" />
          </div>
        </div>
      </div>
      <q-btn flat no-caps dense color="primary" icon="add" label="Add Metadata" class="q-mt-md" @click="addMetadataEntry" />
    </kg-dialog-section>
  </kg-dialog-source-base>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { useQuasar } from 'quasar'
import { computed, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { KgDialogSection, KgDialogSourceBase, KgFieldRow, KgToggleField, ScheduleFormState } from '../../common'
import type { SourceRow } from '../models'

type MetadataValue = string | string[]

type SharePointSourceConfig = {
  site_url?: string
  library?: string | null
  folder_path?: string | null
  recursive?: boolean
  metadata?: Record<string, MetadataValue> | null
}

type MetadataEntry = {
  key: string
  values: string[]
}

type SharePointSourceRecord = Omit<SourceRow, 'type' | 'config'> & {
  type: 'sharepoint'
  config?: SharePointSourceConfig | null
}

const props = defineProps<{
  showDialog: boolean
  graphId: string
  source?: SharePointSourceRecord | null
}>()

const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'created', result: any): void
  (e: 'update:showDialog', value: boolean): void
}>()

const store = useStore()
const $q = useQuasar()
const siteUrl = ref('')
const folderPath = ref('')
const library = ref('')
const includeSubfolders = ref<boolean>(false)
const metadataEntries = ref<MetadataEntry[]>([])
const loading = ref(false)
const error = ref('')
const showValidation = ref(false)

// Refs for field-level validation
const siteUrlRef = ref<any>(null)

const siteUrlRules = [
  (val: string) => !!(val && val.trim()) || 'Site URL is required',
  (val: string) => /^https?:\/\//.test(val || '') || 'Must start with http(s)://',
]

const isFormValid = computed(() => !!siteUrl.value.trim())

const isEditMode = computed(() => !!props.source)

const dialogOpen = computed(() => props.showDialog)

// Helper to convert metadata object to array of entries
function metadataToEntries(metadata: Record<string, MetadataValue> | null | undefined): MetadataEntry[] {
  if (!metadata) return []
  return Object.entries(metadata).map(([key, value]) => ({
    key,
    values: Array.isArray(value) ? value : [value],
  }))
}

// Helper to convert entries array back to metadata object
function entriesToMetadata(entries: MetadataEntry[]): Record<string, MetadataValue> | null {
  const validEntries = entries.filter((e) => e.key.trim() && e.values.length > 0)
  if (validEntries.length === 0) return null
  return Object.fromEntries(validEntries.map((e) => [e.key.trim(), e.values.length === 1 ? e.values[0] : e.values]))
}

// Metadata management functions
function addMetadataEntry() {
  metadataEntries.value.push({ key: '', values: [] })
}

function updateMetadataKey(index: number, newKey: string) {
  if (index >= 0 && index < metadataEntries.value.length) {
    metadataEntries.value[index].key = newKey
  }
}

function updateMetadataValues(index: number, newValues: string[]) {
  if (index >= 0 && index < metadataEntries.value.length) {
    metadataEntries.value[index].values = newValues
  }
}

function removeMetadataValue(entryIndex: number, valueIndex: number) {
  if (entryIndex >= 0 && entryIndex < metadataEntries.value.length) {
    metadataEntries.value[entryIndex].values.splice(valueIndex, 1)
  }
}

function removeMetadataEntry(index: number) {
  if (index >= 0 && index < metadataEntries.value.length) {
    metadataEntries.value.splice(index, 1)
  }
}

// Prefill or reset when dialog opens
watch(
  () => [props.showDialog, props.source] as const,
  () => {
    if (props.showDialog) {
      if (props.source) {
        try {
          const cfg = (props.source?.config || {}) as SharePointSourceConfig
          siteUrl.value = cfg.site_url || ''
          library.value = cfg.library || ''
          folderPath.value = cfg.folder_path || ''
          includeSubfolders.value = !!cfg.recursive
          metadataEntries.value = metadataToEntries(cfg.metadata)
        } catch {
          // ignore prefill errors
        }
      } else {
        // opening in create mode - ensure clean form
        siteUrl.value = ''
        library.value = ''
        folderPath.value = ''
        includeSubfolders.value = false
        metadataEntries.value = []
      }
    }
  },
  { immediate: true }
)

function buildCron(schedule: ScheduleFormState) {
  if (schedule.interval === 'none') return null
  if (schedule.interval === 'hourly') return { minute: 0, hour: '*' }
  if (schedule.interval === 'daily') return { minute: 0, hour: schedule.hour }
  return { minute: 0, hour: schedule.hour, day_of_week: schedule.day }
}

async function applySchedule(sourceId: string, schedule: ScheduleFormState) {
  // Skip unnecessary round-trips: on create, default is None; on edit, only call if schedule exists or user enabled.
  const shouldCall = schedule.interval !== 'none' || (props.source?.schedule !== null && props.source?.schedule !== undefined)
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

const clearError = () => {
  if (error.value) error.value = ''
}

const addSource = async (sourceName: string, schedule: ScheduleFormState) => {
  showValidation.value = true
  const siteOk = await (siteUrlRef.value?.validate?.() ?? true)
  if (!siteOk) return

  loading.value = true
  error.value = ''

  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin

    const payload = {
      type: 'sharepoint',
      name: sourceName.trim() || null,
      config: {
        site_url: siteUrl.value.trim(),
        library: library.value.trim() || null,
        folder_path: folderPath.value.trim() || null,
        recursive: !!includeSubfolders.value,
        metadata: entriesToMetadata(metadataEntries.value),
      },
    }

    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/sources`,
      method: 'POST',
      credentials: 'include',
      body: JSON.stringify(payload),
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (response.ok) {
      const result = await response.json()
      // Apply schedule only after we have a source id.
      if (schedule.interval !== 'none') {
        try {
          await applySchedule(result.id, schedule)
        } catch (e: any) {
          // Avoid keeping the dialog in "create" mode after the source has been created.
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
      error.value = errorData.detail || errorData.error || 'Failed to connect to SharePoint'
    }
  } catch (err) {
    console.error('SharePoint connection error:', err)
    error.value = 'Failed to connect to SharePoint. Please try again.'
  } finally {
    loading.value = false
  }
}

const updateSource = async (sourceName: string, schedule: ScheduleFormState) => {
  if (!props.source) return
  const siteOk = await (siteUrlRef.value?.validate?.() ?? true)
  if (!siteOk) return
  loading.value = true
  error.value = ''
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const payload = {
      name: sourceName.trim() || null,
      config: {
        site_url: siteUrl.value.trim(),
        library: library.value.trim() || null,
        folder_path: folderPath.value.trim() || null,
        recursive: !!includeSubfolders.value,
        metadata: entriesToMetadata(metadataEntries.value),
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
      // For edits, treat schedule save as part of the operation: keep dialog open on failure.
      await applySchedule(props.source.id, schedule)
      emit('created', result)
    } else {
      const errorData = await response.json()
      error.value = errorData.detail || errorData.error || 'Failed to save SharePoint source'
    }
  } catch (err) {
    console.error('SharePoint update error:', err)
    error.value = 'Failed to save SharePoint source. Please try again.'
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

// Clear error message when user edits inputs
watch(
  [siteUrl, library, folderPath, includeSubfolders, metadataEntries],
  () => {
    if (error.value) error.value = ''
  },
  { deep: true }
)
</script>

<style scoped>
.metadata-entries {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metadata-entry {
  display: grid;
  grid-template-columns: 180px 1fr auto;
  gap: 12px;
  align-items: end;
}

.metadata-entry__actions {
  padding-bottom: 6px;
}

.metadata-values-select {
  min-height: 36px;
}

.metadata-values-select :deep(.q-field__control) {
  min-height: 36px;
  padding: 4px 8px;
}

.metadata-values-select :deep(.q-field__native) {
  min-height: 24px;
  padding: 0;
}

.metadata-values-select :deep(.q-chip) {
  margin: 2px;
}
</style>
