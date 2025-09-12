<template lang="pug">
layouts-details-layout
  template(#header)
    .row.items-center.q-gap-12.no-wrap.full-width.bg-white.border-radius-8
      .col.full-width
        .col-auto
          .row.items-center.q-gap-12.q-mb-xs
            .km-heading-7.text-black {{ title }}
            q-space 
            //- km-chip.text-text-grey(label='Email', color='in-progress', round)
        .row.q-gap-16.q-pb-16
          .row.items-center.q-gap-4
            .km-field.text-secondary-text Start time
            .km-field.text-black {{ time.start }}
          .row.items-center.q-gap-4
            .km-field.text-secondary-text End time
            .km-field.text-black {{ time.end }}

        .row.justify-between.q-gap-12.full-width
          .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm
            .text-weight-medium.q-pb-8(style='font-size: 12px') Duration
            .text-primary.text-weight-medium(style='font-size: 16px') {{ duration }}
          .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm
            .text-weight-medium.q-pb-8(style='font-size: 12px') Total Cost
            .text-primary.text-weight-medium(style='font-size: 16px') $ {{ totalCost }}
          .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm
            .text-weight-medium.q-pb-8(style='font-size: 12px') Status
            .row.items-center.q-gap-4
              km-chip.text-text-grey.text-capitalize(:label='status', color='in-progress', round)
              //- km-chip.text-text-grey(label='In Progress', color='in-progress', round)
          .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm
            .text-weight-medium.q-pb-8(style='font-size: 12px') Resolution
            km-chip.text-capitalize(
              :label='resolutionStatusChip.label',
              :color='resolutionStatusChip.color',
              :class='resolutionStatusChip.text',
              round,
              v-if='resolution'
            )
          //- .col.bg-white.ba-border.border-radius-8.q-py-xs.q-px-sm
          //-   .text-weight-medium.q-pb-8(style='font-size: 12px') Language
          //-   km-chip.text-text-grey.text-capitalize(:label='language', color='in-progress', round, v-if='language')
  template(#content)
    .column.no-wrap.q-px-16.q-gap-(style='height: 100vh')
      q-scroll-area.fit
        .column.no-wrap.q-px-16.q-gap-16
          template(v-for='(message, index) in allMessages')
            agent-message(
              v-if='message?.role === "user" || message?.role === "assistant"',
              :message='message',
              :nextMessage='message.action_call_requests?.length > 0 ? allMessages[index + 1] : null',
              :key='index',
              :lastMessage='true',
              :feedback='message.feedback',
              :isDisabled='true',
              :isSelected='selectedMessage?.id === message.id',
              @click='messageSelected(message)',
              @select='messageSelected(message)'
            )
  template(#drawer)
    conversation-drawer(v-if='!selectedMessage', :conversation='conversation', @close='getConversation()')
    conversation-message-drawer(:message='selectedMessage', :conversation='conversation', v-else, @close='selectedMessage = null')
q-inner-loading(:showing='loading', color='primary')
</template>
<script>
import { fetchData } from '@shared'
import { formatDateTime } from '@shared/utils/dateTime'
import { formatDuration } from '@shared/utils'

import { ref } from 'vue'
export default {
  setup() {
    const selectedMessage = ref(null)
    //const conversation = ref(null)
    const loading = ref(false)
    return {
      selectedMessage,
      loading,
    }
  },
  computed: {
    conversation() {
      return this.$store.getters.conversation
    },
    conversationId() {
      return this.$route.params.id
    },
    endpoint() {
      return this.$store.getters.config.api.aiBridge.urlAdmin
    },
    title() {
      const name = this.conversation?.analytics?.feature_name
      const date = formatDateTime(this.conversation?.created_at)
      return `${name} ${date}`
    },
    duration() {
      return formatDuration(this.conversation?.analytics?.latency)
    },
    totalCost() {
      if (!this.conversation?.analytics?.cost) return '-'
      return this.conversation?.analytics?.cost.toFixed(6)
    },
    status() {
      return this.conversation?.analytics?.extra_data?.status ?? '-'
    },
    resolutionStatusChip() {
      if (!this.conversation?.analytics?.conversation_data?.resolution_status) return ''
      if (this.resolution === 'resolved') return { color: 'like-bg', label: 'Resolved', text: 'text-like-text' }
      if (this.resolution === 'not_resolved') return { color: 'error-bg', label: 'Not resolved', text: 'text-error-text' }
      return { color: 'in-progress', label: 'Transferred', text: 'text-text-grey' }
    },
    resolution() {
      return this.conversation?.analytics?.conversation_data?.resolution_status ?? '-'
    },
    language() {
      return this.conversation?.analytics?.conversation_data?.language ?? '-'
    },
    allMessages() {
      return this.conversation?.messages
    },
    time() {
      return {
        start: formatDateTime(this.conversation?.analytics?.start_time),
        end: formatDateTime(this.conversation?.analytics?.end_time),
      }
    },
  },
  watch: {
    conversationId: {
      handler() {
        this.getConversation()
      },
      immediate: true,
    },
  },
  methods: {
    async getConversation() {
      this.loading = true
      try {
        await this.$store.dispatch('getConversation', {
          conversation_id: this.conversationId,
        })
      } finally {
        this.loading = false
      }
    },
    messageSelected(message) {
      if (message.role === 'user') return
      this.selectedMessage = message
    },
  },
}
</script>
