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
            km-btn(label='Create new job', @click='showNewDialog = true')
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
          label='Refresh list',
          @click='refreshTable',
          iconColor='icon',
          hoverColor='primary',
          labelClass='km-title',
          flat,
          iconSize='16px',
          hoverBg='primary-bg'
        )
    km-table(
      ref='tableRef',
      @selectRow='openDetails',
      selection='single',
      row-key='id',
      :columns='Object.values(traceKsControls)',
      :visibleColumns='visibleColumnsCalc',
      :rows='visibleRows',
      style='min-width: 500px',
      binary-state-sort,
      :loading='loadinTraces',
      dense,
      @request='getPaginated',
      v-model:pagination='pagination',
      :filter='filterObject'
    )
q-inner-loading(:showing='loading')
jobs-create-new(:show-new-dialog='showNewDialog', @cancel='showNewDialog = false', @finish='finish', :formDefault='formDefault')
</template>

<script>
import { ref, nextTick, watch } from 'vue'
import { useChroma } from '@shared'
import { DateTime } from 'luxon'
import { formatDateTime } from '@shared/utils/dateTime'
import { traceKsControls } from '@/config/observability/traces'

export default {
  setup() {
    const { update, create } = useChroma('collections')
    const { getDetail } = useChroma('jobs')
    const { pagination, visibleColumns, columns, visibleRows, get, getPaginated, loading: loadinTraces } = useChroma('observability_traces')

    const tableRef = ref()
    return {
      loadinTraces,
      getDetail,
      loading: ref(false),
      formatDateTime,
      pagination,
      visibleColumns,
      columns,
      visibleRows,
      get,
      getPaginated,
      tableRef,
      showNewDialog: ref(false),
      update,
      create,
      traceKsControls,
    }
  },
  computed: {
    formDefault() {
      return {
        name: 'Job for Knowledge Source',
        jobType: 'sync_collection',
        executionType: 'recurring',
        system_name: this.currentRow?.system_name || '',
      }
    },
    currentRow() {
      return this.$store.getters.knowledge
    },
    filterObject: {
      get() {
        return { system_name_in: this.currentRow?.system_name }
      },
      set() {},
    },
    visibleColumnsCalc() {
      return ['status', 'start_time', 'latency', 'type']
    },
    jobId() {
      return this.$store.getters.knowledge?.job_id
    },
    jobName() {
      return this.job?.definition.name || this.jobId || 'N/A'
    },
    job() {
      return this.$store.getters['chroma/jobs'].items.find((j) => j.id === this.jobId)
    },
    jobStatus() {
      return this.job?.status || 'N/A'
    },
    jobInterval() {
      const interval = this.job?.definition?.interval
      if (!interval) return 'N/A'
      
      // Map interval values to human-readable labels
      const intervalLabels = {
        'every_5_minutes': 'Every 5 minutes',
        'hourly': 'Hourly',
        'daily': 'Daily',
        'weekly': 'Weekly',
        'monthly': 'Monthly',
        'custom': this.customCronDisplay,
      }
      
      return intervalLabels[interval] || interval
    },
    customCronDisplay() {
      const cron = this.job?.definition?.cron
      if (!cron) return 'Custom'
      
      // Build cron string from cron object
      const parts = [
        cron.minute || '*',
        cron.hour || '*',
        cron.day || cron.day_of_month || '*',
        cron.month || '*',
        cron.day_of_week || '*',
      ]
      
      return `Custom (${parts.join(' ')})`
    },
    startDate() {
      if (!this.job?.definition?.scheduled_start_time) return 'N/A'
      
      const startTime = this.job.definition.scheduled_start_time
      const jobTimezone = this.job?.definition?.timezone || 'UTC'
      
      // Parse the datetime and convert to local timezone for display
      let dateObj = DateTime.fromISO(startTime)
      
      // If the datetime doesn't have timezone info, assume it's in job's timezone
      if (!dateObj.isValid) {
        return 'N/A'
      }
      
      // If no zone info in the string, set it to job's timezone first
      if (!startTime.includes('+') && !startTime.includes('Z') && !startTime.includes('-', 10)) {
        dateObj = DateTime.fromISO(startTime, { zone: jobTimezone })
      }
      
      // Convert to local timezone for display
      const localDate = dateObj.toLocal()
      return `${localDate.toLocaleString(DateTime.DATE_SHORT)} ${localDate.toLocaleString(DateTime.TIME_SIMPLE)}`
    },
    repeatAt() {
      const cron = this.job?.definition?.cron
      if (!cron) return 'N/A'
      
      // Convert cron object to human-readable format
      return this.cronToHumanReadable(cron)
    },
    formattedLastRun() {
      if (!this.job?.last_run) return 'Not run yet'
      return this.formatDateTime(this.job.last_run)
    },
    formattedNextRun() {
      if (!this.job?.next_run) return 'Not scheduled'
      return this.formatDateTime(this.job.next_run)
    },
  },
  watch: {
    // Watch for jobId changes and fetch job details when it becomes available
    jobId: {
      async handler(newJobId, oldJobId) {
        if (newJobId && newJobId !== oldJobId) {
          try {
            await this.getDetail({ id: newJobId })
          } catch (error) {
            console.error('Error fetching job details:', error)
          }
        }
      },
      immediate: true,
    },
  },
  async mounted() {
    this.loading = true
    try {
      if (this.jobId) {
        await this.getDetail({ id: this.jobId })
      }
      // Wait for the next tick to ensure the table is mounted
      await nextTick()
      await this.refreshTable()
    } catch (error) {
      console.error('Error in mounted:', error)
    } finally {
      this.loading = false
    }
  },
  methods: {
    async save() {
      this.loading = true
      try {
        if (this.currentRow?.created) {
          const obj = { ...this.currentRow }
          delete obj._metadata
          delete obj.id
          console.log(obj)
          await this.update({ id: this.currentRow.id, data: obj })
        } else {
          await this.create(JSON.stringify(this.currentRow))
        }
      } catch (error) {
        console.error('Error saving:', error)
      } finally {
        this.loading = false
      }
    },
    setJobId(id) {
      this.$store.commit('updateKnowledge', { job_id: id })
    },
    cronToHumanReadable(cron) {
      if (!cron) return 'N/A'
      
      const { minute, hour, day, day_of_month, month, day_of_week } = cron
      const dayField = day || day_of_month
      
      const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
      
      // Helper to format time with timezone conversion
      const formatTime = (h, m) => {
        const parsedHour = parseInt(h)
        const parsedMinute = parseInt(m)
        if (isNaN(parsedHour) || isNaN(parsedMinute)) return null
        
        const jobTimezone = this.job?.definition?.timezone || 'UTC'
        const jobTime = DateTime.now()
          .setZone(jobTimezone)
          .set({ hour: parsedHour, minute: parsedMinute })
        const localTime = jobTime.toLocal()
        return `${localTime.toFormat('HH:mm')} (${localTime.toFormat('ZZZZ')})`
      }
      
      // Check for step patterns like */5
      if (minute && minute.startsWith('*/')) {
        const stepValue = parseInt(minute.substring(2))
        if (!isNaN(stepValue)) {
          if (stepValue === 1) return 'Every minute'
          return `Every ${stepValue} minutes`
        }
      }
      
      // Check for hourly pattern: specific minute, any hour
      if (minute && !minute.includes('*') && (hour === '*' || !hour)) {
        const parsedMinute = parseInt(minute)
        if (!isNaN(parsedMinute)) {
          const minStr = String(parsedMinute).padStart(2, '0')
          return `Every hour at :${minStr}`
        }
      }
      
      // Check for hour step patterns like */2
      if (hour && hour.startsWith('*/')) {
        const stepValue = parseInt(hour.substring(2))
        if (!isNaN(stepValue)) {
          const minStr = minute && minute !== '*' ? String(parseInt(minute)).padStart(2, '0') : '00'
          return `Every ${stepValue} hours at :${minStr}`
        }
      }
      
      // Daily pattern: specific hour and minute, any day
      if (minute && hour && !minute.includes('*') && !hour.includes('*') && 
          (dayField === '*' || !dayField) && (day_of_week === '*' || !day_of_week)) {
        const timeStr = formatTime(hour, minute)
        if (timeStr) return `Daily at ${timeStr}`
      }
      
      // Weekly pattern: specific day_of_week
      if (minute && hour && day_of_week && day_of_week !== '*' && !minute.includes('*') && !hour.includes('*')) {
        const timeStr = formatTime(hour, minute)
        const dayNum = parseInt(day_of_week)
        const dayName = !isNaN(dayNum) && dayNum >= 0 && dayNum <= 6 ? dayNames[dayNum] : day_of_week
        if (timeStr) return `Every ${dayName} at ${timeStr}`
      }
      
      // Monthly pattern: specific day of month
      if (minute && hour && dayField && dayField !== '*' && !minute.includes('*') && !hour.includes('*')) {
        const timeStr = formatTime(hour, minute)
        const dayNum = parseInt(dayField)
        if (timeStr && !isNaN(dayNum)) {
          const suffix = dayNum === 1 ? 'st' : dayNum === 2 ? 'nd' : dayNum === 3 ? 'rd' : 'th'
          return `Monthly on the ${dayNum}${suffix} at ${timeStr}`
        }
      }
      
      // Fallback: show cron expression
      const parts = [minute || '*', hour || '*', dayField || '*', month || '*', day_of_week || '*']
      return parts.join(' ')
    },
    async finish(job) {
      try {
        this.setJobId(job.job_id)
        await this.save()
        this.showNewDialog = false
        await this.getDetail({ id: this.jobId })
        await this.refreshTable()
      } catch (error) {
        console.error('Error in finish:', error)
      }
    },
    async refreshTable() {
      this.loading = true
      try {
        if (this.tableRef) {
          await this.tableRef.requestServerInteraction()
        } else {
          console.warn('Table reference is not available yet')
        }
      } catch (error) {
        console.error('Error refreshing table:', error)
      } finally {
        this.loading = false
      }
    },
    navigate(path = '') {
      if (this.$route?.path !== `/${path}`) {
        this.$router?.push(`/${path}`)
      }
    },
    async openDetails(row) {
      window.open(this.$router.resolve({ path: `/observability-traces/${row.id}` }).href, '_blank')
    },
    openJob() {
      if (!this.jobId) return
      // Navigate to job details page
      this.$router.push({
        name: 'Jobs',
        query: { job_id: this.jobId },
      })
    },
    createJob() {
      // Logic to create a new job for this Knowledge Source
      this.$router.push({
        name: 'Jobs',
        query: {
          create: true,
          knowledge_source_id: this.$store.getters.knowledge?.id,
        },
      })
    },
  },
}
</script>

<style scoped>
.empty-state {
  min-height: 300px;
  padding: 2rem;
}
</style>
