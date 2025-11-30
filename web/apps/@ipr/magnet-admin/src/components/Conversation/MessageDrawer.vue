<template lang="pug">
.column.bg-white.fit.bl-border.height-100.fit.no-wrap.q-pt-16(style='min-width: 500px; max-width: 500px')
  .row.no-wrap.full-width.q-px-16.q-py-6
    .row.cursor-pointer.q-gap-8.items-center(@click='$emit("close")')
      q-icon(name='fas fa-arrow-left', size='14px', color='secondary')
      .km-title.text-secondary-text Back to conversation
  .bb-border
  .row.no-wrap.full-width.q-px-16.q-py-6
    q-tabs(
      v-model='tab',
      narrow-indicator,
      dense,
      align='left',
      active-color='primary',
      indicator-color='primary',
      active-bg-color='white',
      no-caps,
      content-class='km-tabs-dense'
    )
      template(v-for='t in tabs')
        q-tab(:name='t.name', :label='t.label')
      .fit
  .column.q-px-8.no-wrap.fit
    q-scroll-area.fit
      .column.full-height.q-py-6.q-px-16.q-gap-16
        .column.q-gap-16(v-if='tab === "details"')
          .col-6
            .km-description.text-secondary-text.q-pb-6 Message Time
            .row
              .km-label {{ time }}
          .col-6
            .km-description.text-secondary-text.q-pb-6.text-capitalize Latency
            .row
              .km-label {{ responseTime }}
          .col-6
            .km-description.text-secondary-text.q-pb-6.text-capitalize Role
            .row
              .km-label.text-capitalize {{ message?.role }}
          //- .col-6
          //-   .km-description.text-secondary-text.q-pb-6 Message
          //-   .row
          //-     dashboard-markdown(:source='message?.content')
          .col-6
            .km-description.text-secondary-text.q-pb-6.text-capitalize Agent Topic
            .row
              .km-label {{ topic }}
          .km-button-text.bb-border.q-pb-4 User satisfaction
          .col-6
            .km-description.text-secondary-text.q-pb-6.text-capitalize User feedback
            .row
              .km-label.text-capitalize {{ message?.feedback?.type || '-' }}
          .col-6
            .km-description.text-secondary-text.q-pb-6.text-capitalize Feedback reason
            .row
              .km-label.text-capitalize {{ feedbackReason }}
          .col-6
            .km-description.text-secondary-text.q-pb-6.text-capitalize User comment
            .row
              .km-label {{ message?.feedback?.comment || '-' }}
          .col-6
            .km-description.text-secondary-text.q-pb-6.text-capitalize Copied
            .row
              .km-label {{ message?.copied ? 'Yes' : 'No' }}
        template(v-if='tab == "insights"')
          .km-button-text.bb-border.q-pb-4 Substandard Result analysis
          .col-6
            .km-description.text-secondary-text Substandard Result Reason
            .row
              km-select.full-width(v-model='resultReason', :options='substandartResultReasons')
          .col-6
            .km-description.text-secondary-text Comment
            .row
              km-input.full-width.q-pb-16(autogrow, :rows='3', type='textarea', v-model='comment')
        .column.q-gap-16(v-if='tab === "costs-latency"')

        .column.q-gap-16(v-if='tab === "steps"')
          q-timeline
            agents-timeline-step(v-for='(step, index) in selectedMessagePrepared', :key='`${message.id}-${index}`', :step='step', :index='index')
  q-separator
  .row.items-center.q-pa-16.justify-between.bt-border(v-if='selectedRow?.trace_id || isUpdated')
    .row.items-center.q-gap-8.cursor-pointer(@click='openDetails', v-if='selectedRow?.trace_id')
      km-btn(flat, label='View trace', icon='fa fa-external-link', color='secondary-text', labelClass='km-button-text', iconSize='16px')

    .col-auto
    .row.items-center.q-gap-8
      km-btn.self-end(label='Cancel', @click='cancelUpdate', v-if='isUpdated', flat)
      km-btn.self-end(label='Update', @click='updateMessage', v-if='isUpdated', :loading='loading', :disable='loading')
</template>

<script>
import _ from 'lodash'
import { formatDateTime } from '@shared/utils/dateTime'
import { fetchData } from '@shared'

export default {
  props: ['message', 'conversation'],
  emits: ['close', 'update:message'],
  data() {
    return {
      tab: 'details',
      tabs: [
        {
          name: 'details',
          label: 'Message details',
        },
        // {
        //   name: 'costs-latency',
        //   label: 'Costs & Latency',
        // },
        {
          name: 'steps',
          label: 'Steps',
        },
        {
          name: 'insights',
          label: 'Insights',
        },
      ],
      substandartResultReasons: [
        { label: 'User input issue', value: 'user_input_issue' },
        { label: 'Topic selection issue', value: 'topic_selection_issue' },
        { label: 'Action selection issue', value: 'action_selection_issue' },
        { label: 'Action execution issue', value: 'action_execution_issue' },
        { label: 'Other', value: 'other' },
      ],
      custom_feedback: this.message?.custom_feedback ? { ...this.message.custom_feedback } : { reason: '', comment: '' },
      loading: false,
    }
  },
  computed: {
    isUpdated() {
      return !_.isEqual(this.custom_feedback, this.message?.custom_feedback || { reason: '', comment: '' })
    },
    resultReason: {
      get() {
        return this.custom_feedback?.reason ? this.substandartResultReasons.find((reason) => reason.value === this.custom_feedback.reason) || '' : ''
      },
      set(value) {
        this.custom_feedback = { ...this.custom_feedback, reason: value.value }
        // Optionally emit to parent:
        // this.$emit('update:message', { ...this.message, custom_feedback: { ...this.custom_feedback } })
      },
    },
    comment: {
      get() {
        return this.custom_feedback?.comment || ''
      },
      set(value) {
        this.custom_feedback = { ...this.custom_feedback, comment: value }
        // Optionally emit to parent:
        // this.$emit('update:message', { ...this.message, custom_feedback: { ...this.custom_feedback } })
      },
    },
    time() {
      if (this.message?.created_at) {
        return formatDateTime(this.message?.created_at)
      }
      return '-'
    },
    selectedMessagePrepared() {
      if (!this.message) return null
      const object = _.cloneDeep(this.message)

      return object?.run?.steps.map((step) => {
        const startTime = new Date(step.started_at)
        const endTime = new Date(step.completed_at)
        const duration = this.formatDelay(endTime - startTime)

        return {
          type: step.type,
          detailsJSON: JSON.stringify(step[step.type] || {}, null, 2),
          details: step?.details || {},
          started_at: startTime.toLocaleString(),
          completed_at: endTime.toLocaleString(),
          duration_seconds: duration,
          icon: step.type === 'classification' ? 'fas fa-layer-group' : step.type === 'topic_completion' ? 'fas fa-microchip' : 'fas fa-code',
          typeLabel: step.type === 'classification' ? 'Classification' : step.type === 'topic_completion' ? 'Topic Completion' : 'Topic Action Call',
        }
      })
    },
    responseTime() {
      if (this.message?.run?.steps?.length) {
        const firstStep = this.message?.run?.steps[0]?.started_at
        const lastStep = this.message?.run?.steps[this.message?.run?.steps.length - 1]?.completed_at
        const duration = new Date(lastStep) - new Date(firstStep)
        return this.formatDelay(duration)
      }
      return '-'
    },
    topic() {
      if (!this.selectedMessagePrepared?.length) return '-'
      const topic = this.selectedMessagePrepared.find((step) => step.type === 'topic_completion')
      return topic?.details?.topic?.name
    },
    feedbackReason() {
      if (!this.message?.feedback?.reason) return '-'
      return this.message.feedback.reason.replace(/_/g, ' ').replace(/^\w/, (l) => l.toUpperCase())
    },
    endpoint() {
      return this.$store.getters.config.api.aiBridge?.urlAdmin
    },
  },
  watch: {
    message: {
      handler(newVal, oldVal) {
        if (newVal?.id !== oldVal?.id) {
          // this.tab = 'details'
        }
        // Update local custom_feedback when message changes
        this.custom_feedback = newVal?.custom_feedback ? { ...newVal.custom_feedback } : { reason: '', comment: '' }
      },
      deep: true,
      immediate: true,
    },
  },
  methods: {
    cancelUpdate() {
      this.custom_feedback = this.message?.custom_feedback ? { ...this.message.custom_feedback } : { reason: '', comment: '' }
    },
    async updateMessage() {
      if (this.loading) return
      this.loading = true
      try {
        const body = { ...this.custom_feedback }

        // conversation_id and message_id are assumed to be available in the component context
        const conversation_id = this.conversation?.id
        const message_id = this.message?.id

        if (!conversation_id || !message_id) {
          console.error('Conversation ID or Message ID is missing')
          this.loading = false
          return
        }

        const response = await fetchData({
          endpoint: this.endpoint,
          method: 'PUT',
          credentials: 'include',
          service: `observability/monitoring/conversation/${conversation_id}/messages/${message_id}/feedback_custom`,
          body: JSON.stringify(body),
        })

        if (response.ok) {
          // Update custom_feedback via emit instead of direct mutation
          this.$emit('update:message', { ...this.message, custom_feedback: { ...this.custom_feedback } })
        }
      } finally {
        this.loading = false
      }
    },
    formatDelay(milliseconds) {
      console.log(milliseconds)
      if (milliseconds < 1000) {
        return new Intl.NumberFormat(undefined, {
          style: 'unit',
          unit: 'millisecond',
          unitDisplay: 'short',
          maximumFractionDigits: 0,
        }).format(milliseconds)
      } else if (milliseconds < 60000) {
        const seconds = milliseconds / 1000
        return new Intl.NumberFormat(undefined, {
          style: 'unit',
          unit: 'second',
          unitDisplay: 'short',
          maximumFractionDigits: 2,
          minimumFractionDigits: 2,
        }).format(seconds)
      } else {
        const minutes = Math.floor(milliseconds / 60000)
        const remainingMs = milliseconds % 60000
        let seconds = Math.floor(remainingMs / 1000)
        seconds = seconds < 10 ? `0${seconds}` : seconds
        return `${minutes}m${seconds}s`
      }
    },
  },
}
</script>
