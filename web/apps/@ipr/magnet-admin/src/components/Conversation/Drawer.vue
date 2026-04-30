<template>
  <km-drawer-layout storage-key="drawer-conversation">
    <template #tabs>
      <div class="pt-lg px-lg">
        <km-tabs v-model="tab" class="bb-border full-width" narrow-indicator dense align="left" no-caps content-class="km-tabs">
          <template v-for="t in tabs" :key="t">
            <km-tab :name="t.name" :label="t.label" />
          </template>
          <div class="fit" />
        </km-tabs>
      </div>
    </template>
    <div v-if="tab === &quot;details&quot;" class="stack" data-gap="lg">
      <div class="basis-6">
        <div class="km-description text-secondary-text pb-sm">Agent Name</div>
        <div class="cluster" data-gap="lg">
          <div class="km-label">{{ analytics.feature_name }}</div>
          <km-glyph v-if="analytics?.feature_id" class="cursor-pointer" name="external-link" size="10" @click="openAgent" />
          <km-chip class="text-grey" :label="variant" tone="neutral" round />
        </div>
      </div>
      <div class="basis-6">
        <div class="km-description text-secondary-text pb-sm">Consumer type</div>
        <div class="cluster" data-gap="sm">
          <div class="km-label">{{ analytics?.source ?? '-' }}</div>
        </div>
      </div>
      <div class="basis-6">
        <div class="km-description text-secondary-text pb-sm">Start Time</div>
        <div class="km-field text-black">{{ formatDateTime(analytics.start_time) }}</div>
      </div>
      <div class="basis-6">
        <div class="km-description text-secondary-text pb-sm">End Time</div>
        <div class="km-field text-black">{{ formatDateTime(analytics.end_time) }}</div>
      </div>
      <div class="basis-6">
        <div class="km-description text-secondary-text pb-sm">Duration</div>
        <div class="km-field text-black">{{ duration }}</div>
      </div>
      <div class="basis-6">
        <div class="km-description text-secondary-text pb-sm">Total Assistant Messages</div>
        <div class="km-field text-black">{{ assistantMessagesCount }}</div>
      </div>
    </div>
    <div v-if="tab === &quot;costs&quot;" class="stack" data-gap="lg">
      <div class="basis-6">
        <div class="km-description text-secondary-text pb-sm">Total Agent messages cost</div>
        <div class="km-field text-black">{{ totalCost }} $</div>
      </div>
      <div class="basis-6">
        <div class="km-description text-secondary-text pb-sm">Average latency</div>
        <div class="km-field text-black">{{ analytics?.conversation_data?.avg_tool_call_latency ? formatDuration(analytics?.conversation_data?.avg_tool_call_latency) : '-' }}</div>
      </div>
    </div>
    <div v-if="tab === &quot;insights&quot;" class="stack" data-gap="lg">
      <div class="km-button-text bb-border pb-xs">Agent Processing</div>
      <div class="basis-6">
        <div class="km-description text-secondary-text pb-sm">Agent topics</div>
        <div class="km-field text-black">{{ topics }}</div>
      </div>
      <div class="km-button-text bb-border pb-xs">Post-processing results</div>
      <div class="basis-6">
        <div class="km-description text-secondary-text">Resolution status</div>
        <km-select v-model="resolution" class="full-width" :options="statusOptions" />
      </div>
      <div class="basis-6">
        <div class="km-description text-secondary-text">Final sentiment</div>
        <km-select v-model="sentiment" class="full-width" :options="sentimentOptions" />
      </div>
      <div class="basis-6">
        <div class="km-description text-secondary-text pb-sm">Language</div>
        <km-input v-model="analytics.conversation_data.language" class="full-width" />
      </div>
      <div class="km-button-text bb-border pb-xs">User satisfaction</div>
      <div class="basis-6">
        <div class="km-description text-secondary-text pb-sm">User feedback</div>
        <div class="km-field text-black">{{ feedback }}</div>
      </div>
      <div class="basis-6">
        <div class="km-description text-secondary-text pb-sm">Copied</div>
        <div class="km-field text-black">{{ analytics?.extra_data?.answer_copy ? 'Yes' : 'No' }}</div>
      </div>
      <div class="km-button-text bb-border pb-xs">Substandard Result analysis</div>
      <div class="basis-6">
        <div class="km-description text-secondary-text">Substandard Result Reason</div>
        <km-select v-model="resultReason" class="full-width" :options="substandartResultReasons" />
      </div>
      <div class="basis-6">
        <div class="km-description text-secondary-text">Comment</div>
        <km-input v-model="comment" class="full-width pb-lg" autogrow :rows="3" type="textarea" />
      </div>
    </div>
    <div class="cluster p-lg bt-border relative" data-justify="between" style="z-index: 10">
      <div v-if="conversation?.trace_id" class="cluster cursor-pointer" data-gap="sm" @click="openDetails">
        <km-btn flat :label="m.conversation_viewTrace()" icon="external-link" tone="subtle" label-class="km-button-text" icon-size="16px" />
      </div>
      <div class="flex-none" />
      <div class="cluster" data-gap="sm">
        <km-btn v-if="isUpdated" class="self-end" :label="m.common_cancel()" flat @click="cancelUpdate" />
        <km-btn v-if="isUpdated" class="self-end" :label="m.common_update()" @click="updateAnalytics" />
      </div>
    </div>
    <km-inner-loading :showing="loading" />
  </km-drawer-layout>
</template>

<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { formatDateTime } from '@shared/utils/dateTime'
import { formatDuration } from '@shared/utils'
import _ from 'lodash'
import { fetchData } from '@shared'
export default {
  props: {
    // Allow null: the parent page may mount this drawer before the
    // conversation is loaded. Template already uses `?.` on every
    // access, so null is the intended "not yet loaded" state.
    conversation: {
      type: Object,
      required: false,
      default: null,
    },
  },
  emits: ['close'],

  setup() {
    const closeLoading = ref(false)
    const loading = ref(false)
    const item = ref(null)
    return {
      m,
      tab: ref('details'),
      tabs: ref([
        { name: 'details', label: m.conversation_conversationDetails() },
        { name: 'costs', label: m.conversation_costAndLatency() },
        { name: 'insights', label: m.conversation_insights() },
      ]),
      statusOptions: ref([
        { label: 'Resolved', value: 'resolved' },
        { label: 'Not resolved', value: 'not_resolved' },
        { label: 'Transferred to human', value: 'transferred' },
      ]),
      sentimentOptions: ref([
        { label: 'Positive', value: 'positive' },
        { label: 'Negative', value: 'negative' },
        { label: 'Neutral', value: 'neutral' },
      ]),

      substandartResultReasons: ref([
        { label: 'User input issue', value: 'user_input_issue' },
        { label: 'Topic selection issue', value: 'topic_selection_issue' },
        { label: 'Action selection issue', value: 'action_selection_issue' },
        { label: 'Action execution issue', value: 'action_execution_issue' },
        { label: 'Other', value: 'other' },
      ]),
      formatDateTime,
      formatDuration,
      closeLoading,
      loading,
      item,
    }
  },

  computed: {
    resultReason: {
      get() {
        if (this.analytics.conversation_data?.substandart_result_reason) {
          return this.substandartResultReasons.find((option) => option.value === this.analytics.conversation_data?.substandart_result_reason)
        }
        return '-'
      },
      set(value) {
        this.analytics.conversation_data.substandart_result_reason = value.value
      },
    },
    comment: {
      get() {
        return this.analytics.conversation_data?.comment ?? ''
      },
      set(value) {
        this.analytics.conversation_data.comment = value
      },
    },
    sentiment: {
      get() {
        return (
          this.sentimentOptions.find((option) => option.value === this.analytics.conversation_data?.sentiment) ??
          this.analytics.conversation_data?.sentiment
        )
      },
      set(value) {
        this.analytics.conversation_data.sentiment = value.value
      },
    },
    resolution: {
      get() {
        return (
          this.statusOptions.find((option) => option.value === this.analytics.conversation_data?.resolution_status) ??
          this.analytics.conversation_data?.resolution_status
        )
      },
      set(value) {
        this.analytics.conversation_data.resolution_status = value.value
      },
    },
    variant() {
      if (!this.conversation?.analytics?.feature_variant) return '-'
      return this.conversation.analytics.feature_variant.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())
    },
    analytics() {
      return this.item?.analytics ?? {}
    },
    recountFeedback() {
      const messages = this.conversation?.messages ?? []
      const messages_with_feedback = messages.filter((message) => message.feedback)
      const likes = messages_with_feedback.filter((message) => message.feedback.type === 'like').length
      const dislikes = messages_with_feedback.filter((message) => message.feedback.type === 'dislike').length
      return { likes, dislikes }
      // return messages.filter((message) => message.feedback)
    },
    feedback() {
      let title = ''
      const likes = this.recountFeedback.likes //this.analytics.conversation_data?.likes
      const dislikes = this.recountFeedback.dislikes //this.analytics.conversation_data?.dislikes
      if (likes >= 0) {
        title += likes
        title += likes === 1 ? ' like' : ' likes'
        if (dislikes !== null) title += ', '
      }
      if (dislikes >= 0) {
        title += dislikes
        title += dislikes === 1 ? ' dislike' : ' dislikes'
      }
      if (title === '') return '-'
      return title
    },
    topics() {
      return this.analytics.conversation_data?.topics?.length > 0 ? this.analytics.conversation_data?.topics?.join(', ') : '-'
    },
    totalCost() {
      if (!this.conversation?.analytics?.cost) return '-'
      return this.conversation?.analytics?.cost.toFixed(6)
    },
    duration() {
      return formatDuration(this.analytics?.latency)
    },
    isUpdated() {
      return !_.isEqual(this.conversation, this.item)
    },
    endpoint() {
      return this.$appConfig.api.aiBridge.urlAdmin
    },
    assistantMessagesCount() {
      return this.conversation?.messages?.filter((message) => message.role === 'assistant').length || '-'
    },
  },
  watch: {
    conversation: {
      handler(newVal) {
        this.item = _.cloneDeep(newVal)
      },
      immediate: true,
    },
  },
  methods: {
    openAgent() {
      this.$router.push(`/agents/${this.analytics?.feature_id}`)
    },

    cancelUpdate() {
      this.item = _.cloneDeep(this.conversation)
    },
    async updateAnalytics() {
      const body = {
        conversation_data: {},
      }
      const itemData = this.item.analytics.conversation_data
      const conversationData = this.conversation.analytics.conversation_data

      if (itemData.resolution_status !== conversationData.resolution_status) {
        body.conversation_data.resolution_status = itemData.resolution_status
      }
      if (itemData.sentiment !== conversationData.sentiment) {
        body.conversation_data.sentiment = itemData.sentiment
      }
      if (itemData.language !== conversationData.language) {
        body.conversation_data.language = itemData.language
      }

      if (itemData.substandart_result_reason !== conversationData.substandart_result_reason) {
        body.conversation_data.substandart_result_reason = itemData.substandart_result_reason
      }
      if (itemData.comment !== conversationData.comment) {
        body.conversation_data.comment = itemData.comment
      }
      const response = await fetchData({
        endpoint: this.endpoint,
        method: 'PUT',
        credentials: 'include',
        service: `observability/monitoring/analytics/${this.analytics._id}`,
        body: JSON.stringify(body),
      })
      if (response.ok) {
        const data = await response.json()
        this.$emit('close')
      }
    },
    openDetails() {
      this.$router.push(`/observability-traces/${this.conversation.trace_id.substring(8)}`)
    },
  },
}
</script>
