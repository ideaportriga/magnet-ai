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
  </kg-dialog-source-base>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { useQuasar } from 'quasar'
import { computed, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { KgDialogSection, KgDialogSourceBase, KgFieldRow, KgToggleField, ScheduleFormState } from '../../common'
import type { SourceRow } from '../models'

type SharePointSourceConfig = {
  site_url?: string
  library?: string | null
  folder_path?: string | null
  recursive?: boolean
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
        } catch {
          // ignore prefill errors
        }
      } else {
        // opening in create mode - ensure clean form
        siteUrl.value = ''
        library.value = ''
        folderPath.value = ''
        includeSubfolders.value = false
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
watch([siteUrl, library, folderPath, includeSubfolders], () => {
  if (error.value) error.value = ''
})
</script>
