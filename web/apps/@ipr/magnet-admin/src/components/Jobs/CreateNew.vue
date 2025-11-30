<template lang="pug">
q-dialog(:model-value='showNewDialog', @cancel='$emit("cancel")')
  q-card.card-style(style='min-width: 700px')
    q-card-section.card-section-style
      .row
        .col
          .km-heading-7 {{ job.id ? 'Reconfigure' : 'New' }} Job
        .col-auto
          q-btn(icon='close', flat, dense, @click='$emit("cancel")')
    q-card-section.card-section-style.q-mb-md
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Name
      .full-width
        km-input(height='30px', v-model='form.name', ref='nameRef')

      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-pt-md Job execution type
      .full-width
        km-select(v-model='form.executionType', :options='executionTypes', emit-value, map-options, :disabled='isFormDefault')

      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-pt-md Job
      .full-width
        km-select(v-model='form.jobType', :options='jobTypes', emit-value, map-options, :disabled='isFormDefault')

      // is_system checkbox for recurring jobs only
      .row.items-center.q-mt-md(v-if='form.executionType === "recurring"')
        km-checkbox(v-model='form.is_system', label='System job (applies to all records)', :disable='form.executionType !== "recurring"')
        //- When is_system is checked, all additional parameters are hidden, as it applies to all records

      // Hide additional parameters if is_system is checked
      template(v-if='!form.is_system')
        template(v-if='form.jobType === "sync_collection"')
          .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-pt-md System name
          .full-width
            km-input(height='30px', v-model='form.system_name', placeholder='Enter system name', :disabled='isFormDefault')

        template(v-if='form.jobType === "post_processing_conversations"')
          .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-pt-md Agents
          .full-width
          km-select(
            data-test='agents-select',
            height='auto',
            minHeight='36px',
            placeholder='Select agents',
            multiple,
            :options='agents',
            v-model='form.agents',
            use-chips,
            hasDropdownSearch,
            emit-value,
            map-options,
            option-value='system_name',
            option-label='name'
          )

      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-pt-md(v-if='form.executionType === "recurring"') Job interval
      .full-width(v-if='form.executionType === "recurring"')
        q-btn-toggle(
          v-model='form.interval',
          toggle-color='primary-light',
          :options='intervals',
          dense,
          text-color='text-weak',
          toggle-text-color='primary'
        )
      .row.q-mt-md.items-center.q-gap-8.q-pl-8(
        v-if='(form.interval === "daily" || form.interval === "weekly") && form.executionType !== "one_time_immediate"'
      )
        .row.items-center.q-gap-8(v-if='form.interval === "weekly"')
          .km-field.text-secondary-text Every
          km-select(v-model='form.day', :options='days', emit-value, map-options)
        .row.items-center.q-gap-8
          .km-field.text-secondary-text at
          km-select(v-model='form.time', :options='times')
      .row.q-mt-md.items-center
        km-checkbox(size='40px', v-model='form.enabled', disable)
        .km-field Send error notifications (upcoming feature)
      .km-tiny.text-secondary-text Email admin in case of syncing errors. Applies only for scheduled sync.
      template(v-if='form.enabled')
        .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-pt-md Error notification email
        .full-width
          km-input(height='30px', v-model='form.error_email', ref='errorEmailRef')
      .row.q-mt-lg
        .col-auto
          km-btn(flat, label='Cancel', color='primary', @click='$emit("cancel")')
        .col
        .col-auto
          km-btn(label='Save', @click='finish')
</template>

<script>
import { ref, reactive, watch } from 'vue'
import _ from 'lodash'
import { useChroma } from '@shared'

const intervals = [
  { label: 'Hourly', value: 'hourly' },
  { label: 'Daily', value: 'daily' },
  { label: 'Weekly', value: 'weekly' },
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

    const { items: agents } = useChroma('agents')

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

    return {
      form,
      intervals,
      days,
      jobTypes,
      executionTypes,
      times,
      agents,
    }
  },
  computed: {
    isFormDefault() {
      return Object.keys(this.formDefault).length > 0
    },
  },
  methods: {
    async createJob() {
      console.log('form=', this.form)

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
        const cron =
          this.form.interval === 'hourly'
            ? { minute: '0', hour: '*', day_of_month: '*' }
            : this.form.interval === 'daily'
              ? { minute: '0', hour, day_of_month: '*' }
              : { minute: '0', hour, day_of_month: '*', day_of_week: this.form.day }

        jobData.cron = cron
        jobData.interval = this.form.interval
      }

      const job = await this.$store.dispatch('createAndRunJobScheduler', jobData)
      this.$emit('finish', job)
    },

    finish() {
      this.createJob()
      this.$emit('cancel')
    },
  },
}
</script>
