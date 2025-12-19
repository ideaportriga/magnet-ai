<template>
  <kg-dialog-base
    :model-value="showDialog"
    :title="title"
    :confirm-label="confirmLabel"
    :loading="loading"
    :disable-confirm="disableConfirm || (syncable && !isScheduleValid)"
    :error="error"
    :size="size"
    @update:model-value="onModelUpdate"
    @cancel="$emit('cancel')"
    @confirm="onConfirm"
  >
    <kg-dialog-section title="Source Name" description="Give this source a friendly name." icon="edit">
      <km-input v-model="localSourceName" height="36px" placeholder="E.g., Engineering Docs" />
    </kg-dialog-section>

    <slot />

    <kg-dialog-section v-if="syncable" title="Schedule" description="Pick how often to sync and at what time." icon="event" focus-highlight>
      <template #header-actions>
        <q-btn-toggle
          v-model="schedule.interval"
          toggle-color="primary-light"
          :options="intervals"
          dense
          text-color="text-weak"
          toggle-text-color="primary"
        />
      </template>

      <div class="row items-center q-gutter-x-sm q-gutter-y-sm">
        <template v-if="schedule.interval === 'none'">
          <div class="km-description text-secondary-text" style="padding: 9px 0">Automatic syncing is turned off.</div>
        </template>

        <template v-else-if="schedule.interval === 'weekly'">
          <div class="row items-center q-gap-6">
            <div class="km-field text-secondary-text">every</div>
            <km-select v-model="schedule.day" :options="days" emit-value map-options style="min-width: 190px" />
          </div>
        </template>

        <template v-if="schedule.interval !== 'hourly' && schedule.interval !== 'none'">
          <div class="row items-center q-gap-6">
            <div class="km-field text-secondary-text">at</div>
            <km-select v-model="schedule.hour" :options="times" emit-value map-options style="min-width: 160px" />
          </div>
        </template>

        <template v-else-if="schedule.interval === 'hourly'">
          <div class="km-description text-secondary-text" style="padding: 9px 0">Runs at the start of every hour.</div>
        </template>
      </div>
    </kg-dialog-section>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { DialogSize, KgDialogBase, KgDialogSection } from '.'
import type { SourceRow } from '../Sources/models'

type Option<T = string> = { label: string; value: T }

export type ScheduleInterval = 'none' | 'hourly' | 'daily' | 'weekly'

export type ScheduleFormState = {
  interval: ScheduleInterval
  day: number
  hour: number
  timezone: string
}

const props = defineProps<{
  showDialog: boolean
  title: string
  confirmLabel: string
  loading: boolean
  disableConfirm: boolean
  error: string
  size?: DialogSize
  syncable?: boolean
  source?: SourceRow | null
}>()

const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'changed'): void
  (e: 'confirm', payload: { sourceName: string; schedule: ScheduleFormState }): void
  (e: 'update:showDialog', value: boolean): void
}>()

const syncable = computed(() => props.syncable === true)

const detectedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone

const intervals: Option<ScheduleInterval>[] = [
  { label: 'None', value: 'none' },
  { label: 'Hourly', value: 'hourly' },
  { label: 'Daily', value: 'daily' },
  { label: 'Weekly', value: 'weekly' },
]

const days: Option<number>[] = [
  { label: 'Monday', value: 0 },
  { label: 'Tuesday', value: 1 },
  { label: 'Wednesday', value: 2 },
  { label: 'Thursday', value: 3 },
  { label: 'Friday', value: 4 },
  { label: 'Saturday', value: 5 },
  { label: 'Sunday', value: 6 },
]

const times: Option<number>[] = Array.from({ length: 24 }, (_, i) => {
  const hour = String(i).padStart(2, '0')
  return { label: `${hour}:00`, value: i }
})

const localSourceName = ref('')
const schedule = ref<ScheduleFormState>({
  interval: 'none',
  day: 0,
  hour: 3,
  timezone: detectedTimezone,
})

function toInt(value: unknown): number | null {
  if (value === null || value === undefined) return null
  const n = typeof value === 'number' ? value : Number.parseInt(String(value), 10)
  return Number.isFinite(n) ? n : null
}

function normalizeInterval(rawInterval: unknown, cron: Record<string, any> | null | undefined): ScheduleInterval {
  const interval = String(rawInterval || '').toLowerCase()
  if (interval === 'hourly' || interval === 'daily' || interval === 'weekly') return interval

  const cronHour = cron?.hour
  if (cronHour === '*') return 'hourly'

  const dayOfWeek = cron?.day_of_week
  if (dayOfWeek !== undefined && dayOfWeek !== null && String(dayOfWeek) !== '') return 'weekly'

  return 'daily'
}

function normalizeDayOfWeek(value: unknown): number {
  const n = toInt(value)
  if (n !== null && n >= 0 && n <= 6) return n

  const s = String(value || '')
    .toLowerCase()
    .trim()
  const map: Record<string, number> = {
    mon: 0,
    tue: 1,
    wed: 2,
    thu: 3,
    fri: 4,
    sat: 5,
    sun: 6,
  }
  return map[s] ?? 0
}

const isScheduleValid = computed(() => {
  if (!syncable.value) return true
  if (schedule.value.interval === 'none' || schedule.value.interval === 'hourly') return true
  if (schedule.value.hour === null || schedule.value.hour === undefined) return false
  if (schedule.value.hour < 0 || schedule.value.hour > 23) return false
  if (schedule.value.interval === 'weekly' && (schedule.value.day < 0 || schedule.value.day > 6)) return false
  return true
})

const onModelUpdate = (v: boolean) => {
  if (!v) {
    emit('cancel')
  } else {
    emit('update:showDialog', v)
  }
}

function resetFromSource() {
  localSourceName.value = String(props.source?.name || '').trim()

  const existing = props.source?.schedule || null
  const cron = (existing?.cron as any) || null

  schedule.value.timezone = existing?.timezone || detectedTimezone

  if (!existing) {
    schedule.value.interval = 'none'
    schedule.value.day = 0
    schedule.value.hour = 3
    return
  }

  const interval = normalizeInterval(existing.interval, cron)
  schedule.value.interval = interval

  const hour = toInt(cron?.hour)
  if (interval === 'hourly') {
    schedule.value.hour = 3
    schedule.value.day = 0
  } else {
    schedule.value.hour = hour ?? 3
    schedule.value.day = interval === 'weekly' ? normalizeDayOfWeek(cron?.day_of_week) : 0
  }
}

watch(
  () => [props.showDialog, props.source?.id] as const,
  () => {
    if (!props.showDialog) return
    resetFromSource()
  },
  { immediate: true }
)

watch(
  () => [localSourceName.value, schedule.value] as const,
  () => {
    emit('changed')
  },
  { deep: true }
)

function onConfirm() {
  emit('confirm', { sourceName: localSourceName.value, schedule: schedule.value })
}
</script>
