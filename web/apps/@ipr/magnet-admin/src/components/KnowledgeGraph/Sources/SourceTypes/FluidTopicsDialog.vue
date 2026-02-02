<template>
  <kg-dialog-source-base
    :show-dialog="dialogOpen"
    :source="props.source || null"
    :title="isEditMode ? 'Edit Fluid Topics Connection' : 'Connect to Fluid Topics'"
    :confirm-label="isEditMode ? 'Save Changes' : 'Connect'"
    :loading="loading"
    :disable-confirm="loading"
    :error="error"
    size="md"
    syncable
    @update:show-dialog="(v: boolean) => emit('update:showDialog', v)"
    @cancel="emit('cancel')"
    @confirm="onConfirm"
    @changed="clearError"
  >
    <kg-dialog-section
      title="Content Filtering"
      description="Define filtering criteria using JSON to control which content is imported from Fluid Topics."
      icon="filter_list"
      focus-highlight
    >
      <km-codemirror v-model="jsonFilter" language="json" :options="{ mode: 'application/json' }" style="min-height: 200px" />
    </kg-dialog-section>
  </kg-dialog-source-base>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { useQuasar } from 'quasar'
import { computed, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { KgDialogSection, KgDialogSourceBase, ScheduleFormState } from '../../common'
import type { SourceRow } from '../models'

type FluidTopicsSourceRecord = Omit<SourceRow, 'type'> & {
  type: 'fluid_topics'
}

const props = defineProps<{
  showDialog: boolean
  graphId: string
  source?: FluidTopicsSourceRecord | null
}>()

const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'created', result: any): void
  (e: 'update:showDialog', value: boolean): void
}>()

const store = useStore()
const $q = useQuasar()
const error = ref('')
const loading = ref(false)
const jsonFilter = ref('[\n\n]')

const isEditMode = computed(() => !!props.source)

const dialogOpen = computed(() => props.showDialog)

// Prefill or reset when dialog opens
watch(
  () => [props.showDialog, props.source] as const,
  () => {
    if (props.showDialog) {
      if (props.source) {
        try {
          jsonFilter.value = JSON.stringify(props.source?.config?.filters || [], null, 2)
        } catch {
          // ignore prefill errors
        }
      } else {
        // opening in create mode - ensure clean form
        jsonFilter.value = '[\n\n]'
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
  loading.value = true
  error.value = ''

  try {
    let parsedConfig
    try {
      parsedConfig = JSON.parse(jsonFilter.value)
    } catch (e) {
      throw new Error('Invalid JSON format')
    }

    const endpoint = store.getters.config.api.aiBridge.urlAdmin

    const payload = {
      type: 'fluid_topics',
      name: sourceName.trim() || null,
      config: { filters: parsedConfig },
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
      error.value = errorData.detail || errorData.error || 'Failed to connect to Fluid Topics'
    }
  } catch (err: any) {
    console.error('Fluid Topics connection error:', err)
    error.value = err.message || 'Failed to connect to Fluid Topics. Please try again.'
  } finally {
    loading.value = false
  }
}

const updateSource = async (sourceName: string, schedule: ScheduleFormState) => {
  if (!props.source) return
  loading.value = true
  error.value = ''

  try {
    let parsedFilter: object
    try {
      parsedFilter = JSON.parse(jsonFilter.value)
    } catch (e) {
      throw new Error('Invalid JSON format')
    }

    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const payload = {
      name: sourceName.trim() || null,
      config: { filters: parsedFilter },
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
      error.value = errorData.detail || errorData.error || 'Failed to save Fluid Topics source'
    }
  } catch (err: any) {
    console.error('Fluid Topics update error:', err)
    error.value = err.message || 'Failed to save Fluid Topics source. Please try again.'
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
watch([jsonFilter], () => {
  if (error.value) error.value = ''
})
</script>

<style scoped>
:deep(.ͼ1.cm-focused) {
  background: white !important;
  border: 1px solid var(--q-primary) !important;
  outline: none !important;
}
:deep(.cm-editor) {
  background: white !important;
}
:deep(.cm-line) {
  background: transparent !important;
}
:deep(.cm-activeLine) {
  background: rgba(var(--q-primary-rgb, 25, 118, 210), 0.08) !important;
}
</style>
