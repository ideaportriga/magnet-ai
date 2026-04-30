<template>
  <layouts-details-layout>
    <template #header>
      <div class="cluster full-width bg-white border-radius-8" data-gap="md" data-wrap="no">
        <div class="flex-1 full-width">
          <div class="flex-none">
            <div class="cluster mb-xs" data-gap="md">
              <div class="km-heading-7 text-black">{{ title }}</div>
              <div class="km-space" />
            </div>
          </div>
          <div class="cluster pb-lg" data-gap="lg">
            <div class="cluster" data-gap="xs">
              <div class="km-field text-secondary-text">Start time</div>
              <div class="km-field text-black">{{ time.start }}</div>
            </div>
            <div class="cluster" data-gap="xs">
              <div class="km-field text-secondary-text">End time</div>
              <div class="km-field text-black">{{ time.end }}</div>
            </div>
          </div>
          <div class="cluster full-width" data-gap="md" data-justify="between">
            <div class="flex-1 bg-white ba-border border-radius-8 py-xs px-sm">
              <div class="text-weight-medium pb-sm conversation-page__stat-label">Duration</div>
              <div class="text-primary text-weight-medium conversation-page__stat-value">{{ duration }}</div>
            </div>
            <div class="flex-1 bg-white ba-border border-radius-8 py-xs px-sm">
              <div class="text-weight-medium pb-sm conversation-page__stat-label">Total Cost</div>
              <div class="text-primary text-weight-medium conversation-page__stat-value">$ {{ totalCost }}</div>
            </div>
            <div class="flex-1 bg-white ba-border border-radius-8 py-xs px-sm">
              <div class="text-weight-medium pb-sm conversation-page__stat-label">Status</div>
              <div class="cluster" data-gap="xs">
                <km-chip class="text-text-grey text-capitalize" :label="status" tone="neutral" round />
              </div>
            </div>
            <div class="flex-1 bg-white ba-border border-radius-8 py-xs px-sm">
              <div class="text-weight-medium pb-sm conversation-page__stat-label">Resolution</div>
              <km-chip v-if="resolution" class="text-capitalize" :label="resolutionStatusChip.label" :tone="resolutionStatusChip.tone" round />
            </div>
          </div>
        </div>
      </div>
    </template>
    <template #content>
      <div class="stack px-lg conversation-page__viewport" data-gap="0">
        <km-scroll-area class="fit">
          <div class="stack px-lg" data-gap="lg">
            <template v-for="(message, index) in allMessages" :key="index">
              <agent-message v-if="message?.role === &quot;user&quot; || message?.role === &quot;assistant&quot;" :key="index" :message="message" :next-message="message.action_call_requests?.length &gt; 0 ? allMessages[index + 1] : null" :last-message="true" :feedback="message.feedback" :is-disabled="true" :is-selected="selectedMessage?.id === message.id" @click="messageSelected(message)" @select="messageSelected(message)" />
            </template>
          </div>
        </km-scroll-area>
      </div>
    </template>
    <template #drawer>
      <conversation-drawer v-if="!selectedMessage" :conversation="conversation" @close="getConversation()" />
      <conversation-message-drawer v-else :message="selectedMessage" :conversation="conversation" @close="selectedMessage = null" />
    </template>
  </layouts-details-layout>
  <km-inner-loading :showing="loading" />
</template>
<script>
import { formatDateTime } from '@shared/utils/dateTime'
import { m } from '@/paraglide/messages'
import { formatDuration } from '@shared/utils'
import { useConversationStore } from '@/stores/conversationStore'
import { storeToRefs } from 'pinia'

import { ref } from 'vue'
export default {
  setup() {
    const selectedMessage = ref(null)
    const convStore = useConversationStore()
    const { conversation, loading } = storeToRefs(convStore)
    return {
      m,
      selectedMessage,
      loading,
      conversation,
      convStore,
    }
  },
  computed: {
    conversationId() {
      return this.$route.params.id
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
      if (this.resolution === 'resolved') return { tone: 'success', label: 'Resolved' }
      if (this.resolution === 'not_resolved') return { tone: 'danger', label: 'Not resolved' }
      return { tone: 'neutral', label: 'Transferred' }
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
      // Guard against navigating to /conversation without an id, or
      // against the route param resolving to the literal string
      // "undefined" (which happens when a caller interpolates an
      // undefined value into the URL). Either would hit the backend as
      // GET /agents/conversations/undefined and 500 on an invalid UUID
      // cast, spamming the observability logs.
      const id = this.conversationId
      if (!id || id === 'undefined' || id === 'null') return
      await this.convStore.getConversation({ conversation_id: id })
    },
    messageSelected(message) {
      if (message.role === 'user') return
      this.selectedMessage = message
    },
  },
}
</script>

<style scoped>
.conversation-page__stat-label {
  font-size: var(--ds-font-size-xs);
}

.conversation-page__stat-value {
  font-size: var(--ds-font-size-body-lg);
}

.conversation-page__viewport {
  block-size: 100vb;
}
</style>
