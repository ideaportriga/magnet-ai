<template lang="pug">
div
  div(v-show='!loading')
    km-section(title='Scheduled job info', subTitle='Job that controls the scheduled sync for this Knowledge Source')
      //- No job_id exists - show create button
      template(v-if='!jobId')
        .row.items-center.justify-center
          .col-auto
            .km-heading-3 No job scheduled
        .row.items-center.justify-center
          .col-auto
            .km-label.q-mb-sm Create a job to schedule automatic syncing for this Knowledge Source
        .row.items-center.justify-center
          .col-auto
            km-btn(:label='m.collections_createNewJob()', @click='showNewDialog = true')
      //- job_id exists but job not loaded yet - show loading state
      template(v-else-if='jobId && !job')
        .row.items-center.justify-center
          .col-auto
            q-spinner(color='primary', size='24px')
        .row.items-center.justify-center.q-mt-sm
          .col-auto
            .km-label Loading job information...
      //- Job loaded - show job info
      template(v-else)
        .col.q-pt-8
          .km-input-label.q-pb-xs.q-pl-8 Scheduled job
          km-select(:disabled='true', :modelValue='jobName')
        .row.q-mt-sm
          .col-auto
            km-btn(flat, simple, :label='"Open Job"', iconSize='16px', icon='fas fa-comment-dots', @click='openJob')
    q-separator.q-my-lg

    template(v-if='job')
      km-section(title='Schedule settings and status', subTitle='Go to the Job details to edit settings or cancel scheduled sync.')
        .row.q-col-gutter-md
          .col-4
            .km-field Status
            .km-label {{ jobStatus }}
          .col-4
            .km-field Job interval
            .km-label {{ jobInterval }}
          .col-4
            .km-field Start On
            .km-label {{ startDate }}
        .row.q-col-gutter-md.q-mt-md
          .col-4
            .km-field Repeat at
            .km-label {{ repeatAt }}
          .col-4
            .km-field Last run
            .km-label {{ formattedLastRun }}
          .col-4
            .km-field Next run
            .km-label {{ formattedNextRun }}
    .q-my-lg
    .row
      .col-auto
        .km-heading-4.q-mb-sm Last sync runs
      .col
      .col-auto
        km-btn.q-mr-12(
          icon='refresh',
          :label='m.collections_refreshList()',
          @click='refetchTraces',
          iconColor='icon',
          hoverColor='primary',
          labelClass='km-title',
          flat,
          iconSize='16px',
          hoverBg='primary-bg'
        )
    km-data-table(
      :table='table',
      :loading='isLoadingTraces', :fetching='isFetchingTraces',
      row-key='id',
      dense,
      @row-click='openDetails',
      style='min-width: 500px'
    )
km-inner-loading(:showing='loading')
jobs-create-new(:show-new-dialog='showNewDialog', @cancel='showNewDialog = false', @finish='finish', :formDefault='formDefault')
</template>

<script setup>
import { ref, nextTick, computed, markRaw, onMounted } from 'vue'
import { m } from '@/paraglide/messages'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
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
const q = useQuasar()
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
  componentColumn('status', 'Status', markRaw(StatusField), {
    accessorKey: 'status',
    sortable: true,
    align: 'center',
  }),
  dateColumn('start_time', 'Start Time'),
  textColumn('latency', 'Latency', {
    format: (val) => (val ? formatDuration(val) : '-'),
  }),
  {
    id: 'type',
    accessorFn: (row) => jobRunTypeOptions?.find((el) => el.value === row?.extra_data?.job_definition?.job_type)?.label || '-',
    header: 'Type',
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
  name: 'Job for Knowledge Source',
  jobType: 'sync_collection',
  executionType: 'recurring',
  system_name: draft.value?.system_name || '',
}))

const currentRow = computed(() => draft.value)
const jobName = computed(() => job.value?.definition.name || jobId.value || 'N/A')
const job = computed(() => jobDetailData.value ?? null)
const jobStatus = computed(() => job.value?.status || 'N/A')

const customCronDisplay = computed(() => {
  const cron = job.value?.definition?.cron
  if (!cron) return 'Custom'
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
  if (!interval) return 'N/A'
  const intervalLabels = {
    'every_5_minutes': 'Every 5 minutes',
    'hourly': 'Hourly',
    'daily': 'Daily',
    'weekly': 'Weekly',
    'monthly': 'Monthly',
    'custom': customCronDisplay.value,
  }
  return intervalLabels[interval] || interval
})

const startDate = computed(() => {
  if (!job.value?.definition?.scheduled_start_time) return 'N/A'
  const startTime = job.value.definition.scheduled_start_time
  const jobTimezone = job.value?.definition?.timezone || 'UTC'
  let dateObj = DateTime.fromISO(startTime)
  if (!dateObj.isValid) return 'N/A'
  if (!startTime.includes('+') && !startTime.includes('Z') && !startTime.includes('-', 10)) {
    dateObj = DateTime.fromISO(startTime, { zone: jobTimezone })
  }
  const localDate = dateObj.toLocal()
  return `${localDate.toLocaleString(DateTime.DATE_SHORT)} ${localDate.toLocaleString(DateTime.TIME_SIMPLE)}`
})

const repeatAt = computed(() => {
  const cron = job.value?.definition?.cron
  if (!cron) return 'N/A'
  return cronToHumanReadable(cron)
})

const formattedLastRun = computed(() => {
  if (!job.value?.last_run) return 'Not run yet'
  return formatDateTime(job.value.last_run)
})

const formattedNextRun = computed(() => {
  if (!job.value?.next_run) return 'Not scheduled'
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
    q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: 'Failed to save. Please try again.', timeout: 5000 })
  } finally {
    loading.value = false
  }
}

function setJobId(id) {
  updateField('job_id', id)
}

function cronToHumanReadable(cron) {
  if (!cron) return 'N/A'
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
      if (stepValue === 1) return 'Every minute'
      return `Every ${stepValue} minutes`
    }
  }
  if (minute && !minute.includes('*') && (hour === '*' || !hour)) {
    const parsedMinute = parseInt(minute)
    if (!isNaN(parsedMinute)) {
      const minStr = String(parsedMinute).padStart(2, '0')
      return `Every hour at :${minStr}`
    }
  }
  if (hour && hour.startsWith('*/')) {
    const stepValue = parseInt(hour.substring(2))
    if (!isNaN(stepValue)) {
      const minStr = minute && minute !== '*' ? String(parseInt(minute)).padStart(2, '0') : '00'
      return `Every ${stepValue} hours at :${minStr}`
    }
  }
  if (minute && hour && !minute.includes('*') && !hour.includes('*') &&
      (dayField === '*' || !dayField) && (day_of_week === '*' || !day_of_week)) {
    const timeStr = formatTime(hour, minute)
    if (timeStr) return `Daily at ${timeStr}`
  }
  if (minute && hour && day_of_week && day_of_week !== '*' && !minute.includes('*') && !hour.includes('*')) {
    const timeStr = formatTime(hour, minute)
    const dayNum = parseInt(day_of_week)
    const dayName = !isNaN(dayNum) && dayNum >= 0 && dayNum <= 6 ? dayNames[dayNum] : day_of_week
    if (timeStr) return `Every ${dayName} at ${timeStr}`
  }
  if (minute && hour && dayField && dayField !== '*' && !minute.includes('*') && !hour.includes('*')) {
    const timeStr = formatTime(hour, minute)
    const dayNum = parseInt(dayField)
    if (timeStr && !isNaN(dayNum)) {
      const suffix = dayNum === 1 ? 'st' : dayNum === 2 ? 'nd' : dayNum === 3 ? 'rd' : 'th'
      return `Monthly on the ${dayNum}${suffix} at ${timeStr}`
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
  window.open(router.resolve({ path: `/observability-traces/${row.id}` }).href, '_blank')
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
  min-height: 300px;
  padding: 2rem;
}
</style>
