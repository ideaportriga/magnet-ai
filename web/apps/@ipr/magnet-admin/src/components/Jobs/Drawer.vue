<template lang="pug">
transition(appear, enter-active-class='animated fadeIn', leave-active-class='animated fadeOut')
  .column.no-wrap.full-height.justify-center.q-pa-16.bg-white.fit.relative-position.bl-border(
    v-if='showDrawer',
    style='max-width: 500px; min-width: 500px !important'
  )
    .col-auto.km-heading-7.q-mb-xs Job details
    q-separator.q-mb-xs
    .column.fit(v-if='job')
      q-scroll-area.col
        .row.align-center
          .col
            .km-description.text-secondary-text.q-pb-6 Job info
            .row
              .km-label {{ jobName }}
          .col-auto.items-center.flex
            .row.items-center.q-gap-4
              .col-auto
                km-chip(:label='runConfigurationType', color='light') 
              .col-auto
                km-chip(:label='jobStatus', color='light')
        .row.q-pt-16
          .col
            .km-description.text-secondary-text.q-pb-6 Target
            .row.q-gap-8
              .km-label {{ systemName }}
              km-chip.text-grey(:label='runConfigurationType', color='in-progress')
        .col.q-pt-16.full-width
          .col-auto.km-button-text.q-mb-xs Scheduling settings
          q-separator.q-mb-xs
        .row.q-pt-24(style='gap: 18px 0')
          .col-6
            .km-description.text-secondary-text.q-pb-6 Job Type
            .row
              .km-label {{ jobType }}
          .col-6
            .km-description.text-secondary-text.q-pb-6 Next Run
            .row
              .km-label {{ nextRun }}
          .col-6
            .km-description.text-secondary-text.q-pb-6 Created At
            .row
              .km-label {{ createdAt }}
          .col-6
            .km-description.text-secondary-text.q-pb-6 Timezone
            .row
              .km-label {{ timezone }}
          .col-6
            .km-description.text-secondary-text.q-pb-6 Job Interval
            .row
              .km-label {{ interval }}
          .col-6
            .km-description.text-secondary-text.q-pb-6 Repeat at
            .row
              .km-label {{ cronDescription }}

        .row.q-pt-24
          .col-6
            .km-description.text-secondary-text.q-pb-6 Job ID
            .row
              .km-label {{ jobId }}

      .col-auto.q-pt-16
        .row.justify-between
          .col-auto
            km-btn(flat, @click='showCancelJobConfirm') Cancel Job
          .col-auto
            km-btn(flat, @click='showReconfigureJobConfirm') Reconfigure Job

    km-popup-confirm(
      :visible='showCancelConfirm',
      confirmButtonLabel='Yes, cancel job',
      confirmButtonType='negative',
      cancelButtonLabel='No, keep job',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmCancelJob',
      @cancel='closeCancelConfirm'
    )
      .row.item-center.justify-center.km-heading-7.q-mb-md Cancel Job
      .row.text-center.justify-center Are you sure you want to cancel this job?

    jobs-create-new(
      :showNewDialog='showReconfigureConfirm',
      @cancel='closeReconfigureConfirm',
      @create='confirmReconfigureJob',
      v-if='showReconfigureConfirm',
      :job='job'
    )
</template>

<script>
import { jobRunTypeOptions, jobTypeOptions, jobIntervalOptions } from '@/config/jobs/jobs'
import { DateTime } from 'luxon'

export default {
  props: {
    showDrawer: {
      type: Boolean,
      default: false,
    },
    job: {
      type: Object,
      default: () => null,
    },
  },
  data() {
    return {
      showCancelConfirm: false,
      showReconfigureConfirm: false,
    }
  },
  computed: {
    jobName() {
      return this.job?.definition?.name || this.job?.name || 'Not specified'
    },
    runConfigurationType() {
      const option = jobTypeOptions.find((option) => option.value === this.job?.definition?.run_configuration?.type)
      return option?.label || this.job?.definition?.run_configuration?.type || 'Not specified'
    },
    jobStatus() {
      return this.job?.status || 'Not specified'
    },
    systemName() {
      const params = this.job?.definition?.run_configuration?.params
      const type = this.job?.definition?.run_configuration?.type

      if (type === 'evaluation' && params) {
        const parts = []
        if (params.type) parts.push(params.type)
        const testSets = params.config
          ?.flatMap((c) => c.test_set_system_names || [])
          ?.join(', ')
        if (testSets) parts.push(testSets)
        return parts.join(' · ') || params.system_name || 'Not specified'
      }

      if (type === 'cleanup_logs' && params) {
        const days = params.retention_days
        return days ? `Retention: ${days} days` : params.system_name || 'Not specified'
      }

      return params?.system_name || 'Not specified'
    },
    jobType() {
      const option = jobRunTypeOptions.find((option) => option.value === this.job?.definition?.job_type)
      return option?.label || 'Not specified'
    },
    interval() {
      const intervalValue = this.job?.definition?.interval
      if (!intervalValue) return 'Not specified'
      
      // For custom interval, show the cron expression
      if (intervalValue === 'custom') {
        const cron = this.job?.definition?.cron
        if (cron) {
          const parts = [
            cron.minute || '*',
            cron.hour || '*',
            cron.day || cron.day_of_month || '*',
            cron.month || '*',
            cron.day_of_week || '*',
          ]
          return `Custom (${parts.join(' ')})`
        }
        return 'Custom'
      }
      
      const option = jobIntervalOptions.find((opt) => opt.value === intervalValue)
      return option?.label || intervalValue
    },
    nextRun() {
      return this.formatDateTime(this.job?.next_run)
    },
    createdAt() {
      return this.formatDateTime(this.job?.created_at)
    },
    timezone() {
      return this.job?.definition?.timezone || 'Not specified'
    },
    configurationStatus() {
      return this.job?.definition?.status || 'Not specified'
    },
    cronHour() {
      return this.job?.definition?.cron?.hour || 'Not specified'
    },
    cronMinute() {
      return this.job?.definition?.cron?.minute || 'Not specified'
    },
    cronDay() {
      return this.job?.definition?.cron?.day || 'Not specified'
    },
    cronDayOfWeek() {
      return this.job?.definition?.cron?.day_of_week
    },
    jobId() {
      return this.job?.id || this.job?._id || 'Not specified'
    },
    cronDescription() {
      const cron = this.job?.definition?.cron
      if (!cron) return 'Not specified'
      
      const { minute, hour, day, day_of_month, month, day_of_week } = cron
      const dayField = day || day_of_month
      
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
        const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
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
  },
  methods: {
    // days from 0 to 6
    getDayOfWeekName(day) {
      const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
      return days[day] || 'Not specified'
    },

    formatDateTime(dateTimeString) {
      if (!dateTimeString) return 'Not specified'
      const dt = DateTime.fromISO(dateTimeString, { zone: 'utc' })
      if (!dt.isValid) return 'Not specified'
      return dt.toLocal().toLocaleString(DateTime.DATETIME_MED)
    },
    showCancelJobConfirm() {
      this.showCancelConfirm = true
    },
    closeCancelConfirm() {
      this.showCancelConfirm = false
    },
    async confirmCancelJob() {
      try {
        const jobId = this.job.id || this.job._id
        if (!jobId) {
          console.error('No job ID found for cancellation')
          return
        }

        const result = await this.$store.dispatch('cancelJobScheduler', jobId)
        this.$q.notify({
          position: 'top',
          color: 'positive',
          color: 'positive',
          textColor: 'black',
          message: 'Job successfully cancelled',
        })
      } catch (error) {
        console.error('Error cancelling job:', error)
        this.$q.notify({
          position: 'top',
          color: 'negative',
          textColor: 'white',
          icon: 'error',
          message: 'Failed to cancel job',
        })
      } finally {
        this.showCancelConfirm = false
      }
    },
    showReconfigureJobConfirm() {
      this.showReconfigureConfirm = true
    },
    closeReconfigureConfirm() {
      this.showReconfigureConfirm = false
    },
    confirmReconfigureJob() {
      this.showReconfigureConfirm = false
    },
    onCancelJob() {
      this.showCancelJobConfirm()
    },
    onReconfigureJob() {
      this.showReconfigureJobConfirm()
    },
  },
}
</script>
