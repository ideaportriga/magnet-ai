<template>
  <transition appear enter-active-class="animated fadeIn" leave-active-class="animated fadeOut">
    <km-drawer-layout v-if="showDrawer" storage-key="drawer-jobs">
      <template #header>
        <div class="km-heading-7">Job details</div>
      </template>
      <template v-if="job">
        <div class="cluster">
          <div class="flex-1">
            <div class="km-description text-secondary-text pb-sm">Job info</div>
            <div class="km-label">{{ jobName }}</div>
          </div>
          <div class="flex-none flex items-center">
            <div class="cluster" data-gap="xs">
              <km-chip :label="runConfigurationType" tone="neutral" />
              <km-chip :label="jobStatus" tone="neutral" />
            </div>
          </div>
        </div>
        <div class="pt-lg">
          <div class="km-description text-secondary-text pb-sm">Target</div>
          <div class="cluster" data-gap="sm">
            <div class="km-label">{{ systemName }}</div>
            <km-chip class="text-grey" :label="runConfigurationType" tone="neutral" />
          </div>
        </div>
        <div class="flex-1 pt-lg full-width">
          <div class="flex-none km-button-text mb-xs">Scheduling settings</div>
          <km-separator class="mb-xs" />
        </div>
        <div class="jobs-drawer__settings-grid pt-2xl">
          <div>
            <div class="km-description text-secondary-text pb-sm">Job Type</div>
            <div class="km-label">{{ jobType }}</div>
          </div>
          <div>
            <div class="km-description text-secondary-text pb-sm">Next Run</div>
            <div class="km-label">{{ nextRun }}</div>
          </div>
          <div>
            <div class="km-description text-secondary-text pb-sm">Created At</div>
            <div class="km-label">{{ createdAt }}</div>
          </div>
          <div>
            <div class="km-description text-secondary-text pb-sm">Timezone</div>
            <div class="km-label">{{ timezone }}</div>
          </div>
          <div>
            <div class="km-description text-secondary-text pb-sm">Job Interval</div>
            <div class="km-label">{{ interval }}</div>
          </div>
          <div>
            <div class="km-description text-secondary-text pb-sm">Repeat at</div>
            <div class="km-label">{{ cronDescription }}</div>
          </div>
        </div>
        <div class="cluster pt-2xl">
          <div class="flex-1">
            <div class="km-description text-secondary-text pb-sm">Job ID</div>
            <div class="km-label">{{ jobId }}</div>
          </div>
        </div>
      </template>
      <div v-if="job" class="flex-none pt-lg">
        <div class="cluster" data-justify="between">
          <km-btn flat @click="showCancelJobConfirm">Cancel Job</km-btn>
          <km-btn flat @click="showReconfigureJobConfirm">Reconfigure Job</km-btn>
        </div>
      </div>
      <km-popup-confirm :visible="showCancelConfirm" confirm-button-label="Yes, cancel job" confirm-button-type="negative" cancel-button-label="No, keep job" notification-icon="warning" @confirm="confirmCancelJob" @cancel="closeCancelConfirm">
        <div class="cluster km-heading-7 mb-md" data-justify="center">Cancel Job</div>
        <div class="cluster text-center" data-justify="center">Are you sure you want to cancel this job?</div>
      </km-popup-confirm>
      <jobs-create-new v-if="showReconfigureConfirm" :show-new-dialog="showReconfigureConfirm" :job="job" @cancel="closeReconfigureConfirm" @create="confirmReconfigureJob" />
    </km-drawer-layout>
  </transition>
</template>

<script>
import { jobRunTypeOptions, jobTypeOptions, jobIntervalOptions } from '@/config/jobs/jobs'
import { DateTime } from 'luxon'
import { fetchData } from '@shared'
import { useAppStore } from '@/stores/appStore'
import { notify } from '@shared/utils/notify'

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
  setup() {
    const appStore = useAppStore()
    return { appStore }
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
          return
        }

        const endpoint = this.appStore.config?.scheduler?.endpoint
        const service = this.appStore.config?.scheduler?.service
        const credentials = this.appStore.config?.scheduler?.credentials
        await fetchData({
          endpoint,
          service: `${service}/cancel-job`,
          method: 'POST',
          body: JSON.stringify({ job_id: jobId }),
          headers: { 'Content-Type': 'application/json' },
          credentials,
        })
        notify.success('Job successfully cancelled')
      } catch (error) {
        notify.error('Failed to cancel job')
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

<style scoped>
.jobs-drawer__settings-grid {
  display: grid;
  gap: 18px var(--ds-space-md);
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 767px) {
  .jobs-drawer__settings-grid {
    grid-template-columns: 1fr;
  }
}
</style>
