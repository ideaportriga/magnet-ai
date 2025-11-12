<template lang="pug">
.column.bg-white.fit.bl-border.height-100.fit(style='min-width: 500px; max-width: 500px')
  .col.q-pt-16
    .row.no-wrap.full-width.q-px-16
      q-tabs.bb-border.full-width(
        v-model='tab',
        narrow-indicator,
        dense,
        align='left',
        active-color='primary',
        indicator-color='primary',
        active-bg-color='white',
        no-caps,
        content-class='km-tabs'
      )
        template(v-for='t in tabs')
          q-tab(:name='t.name', :label='t.label')
        .fit
    .column.q-px-8.no-wrap.fit
      q-scroll-area.fit
        .column.full-height.q-py-16.q-px-16.q-gap-16
          .column.q-gap-16(v-if='tab === "details"')
            .col-6
              .km-description.text-secondary-text.q-pb-6 Agent Name
              .row.q-gap-16.items-center
                .km-label {{ analytics.feature_name }}
                q-icon.cursor-pointer(name='fa fa-external-link', color='secondary', size='10', @click='openAgent', v-if='analytics?.feature_id')
                km-chip.text-grey(:label='variant', color='in-progress', round)
            .col-6
              .km-description.text-secondary-text.q-pb-6 Consumer type
              .row.q-gap-8.items-center
                .km-label {{ analytics?.source ?? '-' }}
            .col-6
              .km-description.text-secondary-text.q-pb-6 Start Time
              .km-field.text-black {{ formatDateTime(analytics.start_time) }}
            .col-6
              .km-description.text-secondary-text.q-pb-6 End Time
              .km-field.text-black {{ formatDateTime(analytics.end_time) }}
            .col-6
              .km-description.text-secondary-text.q-pb-6 Duration
              .km-field.text-black {{ duration }}
            .col-6
              .km-description.text-secondary-text.q-pb-6 Total Assistant Messages
              .km-field.text-black {{ assistantMessagesCount }}

          .column.q-gap-16(v-if='tab === "costs"')
            .col-6
              .km-description.text-secondary-text.q-pb-6 Total Agent messages cost
              .km-field.text-black {{ totalCost }} $
            .col-6
              .km-description.text-secondary-text.q-pb-6 Average latency
              .km-field.text-black {{ analytics?.conversation_data?.avg_tool_call_latency ? formatDuration(analytics?.conversation_data?.avg_tool_call_latency) : '-' }}

          .column.q-gap-16(v-if='tab === "insights"')
            .km-button-text.bb-border.q-pb-4 Agent Processing
            .col-6
              .km-description.text-secondary-text.q-pb-6 Agent topics
              .km-field.text-black {{ topics }}
            .km-button-text.bb-border.q-pb-4 Post-processing results
            .col-6
              .km-description.text-secondary-text Resolution status
              .row
                km-select.full-width(v-model='resolution', :options='statusOptions')
            .col-6
              .km-description.text-secondary-text Final sentiment
              .row
                km-select.full-width(v-model='sentiment', :options='sentimentOptions')
            .col-6
              .km-description.text-secondary-text.q-pb-6 Language
              .row
                km-input.full-width(v-model='analytics.conversation_data.language')
            .km-button-text.bb-border.q-pb-4 User satisfaction
            .col-6
              .km-description.text-secondary-text.q-pb-6 User feedback
              .km-field.text-black {{ feedback }}
            .col-6
              .km-description.text-secondary-text.q-pb-6 Copied
              .km-field.text-black {{ analytics?.extra_data?.answer_copy ? 'Yes' : 'No' }}
            .km-button-text.bb-border.q-pb-4 Substandard Result analysis
            .col-6
              .km-description.text-secondary-text Substandard Result Reason
              .row
                km-select.full-width(v-model='resultReason', :options='substandartResultReasons')
            .col-6
              .km-description.text-secondary-text Comment
              .row
                km-input.full-width.q-pb-16(autogrow, :rows='3', type='textarea', v-model='comment')
  .row.items-center.q-pa-16.justify-between.bt-border.relative(style='z-index: 10')
    .row.items-center.q-gap-8.cursor-pointer(@click='openDetails', v-if='conversation?.trace_id')
      km-btn(flat, label='View trace', icon='fa fa-external-link', color='secondary-text', labelClass='km-button-text', iconSize='16px')
    .col-auto
    .row.items-center.q-gap-8
      km-btn.self-end(label='Cancel', @click='cancelUpdate', v-if='isUpdated', flat)
      km-btn.self-end(label='Update', @click='updateAnalytics', v-if='isUpdated')

  q-inner-loading(:showing='loading')
</template>

<script>
import { ref } from 'vue'
import { formatDateTime } from '@shared/utils/dateTime'
import { formatDuration } from '@shared/utils'
import _ from 'lodash'
import { fetchData } from '@shared'
export default {
  props: {
    conversation: {
      type: Object,
      required: true,
    },
  },
  emits: ['close'],

  setup() {
    const closeLoading = ref(false)
    const loading = ref(false)
    const item = ref(null)
    return {
      tab: ref('details'),
      tabs: ref([
        { name: 'details', label: 'Conversation Details' },
        { name: 'costs', label: 'Cost & Latency' },
        { name: 'insights', label: 'Insights' },
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
      return this.$store.getters.config.api.aiBridge.urlAdmin
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
      window.open(this.$router.resolve({ path: `/agents/${this.analytics?.feature_id}` }).href, '_blank')
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
        console.log(data)
        this.$emit('close')
      }
    },
    openDetails() {
      window.open(this.$router.resolve({ path: `/observability-traces/${this.conversation.trace_id.substring(8)}` }).href, '_blank')
    },
  },
}
</script>
