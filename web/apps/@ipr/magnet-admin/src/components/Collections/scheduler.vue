<template>
  <div>
    <div v-show="!loading">
      <km-section :title="m.collections_scheduledJobInfo()" :sub-title="m.collections_scheduledJobSubtitle()">
        <template v-if="!jobId">
          <div class="cluster" data-justify="center">
            <div>
              <div class="km-heading-3">{{ m.collections_noJobScheduled() }}</div>
            </div>
          </div>
          <div class="cluster" data-justify="center">
            <div>
              <div class="km-label mb-sm">{{ m.collections_createJobDescription() }}</div>
            </div>
          </div>
          <div class="cluster" data-justify="center">
            <div>
              <km-btn :label="m.common_createNewJob()" @click="showNewDialog = true" />
            </div>
          </div>
        </template>
        <template v-else-if="jobId &amp;&amp; !job">
          <div class="cluster" data-justify="center">
            <div>
              <km-loader size="24px" />
            </div>
          </div>
          <div class="cluster mt-sm" data-justify="center">
            <div>
              <div class="km-label">{{ m.collections_loadingJobInfo() }}</div>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="pt-sm">
            <div class="km-input-label pb-xs pl-sm">{{ m.collections_scheduledJob() }}</div>
            <km-select :disabled="true" :model-value="jobName" />
          </div>
          <div class="cluster mt-sm">
            <div class="flex-none">
              <km-btn flat simple :label="m.collections_openJob()" icon-size="16px" icon="chat" @click="openJob" />
            </div>
          </div>
        </template>
      </km-section>
      <km-separator class="my-lg" />
      <template v-if="job">
        <km-section :title="m.collections_scheduleSettingsStatus()" :sub-title="m.collections_scheduleSettingsSubtitle()">
          <div class="collections-scheduler__stats-grid">
            <div>
              <div class="km-field">{{ m.common_status() }}</div>
              <div class="km-label">{{ jobStatus }}</div>
            </div>
            <div>
              <div class="km-field">{{ m.collections_jobInterval() }}</div>
              <div class="km-label">{{ jobInterval }}</div>
            </div>
            <div>
              <div class="km-field">{{ m.collections_startOn() }}</div>
              <div class="km-label">{{ startDate }}</div>
            </div>
          </div>
          <div class="collections-scheduler__stats-grid mt-md">
            <div>
              <div class="km-field">{{ m.collections_repeatAt() }}</div>
              <div class="km-label">{{ repeatAt }}</div>
            </div>
            <div>
              <div class="km-field">{{ m.common_lastRun() }}</div>
              <div class="km-label">{{ formattedLastRun }}</div>
            </div>
            <div>
              <div class="km-field">{{ m.common_nextRun() }}</div>
              <div class="km-label">{{ formattedNextRun }}</div>
            </div>
          </div>
        </km-section>
      </template>
      <div class="my-lg" />
      <div class="cluster" data-justify="between">
        <div class="flex-none">
          <div class="km-heading-4 mb-sm">{{ m.collections_lastSyncRuns() }}</div>
        </div>
        <div class="km-space" />
        <div class="flex-none">
          <km-btn class="mr-md" icon="refresh" :label="m.common_refreshList()" interaction-tone="brand" label-class="km-title" flat icon-size="16px" @click="refetchTraces" />
        </div>
      </div>
      <km-data-table :table="table" :loading="isLoadingTraces" :fetching="isFetchingTraces" row-key="id" dense style="min-inline-size: 500px" @row-click="openDetails" />
    </div>
  </div>
  <km-inner-loading :showing="loading" />
  <jobs-create-new :show-new-dialog="showNewDialog" :form-default="formDefault" @cancel="showNewDialog = false" @finish="finish" />
</template>

<script setup>
import { ref, nextTick, computed, markRaw, onMounted } from 'vue'
import { m } from '@/paraglide/messages'
import { useRoute, useRouter } from 'vue-router'
import { notify } from '@ds/composables/useNotify'
import { DateTime } from 'luxon'
import { formatDateTime } from '@shared/utils/dateTime'
import { formatDuration } from '@shared/utils'
import { useEntityQueries } from '@/queries/entities'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useDataTable } from '@/composables/useDataTable'
import { textColumn, dateColumn, componentColumn } from '@/utils/columnHelpers'
import { StatusField } from '@/config/observability/traces/components'
import { jobRunTypeOptions } from '@/config/jobs/jobs'

const route = useRoute()
const router = useRouter()
const queries = useEntityQueries()
const { draft, updateField, buildPayload } = useEntityDetail('collections')
const { mutateAsync: updateCollection } = queries.collections.useUpdate()
const { mutateAsync: createCollection } = queries.collections.useCreate()

const jobId = computed(() => draft.value?.job_id)
const { data: jobDetailData, refetch: refetchJobDetail } = queries.jobs.useDetail(jobId)

const systemName = computed(() => draft.value?.system_name)
const extraParams = computed(() => ({
  system_name_in: systemName.value,
}))

const columns = [
  componentColumn('status', m.common_status(), markRaw(StatusField), {
    accessorKey: 'status',
    sortable: true,
    align: 'center',
  }),
  dateColumn('start_time', m.common_startTime()),
  textColumn('latency', m.common_latency(), {
    format: (val) => (val ? formatDuration(val) : '-'),
  }),
  {
    id: 'type',
    accessorFn: (row) => jobRunTypeOptions?.find((el) => el.value === row?.extra_data?.job_definition?.job_type)?.label || '-',
    header: m.common_type(),
    enableSorting: true,
    meta: { align: 'left' },
  },
]

const { table, isLoading: isLoadingTraces, isFetching: isFetchingTraces, refetch: refetchTraces } = useDataTable(
  'observability_traces',
  columns,
  {
    defaultPageSize: 20,
    defaultSort: [{ id: 'start_time', desc: true }],
    manualPagination: true,
    manualSorting: true,
    manualFiltering: true,
    extraParams,
  }
)

const loading = ref(false)
const showNewDialog = ref(false)

const formDefault = computed(() => ({
  name: m.collections_jobForKnowledgeSource(),
  jobType: 'sync_collection',
  executionType: 'recurring',
  system_name: draft.value?.system_name || '',
}))

const currentRow = computed(() => draft.value)
const jobName = computed(() => job.value?.definition.name || jobId.value || m.common_notAvailable())
const job = computed(() => jobDetailData.value ?? null)
const jobStatus = computed(() => job.value?.status || m.common_notAvailable())

const customCronDisplay = computed(() => {
  const cron = job.value?.definition?.cron
  if (!cron) return m.jobs_custom()
  const parts = [
    cron.minute || '*',
    cron.hour || '*',
    cron.day || cron.day_of_month || '*',
    cron.month || '*',
    cron.day_of_week || '*',
  ]
  return `Custom (${parts.join(' ')})`
})

const jobInterval = computed(() => {
  const interval = job.value?.definition?.interval
  if (!interval) return m.common_notAvailable()
  const intervalLabels = {
    'every_5_minutes': m.jobs_every5Min(),
    'hourly': m.jobs_hourly(),
    'daily': m.jobs_daily(),
    'weekly': m.jobs_weekly(),
    'monthly': m.jobs_monthly(),
    'custom': customCronDisplay.value,
  }
  return intervalLabels[interval] || interval
})

const startDate = computed(() => {
  if (!job.value?.definition?.scheduled_start_time) return m.common_notAvailable()
  const startTime = job.value.definition.scheduled_start_time
  const jobTimezone = job.value?.definition?.timezone || 'UTC'
  let dateObj = DateTime.fromISO(startTime)
  if (!dateObj.isValid) return m.common_notAvailable()
  if (!startTime.includes('+') && !startTime.includes('Z') && !startTime.includes('-', 10)) {
    dateObj = DateTime.fromISO(startTime, { zone: jobTimezone })
  }
  const localDate = dateObj.toLocal()
  return `${localDate.toLocaleString(DateTime.DATE_SHORT)} ${localDate.toLocaleString(DateTime.TIME_SIMPLE)}`
})

const repeatAt = computed(() => {
  const cron = job.value?.definition?.cron
  if (!cron) return m.common_notAvailable()
  return cronToHumanReadable(cron)
})

const formattedLastRun = computed(() => {
  if (!job.value?.last_run) return m.collections_notRunYet()
  return formatDateTime(job.value.last_run)
})

const formattedNextRun = computed(() => {
  if (!job.value?.next_run) return m.collections_notScheduled()
  return formatDateTime(job.value.next_run)
})

onMounted(async () => {
  loading.value = true
  try {
    await nextTick()
  } catch (error) {
  } finally {
    loading.value = false
  }
})

async function save() {
  loading.value = true
  try {
    if (currentRow.value?.created) {
      const obj = { ...currentRow.value }
      delete obj._metadata
      delete obj.id
      await updateCollection({ id: currentRow.value.id, data: obj })
    } else {
      await createCollection(currentRow.value)
    }
  } catch (error) {
    notify.error(m.collections_failedToSaveSchedule())
  } finally {
    loading.value = false
  }
}

function setJobId(id) {
  updateField('job_id', id)
}

function cronToHumanReadable(cron) {
  if (!cron) return m.common_notAvailable()
  const { minute, hour, day, day_of_month, month, day_of_week } = cron
  const dayField = day || day_of_month
  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

  const formatTime = (h, m) => {
    const parsedHour = parseInt(h)
    const parsedMinute = parseInt(m)
    if (isNaN(parsedHour) || isNaN(parsedMinute)) return null
    const jobTimezone = job.value?.definition?.timezone || 'UTC'
    const jobTime = DateTime.now()
      .setZone(jobTimezone)
      .set({ hour: parsedHour, minute: parsedMinute })
    const localTime = jobTime.toLocal()
    return `${localTime.toFormat('HH:mm')} (${localTime.toFormat('ZZZZ')})`
  }

  if (minute && minute.startsWith('*/')) {
    const stepValue = parseInt(minute.substring(2))
    if (!isNaN(stepValue)) {
      if (stepValue === 1) return m.collections_everyMinute()
      return m.collections_everyNMinutes({ count: stepValue })
    }
  }
  if (minute && !minute.includes('*') && (hour === '*' || !hour)) {
    const parsedMinute = parseInt(minute)
    if (!isNaN(parsedMinute)) {
      const minStr = String(parsedMinute).padStart(2, '0')
      return m.collections_everyHourAt({ minute: minStr })
    }
  }
  if (hour && hour.startsWith('*/')) {
    const stepValue = parseInt(hour.substring(2))
    if (!isNaN(stepValue)) {
      const minStr = minute && minute !== '*' ? String(parseInt(minute)).padStart(2, '0') : '00'
      return m.collections_everyNHoursAt({ count: stepValue, minute: minStr })
    }
  }
  if (minute && hour && !minute.includes('*') && !hour.includes('*') &&
      (dayField === '*' || !dayField) && (day_of_week === '*' || !day_of_week)) {
    const timeStr = formatTime(hour, minute)
    if (timeStr) return m.collections_dailyAt({ time: timeStr })
  }
  if (minute && hour && day_of_week && day_of_week !== '*' && !minute.includes('*') && !hour.includes('*')) {
    const timeStr = formatTime(hour, minute)
    const dayNum = parseInt(day_of_week)
    const dayName = !isNaN(dayNum) && dayNum >= 0 && dayNum <= 6 ? dayNames[dayNum] : day_of_week
    if (timeStr) return m.collections_everyDayAt({ day: dayName, time: timeStr })
  }
  if (minute && hour && dayField && dayField !== '*' && !minute.includes('*') && !hour.includes('*')) {
    const timeStr = formatTime(hour, minute)
    const dayNum = parseInt(dayField)
    if (timeStr && !isNaN(dayNum)) {
      const suffix = dayNum === 1 ? 'st' : dayNum === 2 ? 'nd' : dayNum === 3 ? 'rd' : 'th'
      return m.collections_monthlyOnAt({ day: `${dayNum}${suffix}`, time: timeStr })
    }
  }
  const parts = [minute || '*', hour || '*', dayField || '*', month || '*', day_of_week || '*']
  return parts.join(' ')
}
async function finish(jobResult) {
  try {
    setJobId(jobResult.job_id)
    await save()
    showNewDialog.value = false
    await refetchJobDetail()
    refetchTraces()
  } catch (error) {
  }
}
function navigate(path = '') {
  if (route?.path !== `/${path}`) {
    router?.push(`/${path}`)
  }
}
async function openDetails(row) {
  router.push(`/observability-traces/${row.id}`)
}
function openJob() {
  if (!jobId.value) return
  router.push({
    name: 'Jobs',
    query: { job_id: jobId.value },
  })
}
function createJob() {
  router.push({
    name: 'Jobs',
    query: {
      create: true,
      knowledge_source_id: draft.value?.id,
    },
  })
}
</script>

<style scoped>
.empty-state {
  min-block-size: 300px;
  padding: var(--ds-space-3xl);
}

.collections-scheduler__stats-grid {
  display: grid;
  gap: var(--ds-space-md);
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

@media (max-width: 768px) {
  .collections-scheduler__stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
