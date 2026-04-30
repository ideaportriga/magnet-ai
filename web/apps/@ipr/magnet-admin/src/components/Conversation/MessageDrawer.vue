<template>
  <km-drawer-layout storage-key="drawer-conversation-message">
    <template #tabs>
      <div class="cluster px-lg py-sm" data-wrap="no">
        <div class="cluster cursor-pointer" data-gap="sm" @click="$emit(&quot;close&quot;)">
          <km-glyph name="arrow-left" size="14px" />
          <div class="km-title text-secondary-text">{{ m.conversation_backToConversation() }}</div>
        </div>
      </div>
      <div class="bb-border" />
      <div class="cluster px-lg py-sm" data-wrap="no">
        <km-tabs v-model="tab" narrow-indicator dense align="left" no-caps content-class="km-tabs-dense">
          <template v-for="t in tabs" :key="t">
            <km-tab :name="t.name" :label="t.label" />
          </template>
          <div class="fit" />
        </km-tabs>
      </div>
    </template>
    <div class="stack full-height" data-gap="lg">
      <div v-if="tab === &quot;details&quot;" class="stack" data-gap="lg">
        <div class="basis-6">
          <div class="km-description text-secondary-text pb-sm">Message Time</div>
          <div class="km-label">{{ time }}</div>
        </div>
        <div class="basis-6">
          <div class="km-description text-secondary-text pb-sm text-capitalize">Latency</div>
          <div class="km-label">{{ responseTime }}</div>
        </div>
        <div class="basis-6">
          <div class="km-description text-secondary-text pb-sm text-capitalize">Role</div>
          <div class="km-label text-capitalize">{{ message?.role }}</div>
        </div>
        <div class="basis-6">
          <div class="km-description text-secondary-text pb-sm text-capitalize">Agent Topic</div>
          <div class="km-label">{{ topic }}</div>
        </div>
        <div class="km-button-text bb-border pb-xs">User satisfaction</div>
        <div class="basis-6">
          <div class="km-description text-secondary-text pb-sm text-capitalize">User feedback</div>
          <div class="km-label text-capitalize">{{ message?.feedback?.type || '-' }}</div>
        </div>
        <div class="basis-6">
          <div class="km-description text-secondary-text pb-sm text-capitalize">Feedback reason</div>
          <div class="km-label text-capitalize">{{ feedbackReason }}</div>
        </div>
        <div class="basis-6">
          <div class="km-description text-secondary-text pb-sm text-capitalize">User comment</div>
          <div class="km-label">{{ message?.feedback?.comment || '-' }}</div>
        </div>
        <div class="basis-6">
          <div class="km-description text-secondary-text pb-sm text-capitalize">Copied</div>
          <div class="km-label">{{ message?.copied ? 'Yes' : 'No' }}</div>
        </div>
      </div>
      <template v-if="tab == &quot;insights&quot;">
        <div class="km-button-text bb-border pb-xs">Substandard Result analysis</div>
        <div class="basis-6">
          <div class="km-description text-secondary-text">Substandard Result Reason</div>
          <km-select v-model="resultReason" class="full-width" :options="substandartResultReasons" />
        </div>
        <div class="basis-6">
          <div class="km-description text-secondary-text">Comment</div>
          <km-input v-model="comment" class="full-width pb-lg" autogrow :rows="3" type="textarea" />
        </div>
      </template>
      <div v-if="tab === &quot;costs-latency&quot;" class="stack" data-gap="lg" />
      <div v-if="tab === &quot;steps&quot;" class="stack" data-gap="lg">
        <km-timeline>
          <agents-timeline-step v-for="(step, index) in selectedMessagePrepared" :key="`${message.id}-${index}`" :step="step" :index="index" />
        </km-timeline>
      </div>
    </div>
    <km-separator />
    <div v-if="selectedRow?.trace_id || isUpdated" class="cluster p-lg bt-border" data-justify="between">
      <div v-if="selectedRow?.trace_id" class="cluster cursor-pointer" data-gap="sm" @click="openDetails">
        <km-btn flat :label="m.conversation_viewTrace()" icon="external-link" tone="subtle" label-class="km-button-text" icon-size="16px" />
      </div>
      <div class="flex-none" />
      <div class="cluster" data-gap="sm">
        <km-btn v-if="isUpdated" class="self-end" :label="m.common_cancel()" flat @click="cancelUpdate" />
        <km-btn v-if="isUpdated" class="self-end" :label="m.common_update()" :loading="loading" :disable="loading" @click="updateMessage" />
      </div>
    </div>
  </km-drawer-layout>
</template>

<script>
import _ from 'lodash'
import { m } from '@/paraglide/messages'
import { formatDateTime } from '@shared/utils/dateTime'
import { fetchData } from '@shared'

export default {
  props: ['message', 'conversation'],
  emits: ['close', 'update:message'],
  // Expose the paraglide messages object to the template. Options API
  // does not auto-expose top-level imports; without this, every
  // `m.foo()` in the template dereferences `undefined` and throws
  // "Cannot read properties of undefined".
  setup() {
    return { m }
  },
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
          icon: step.type === 'classification' ? 'stack' : step.type === 'topic_completion' ? 'cpu' : 'code',
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
      return this.$appConfig.api.aiBridge?.urlAdmin
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
