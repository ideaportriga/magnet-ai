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
import { jobRunTypeOptions, jobTypeOptions } from '@/config/jobs/jobs'

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
      return option?.label || 'Not specified'
    },
    jobStatus() {
      return this.job?.status || 'Not specified'
    },
    systemName() {
      return this.job?.definition?.run_configuration?.params?.system_name || 'Not specified'
    },
    jobType() {
      const option = jobRunTypeOptions.find((option) => option.value === this.job?.definition?.job_type)
      return option?.label || 'Not specified'
    },
    interval() {
      return this.job?.definition?.interval || 'Not specified'
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
      const hour = this.cronHour !== 'Not specified' ? this.cronHour : null
      const day = this.cronDay !== 'Not specified' ? this.cronDay : null
      const dayOfWeek = this.cronDayOfWeek

      if (hour == '*') {
        return `Every hour`
      } else if (hour && !day && !(dayOfWeek || dayOfWeek == 0)) {
        return `Every day at ${hour}:00`
      } else if (hour && (dayOfWeek || dayOfWeek == 0) && !day) {
        return `Every ${this.getDayOfWeekName(dayOfWeek)} at ${hour}:00`
      } else {
        return 'Schedule not specified'
      }
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
      try {
        // Ensure the string is treated as UTC if it doesn't already include a timezone
        if (!dateTimeString.includes('Z') && !dateTimeString.includes('+') && !dateTimeString.includes('-')) {
          dateTimeString += 'Z' // Append UTC timezone if missing
        }
        // Handle cases where fractional seconds are present
        const normalizedDateTimeString = dateTimeString.replace(/(\.\d+)(?!Z|[+-])/, '$1Z')
        const date = new Date(normalizedDateTimeString)
        return date.toLocaleString()
      } catch (e) {
        return dateTimeString
      }
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
