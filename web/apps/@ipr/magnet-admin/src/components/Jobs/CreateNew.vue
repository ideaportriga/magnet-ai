<template>
  <km-dialog :model-value="showNewDialog" @cancel="$emit(&quot;cancel&quot;)">
    <km-card class="card-style" style="min-inline-size: 700px">
      <div class="km-card-section card-section-style">
        <div class="cluster" data-justify="between">
          <div class="km-heading-7">{{ job.id ? 'Reconfigure' : 'New' }} Job</div>
          <km-btn icon="close" flat dense @click="$emit(&quot;cancel&quot;)" />
        </div>
      </div>
      <div class="km-card-section card-section-style mb-md">
        <div class="km-field text-secondary-text pb-xs pl-sm">Name</div>
        <div class="full-width">
          <km-input ref="nameRef" v-model="form.name" height="30px" />
        </div>
        <div class="km-field text-secondary-text pb-xs pl-sm pt-md">Job execution type</div>
        <div class="full-width">
          <km-select v-model="form.executionType" :options="executionTypes" emit-value map-options :disabled="isFormDefault" />
        </div>
        <div class="km-field text-secondary-text pb-xs pl-sm pt-md">Job</div>
        <div class="full-width">
          <km-select v-model="form.jobType" :options="jobTypes" emit-value map-options :disabled="isFormDefault" />
        </div>
        <!-- is_system checkbox for recurring jobs only-->
        <div v-if="form.executionType === &quot;recurring&quot;" class="cluster mt-md">
          <km-checkbox v-model="form.is_system" :label="m.collections_systemJob()" :disable="form.executionType !== &quot;recurring&quot;" />
        </div>
        <!-- Hide additional parameters if is_system is checked-->
        <template v-if="!form.is_system">
          <template v-if="form.jobType === &quot;sync_collection&quot;">
            <div class="km-field text-secondary-text pb-xs pl-sm pt-md">System name</div>
            <div class="full-width">
              <km-input v-model="form.system_name" height="30px" :placeholder="m.jobs_enterSystemName()" :disabled="isFormDefault" />
            </div>
          </template>
          <template v-if="form.jobType === &quot;post_processing_conversations&quot;">
            <div class="km-field text-secondary-text pb-xs pl-sm pt-md">Agents</div>
            <div class="full-width" />
            <km-select v-model="form.agents" data-test="agents-select" height="auto" min-height="36px" :placeholder="m.jobs_selectAgents()" multiple :options="agents" use-chips has-dropdown-search emit-value map-options option-value="system_name" option-label="name" />
          </template>
          <template v-if="form.jobType === &quot;cleanup_logs&quot;">
            <div class="km-field text-secondary-text pb-xs pl-sm pt-md">Retention period (days)</div>
            <div class="full-width">
              <km-input v-model.number="form.retention_days" type="number" height="30px" placeholder="30" :min="1" />
            </div>
            <div class="km-tiny text-secondary-text pl-sm pt-xs">Logs older than this will be deleted</div>
            <div class="cluster mt-md pl-sm" data-gap="lg">
              <km-checkbox v-model="form.cleanup_traces" :label="m.observability_deleteTraces()" />
              <km-checkbox v-model="form.cleanup_metrics" :label="m.observability_deleteMetrics()" />
            </div>
          </template>
        </template>
        <div v-if="form.executionType === &quot;recurring&quot;" class="km-field text-secondary-text pb-xs pl-sm pt-md">Job interval</div>
        <div v-if="form.executionType === &quot;recurring&quot;" class="full-width">
          <km-btn-toggle v-model="form.interval" :options="intervals" dense />
        </div>
        <div v-if="(form.interval === &quot;daily&quot; || form.interval === &quot;weekly&quot;) &amp;&amp; form.executionType !== &quot;one_time_immediate&quot;" class="cluster mt-md pl-sm" data-gap="sm">
          <div v-if="form.interval === &quot;weekly&quot;" class="cluster" data-gap="sm">
            <div class="km-field text-secondary-text">Every</div>
            <km-select v-model="form.day" :options="days" emit-value map-options />
          </div>
          <div class="cluster" data-gap="sm">
            <div class="km-field text-secondary-text">at</div>
            <km-select v-model="form.time" :options="times" />
          </div>
        </div>
        <div v-if="form.interval === &quot;custom&quot; &amp;&amp; form.executionType === &quot;recurring&quot;" class="mt-md pl-sm">
          <div class="km-field text-secondary-text pb-xs">Cron expression</div>
          <km-input v-model="form.customCron" height="30px" :placeholder="m.common_cronExpression()" />
          <div class="km-tiny text-secondary-text mt-xs">Format: minute hour day month day_of_week (e.g., */10 * * * * for every 10 minutes)</div>
        </div>
        <div class="cluster mt-md">
          <km-checkbox v-model="form.enabled" size="40px" disable />
          <div class="km-field">Send error notifications (upcoming feature)</div>
        </div>
        <div class="km-tiny text-secondary-text">Email admin in case of syncing errors. Applies only for scheduled sync.</div>
        <template v-if="form.enabled">
          <div class="km-field text-secondary-text pb-xs pl-sm pt-md">Error notification email</div>
          <div class="full-width">
            <km-input ref="errorEmailRef" v-model="form.error_email" height="30px" />
          </div>
        </template>
        <div class="cluster mt-lg" data-justify="between">
          <km-btn flat :label="m.common_cancel()" tone="brand" @click="$emit(&quot;cancel&quot;)" />
          <km-btn :label="m.common_save()" @click="finish" />
        </div>
      </div>
    </km-card>
  </km-dialog>
</template>

<script>
import { ref, reactive, watch } from 'vue'
import _ from 'lodash'
import { fetchData } from '@shared'
import { m } from '@/paraglide/messages'
import { useAppStore } from '@/stores/appStore'
import { useCatalogOptions } from '@/queries/useCatalogOptions'

const intervals = [
  { label: 'Every 5 minutes', value: 'every_5_minutes' },
  { label: 'Hourly', value: 'hourly' },
  { label: 'Daily', value: 'daily' },
  { label: 'Weekly', value: 'weekly' },
  { label: 'Custom', value: 'custom' },
]
const days = [
  { label: 'Monday', value: 0 },
  { label: 'Tuesday', value: 1 },
  { label: 'Wednesday', value: 2 },
  { label: 'Thursday', value: 3 },
  { label: 'Friday', value: 4 },
  { label: 'Saturday', value: 5 },
  { label: 'Sunday', value: 6 },
]
const jobTypes = [
  { label: 'Custom', value: 'custom' },
  { label: 'Sync knowledge source', value: 'sync_collection' },
  { label: 'Post-processing conversations', value: 'post_processing_conversations' },
  { label: 'Cleanup logs (traces & metrics)', value: 'cleanup_logs' },
]
const executionTypes = [
  { label: 'Run Once Immediately', value: 'one_time_immediate' },
  { label: 'Run Once at Scheduled Time', value: 'one_time_scheduled' },
  { label: 'Recurring', value: 'recurring' },
]
// Generate times for every hour
const times = Array.from({ length: 24 }, (_, i) => {
  const hour = String(i).padStart(2, '0')
  return { label: `${hour}:00`, value: i }
})

export default {
  props: {
    showNewDialog: {
      type: Boolean,
      required: true,
    },
    job: {
      type: Object,
      default: () => ({}),
    },
    formDefault: {
      type: Object,
      default: () => ({}),
    },
  },
  emits: ['cancel', 'finish'],
  setup(props) {
    const job = _.cloneDeep(props.job)

    const { options: agents } = useCatalogOptions('agents')

    const form = reactive({
      ...{
        name: '',
        interval: 'daily',
        day: 0,
        time: { label: '03:00', value: 3 },
        enabled: false,
        jobType: 'custom',
        error_email: '',
        executionType: 'recurring',
        system_name: '',
        agents: [],
        is_system: false, // new param
        customCron: '*/10 * * * *', // default custom cron
        // Cleanup logs params
        retention_days: 30,
        cleanup_traces: true,
        cleanup_metrics: true,
      },
      ...props.formDefault,
      ...(!_.isEmpty(job)
        ? {
            job_id: job.id,
            name: job.definition.name,
            interval: job.definition.interval,
            jobType: job.definition?.run_configuration?.type,
            system_name: job.definition?.run_configuration?.params?.system_name,
            is_system: job.definition?.is_system || false,
            // Cleanup logs params from existing job
            retention_days: job.definition?.run_configuration?.params?.retention_days || 30,
            cleanup_traces: job.definition?.run_configuration?.params?.cleanup_traces !== false,
            cleanup_metrics: job.definition?.run_configuration?.params?.cleanup_metrics !== false,
          }
        : {}),
    })

    // Watch executionType and reset is_system if not recurring
    watch(
      () => form.executionType,
      (val) => {
        if (val !== 'recurring') {
          form.is_system = false
        }
      }
    )

    const appStore = useAppStore()

    return {
      m,
      form,
      intervals,
      days,
      jobTypes,
      executionTypes,
      times,
      agents,
      appStore,
    }
  },
  computed: {
    isFormDefault() {
      return Object.keys(this.formDefault).length > 0
    },
  },
  methods: {
    async createJob() {

      let params
      // Only add params if not is_system
      if (!this.form.is_system) {
        if (this.form.jobType === 'post_processing_conversations') {
          params = {
            agent_system_names: this.form.agents,
          }
        } else if (this.form.jobType === 'sync_collection') {
          params = {
            system_name: this.form.system_name,
          }
        } else if (this.form.jobType === 'cleanup_logs') {
          params = {
            retention_days: this.form.retention_days,
            cleanup_traces: this.form.cleanup_traces,
            cleanup_metrics: this.form.cleanup_metrics,
          }
        }
      }

      // Always ensure params is an object
      if (!params) params = {}
      // Always set is_system inside params
      params.is_system = this.form.is_system

      let jobData = {
        job_id: this.form.job_id,
        name: this.form.name,
        job_type: this.form.executionType,
        notification_email: this.form.error_email,
        run_configuration: {
          type: this.form.jobType,
          params: params,
        },
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      }

      // Only add cron and interval for scheduled jobs
      if (this.form.executionType !== 'one_time_immediate') {
        const hour = typeof this.form.time === 'object' ? this.form.time.value : this.form.time
        let cron
        if (this.form.interval === 'custom') {
          // Parse custom cron string: minute hour day month day_of_week
          const parts = this.form.customCron.trim().split(/\s+/)
          cron = {
            minute: parts[0] || '*',
            hour: parts[1] || '*',
            day: parts[2] || '*',
            month: parts[3] || '*',
            day_of_week: parts[4] || '*',
          }
        } else if (this.form.interval === 'every_5_minutes') {
          cron = { minute: '*/5', hour: '*', day_of_month: '*' }
        } else if (this.form.interval === 'hourly') {
          cron = { minute: '0', hour: '*', day_of_month: '*' }
        } else if (this.form.interval === 'daily') {
          cron = { minute: '0', hour, day_of_month: '*' }
        } else {
          // weekly
          cron = { minute: '0', hour, day_of_month: '*', day_of_week: this.form.day }
        }

        jobData.cron = cron
        jobData.interval = this.form.interval
      }

      const endpoint = this.appStore.config?.scheduler?.endpoint
      const service = this.appStore.config?.scheduler?.service
      const credentials = this.appStore.config?.scheduler?.credentials
      const response = await fetchData({
        endpoint,
        service: `${service}/create-job`,
        method: 'POST',
        body: JSON.stringify(jobData),
        credentials,
        headers: { 'Content-Type': 'application/json' },
      })
      const job = await response.json()
      this.$emit('finish', job)
    },

    finish() {
      this.createJob()
      this.$emit('cancel')
    },
  },
}
</script>
