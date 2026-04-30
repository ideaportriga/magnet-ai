<template>
  <km-drawer-layout storage-key="drawer-agents-preview" :default-width="500" :max-width="1200" no-scroll>
    <template #header>
      <div class="cluster" data-justify="between">
        <div class="km-field text-secondary-text" />
        <div v-if="selectedMessage" class="ml-sm">
          <km-btn icon="close" flat dense @click="selectedMessage = null" />
        </div>
      </div>
      <div class="km-heading-7">{{ m.agents_agentPreview() }}</div>
    </template>
    <div class="cluster full-height" data-wrap="no" data-align="stretch">
      <div v-if="selectedMessage" class="flex-1 full-height overflow-hidden">
        <div class="stack full-height" data-gap="0">
          <div class="flex-1 min-h-0">
            <div class="stack full-height" data-gap="0">
              <div class="full-height stack pl-sm agents-drawer-preview__steps-scroll" data-gap="0">
                <km-timeline>
                  <km-timeline-entry v-for="(step, index) in selectedMessagePrepared" :key="step.started_at" :icon="step.icon" :tone="expandedStep[index] ? &quot;success&quot; : &quot;brand&quot;">
                    <template #subtitle>
                      <div class="cluster agents-drawer-preview__step-row" data-justify="between">
                        <div class="flex-1 mr-md">
                          <km-chip label-class="km-heading-2" flat dense icon-size="16px" @click="step.type === &quot;classification&quot; || (step.type === &quot;topic_completion&quot; &amp;&amp; !step?.details?.action_call_requests) ? null : toggleExpand(index)">
                            <div class="cluster" data-justify="center">
                              <km-glyph v-if="!(step.type === &quot;classification&quot; || (step.type === &quot;topic_completion&quot; &amp;&amp; !step?.details?.action_call_requests))" name="chevron-right" flat class="agents-drawer-preview__chevron" :data-expanded="expandedStep[index] ? 'true' : 'false'" />
                              <div class="ml-sm text-secondary-text cursor-pointer">{{ step?.typeLabel }}</div>
                            </div>
                          </km-chip>
                        </div>
                        <div class="flex-none mr-md km-field">{{ step?.duration_seconds }}</div>
                      </div>
                    </template>
                    <div class="stack" data-gap="sm">
                      <template v-if="step.type === &quot;classification&quot;">
                        <div class="flex-1">
                          <div class="cluster">
                            <div class="agents-drawer-preview__label flex-none mr-md">
                              <div class="km-field text-secondary-text">Intent</div>
                            </div>
                            <div class="flex-1 km-flex-min-w-0">
                              <km-chip :label="step.details.intent" tone="neutral" />
                            </div>
                          </div>
                        </div>
                        <div v-if="step.details?.topic" class="flex-1">
                          <div class="cluster">
                            <div class="agents-drawer-preview__label flex-none mr-md">
                              <div class="km-field text-secondary-text">Topic</div>
                            </div>
                            <div class="flex-1 km-flex-min-w-0">
                              <km-chip :label="step.details?.topic" tone="neutral" />
                            </div>
                          </div>
                        </div>
                        <div class="flex-1">
                          <div class="cluster">
                            <div class="flex-none mr-md">
                              <div class="km-field text-secondary-text">Reason</div>
                            </div>
                            <div class="flex-1 km-flex-min-w-0">{{ step.details.reason }}</div>
                          </div>
                        </div>
                      </template>
                      <template v-else-if="step.type === &quot;topic_completion&quot;">
                        <div class="flex-1">
                          <div class="cluster">
                            <div class="flex-none mr-md">
                              <div class="km-field text-secondary-text">Topic</div>
                            </div>
                            <div class="flex-1 km-flex-min-w-0">{{ step.details.topic.name }}</div>
                          </div>
                        </div>
                        <div class="flex-1">
                          <div class="cluster">
                            <div class="flex-none mr-md">
                              <div class="km-field text-secondary-text">Topic Description</div>
                            </div>
                            <div class="flex-1 km-flex-min-w-0">{{ step.details.topic.description }}</div>
                          </div>
                          <div v-if="step.details?.action_call_requests" class="mt-sm">
                            <km-slide-transition>
                              <div v-if="step.details?.action_call_requests &amp;&amp; expandedStep[index]" class="mt-sm">
                                <div v-for="(rq, rqIndex) in step.details.action_call_requests" :key="rqIndex" class="text-secondary-text">
                                  <div class="cluster mb-sm">
                                    <km-chip :label="rq.action_type" tone="neutral" />
                                    <div class="ml-sm">{{ rq.function_name }}</div>
                                  </div>
                                  <div class="km-field text-secondary-text">Request</div>
                                  <km-codemirror :model-value="stringify(rq.arguments)" readonly class="agents-drawer-preview__codemirror--md" />
                                </div>
                              </div>
                            </km-slide-transition>
                          </div>
                        </div>
                      </template>
                      <template v-else-if="step.type === &quot;topic_action_call&quot;">
                        <div v-if="step.details" class="mt-sm">
                          <div class="text-secondary-text">
                            <div class="cluster mb-sm">
                              <km-chip :label="step.details.request.action_type" tone="neutral" />
                              <div class="ml-sm">{{ step.details.request.function_name }}</div>
                            </div>
                            <div v-if="step.details?.request &amp;&amp; !expandedStep[index]" class="km-field text-secondary-text">
                              Request
                              <km-codemirror :model-value="stringify(step.details.request.arguments)" readonly class="agents-drawer-preview__codemirror--sm" />
                            </div>
                          </div>
                        </div>
                        <div v-if="step.details">
                          <km-slide-transition>
                            <div v-if="step.details?.request &amp;&amp; expandedStep[index]">
                              <div class="km-field text-secondary-text">Request</div>
                              <km-codemirror :model-value="stringify(step?.details?.request)" readonly class="agents-drawer-preview__codemirror--md" />
                              <div class="km-field text-secondary-text">Response</div>
                              <km-codemirror :model-value="stringify(step?.details?.response)" readonly class="agents-drawer-preview__codemirror--md" />
                            </div>
                          </km-slide-transition>
                        </div>
                      </template>
                      <template v-else>
                        <km-codemirror v-model="step.detailsJSON" class="agents-drawer-preview__codemirror--lg" readonly />
                      </template>
                    </div>
                  </km-timeline-entry>
                </km-timeline>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="selectedMessage" class="flex-none">
        <div class="flex items-center full-height">
          <div class="bg-white agents-drawer-preview__divider" />
        </div>
      </div>
      <div class="flex-1 full-height">
        <div class="stack full-height" data-gap="0">
          <div class="flex-1 min-h-0">
            <div class="stack full-height" data-gap="0">
              <div ref="messagesContainer" class="full-height py-lg stack agents-drawer-preview__messages-scroll" data-gap="0">
                <template v-if="processing">
                  <div class="agents-drawer-preview__processing">
                    <km-loader size="62px" />
                    <km-btn flat simple :label="m.panel_stop()" icon-size="16px" icon="close" @click="abortController.abort()" />
                  </div>
                </template>
                <div class="stack px-lg" data-gap="sm" data-wrap="no">
                  <template v-for="(message, index) in allMessages" :key="index">
                    <agent-message v-if="showAllMessages || message?.role === &quot;user&quot; || message?.role === &quot;assistant&quot;" :is-selected="selectedMessage?.id === message?.id" :message="message" :preview-mode="true" :last-message="index === allMessages.length - 1" @copy="copyMessage(message)" @save="saveMessage(index)" @delete="deleteMessage(index)" @focus="message?.role === &quot;assistant&quot; ? (selectedMessage = message) : null" @confirm="confirmMessage($event)" />
                  </template>
                </div>
              </div>
              <agents-feedback-modal :feedback-modal="feedbackModal" :feedback-confirm-modal="feedbackConfirmModal" @update:feedback-modal="feedbackModal = $event" @update:feedback-confirm-modal="feedbackConfirmModal = $event" @submit="submitForm" />
              <div class="flex-none mt-md px-lg">
                <form @submit.prevent="sendUserMessage">
                  <km-input ref="input" data-test="preview-input" autogrow :rows="1" :min-rows="1" :max-rows="10" :placeholder="m.agents_typeYourQuestion()" :model-value="userMessage" border-radius="8px" height="36px" type="textarea" @input="userMessage = $event" @keydown.enter="handleUserMessageEnter">
                    <template #append>
                      <km-btn data-test="preview-btn" type="submit" size="icon-xs" icon="send" icon-size="16px" icon-tone="inverse" :disable="cantSendUserMessage" />
                    </template>
                  </km-input>
                  <template v-if="isShowHints">
                    <div class="cluster mt-sm">
                      <div class="flex-1 km-heading-3">{{ m.common_youCanAskLikeThis() }}</div>
                      <div class="flex-none">
                        <km-btn flat tone="brand" @click="showHints = false">
                          <div class="km-button-text">{{ m.common_dontShowHints() }}</div>
                        </km-btn>
                      </div>
                    </div>
                    <template v-for="(item, index) in sampleQuestion" :key="index">
                      <km-btn flat @click="refine(item)">
                        <div class="wrapped-text">{{ item }}</div>
                      </km-btn>
                    </template>
                  </template>
                  <div class="cluster py-md" data-justify="end">
                    <div class="flex-none">
                      <km-btn flat simple icon-size="16px" icon="redo" @click="clearChat" />
                    </div>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </km-drawer-layout>
</template>
<script>
import { copyToClipboard } from '@ds/utils/clipboard'
import _ from 'lodash'
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { fetchData } from '@shared'
import { useEntityQueries } from '@/queries/entities'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import { useAppStore } from '@/stores/appStore'
import { notify } from '@shared/utils/notify'

export default {
  props: {
    ragTools: {
      type: Array,
    },
    promptTemplate: {
      type: Array,
    },
    mockData: {
      type: String,
    },
    endUserMode: {
      type: String,
      default: 'false',
    },
  },
  setup(props) {
    const queries = useEntityQueries()
    const { data: ragData } = queries.rag_tools.useList()
    const ragList = computed(() => ragData.value?.items ?? [])
    const { data: promptTemplatesListData } = queries.promptTemplates.useList()
    const promptTemplatesList = computed(() => promptTemplatesListData.value?.items ?? [])
    const userMessage = ref('')
    const showAllMessages = ref(false)
    const allMessages = ref([])
    const processing = ref(false)
    const messageToEdit = ref(null)
    const messageToEditContent = ref('')
    const hoverMessage = ref(null)
    const abortController = ref(null)
    const reactions = ref({})
    const expandedStep = ref({})
    const feedbackModal = ref(false)
    const feedbackConfirmModal = ref(false)
    function toggleExpand(index) {
      expandedStep.value[index] = !expandedStep.value[index]
    }
    const selectedMessage = ref(null)

    const { draft, activeVariant, testSetItem } = useAgentEntityDetail()
    const appStore = useAppStore()
    const isUserMode = computed(() => props.endUserMode === 'true')
    return {
      draft,
      activeVariant,
      testSetItem,
      appStore,
      ragList,
      promptTemplatesList,
      userMessage,
      showAllMessages,
      allMessages,
      processing,
      messageToEdit,
      messageToEditContent,
      hoverMessage,
      abortController,
      isUserMode,
      props,
      reactions,
      selectedMessage,
      expandedStep,
      toggleExpand,
      feedbackModal,
      feedbackConfirmModal,
      traceId: ref(null),
      showHints: ref(true),
      m,
    }
  },
  computed: {
    selectedMessagePrepared() {
      const object = _.cloneDeep(this.selectedMessage)

      return object?.run?.steps.map((step) => {
        const startTime = new Date(step.started_at)
        const endTime = new Date(step.completed_at)
        const duration = this.formatDelay(endTime - startTime)

        return {
          type: step.type,
          detailsJSON: JSON.stringify(step[step.type] || {}, null, 2),
          details: step?.details || {},
          started_at: startTime.toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          }),
          completed_at: endTime.toLocaleString(),
          duration_seconds: duration,
          icon: step.type === 'classification' ? 'stack' : step.type === 'topic_completion' ? 'cpu' : 'code',
          typeLabel: step.type === 'classification' ? 'Classification' : step.type === 'topic_completion' ? 'Topic Completion' : 'Topic Action Call',
        }
      })
    },
    isShowHints() {
      // if messages are empty and sample questions are enabled
      return (
        this.allMessages?.length <= 1 &&
        this.showHints &&
        this.activeVariant?.value?.settings?.sample_questions?.enabled &&
        (!!this.activeVariant?.value?.settings?.sample_questions?.questions?.question1 ||
          !!this.activeVariant?.value?.settings?.sample_questions?.questions?.question2 ||
          !!this.activeVariant?.value?.settings?.sample_questions?.questions?.question3)
      )
    },
    sampleQuestion() {
      return this.activeVariant?.value?.settings?.sample_questions?.questions
    },
    welcomeMessage() {
      return this.activeVariant?.value?.settings?.welcome_message
    },
    systemPromptTemplate() {
      return this.promptTemplatesList.find((template) => template.system_name == this.promptTemplate)
    },
    messages() {
      if (this.showAllMessages) return this.allMessages
      return this.allMessages.filter((message) => {
        return message?.role == 'user' || (message?.role == 'assistant' && !!message.content)
      })
    },
    cantSendUserMessage() {
      if (this.processing) return true
      if (this.isUserMode && this?.userMessage.length === 0) return true
      return false
    },
    agentTestSetItem() {
      return this.testSetItem
    },
  },
  watch: {
    isUserMode(val) {
      if (val) {
        this.showAllMessages = false
      }
    },
    agentTestSetItem: {
      deep: true,
      handler(next, prev) {
        if (prev?.user_input !== next?.user_input) {
          this.userMessage = next?.user_input || ''
        }
      },
    },
  },
  mounted() {
    if (this.welcomeMessage) {
      this.allMessages.push({
        role: 'assistant',
        content: this.welcomeMessage,
        id: crypto.randomUUID(),
      })
    }
  },
  methods: {
    stringify(obj) {
      return JSON.stringify(obj, null, 2)
    },
    refine(question) {
      this.userMessage = question
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
    messageStyles(role, content, created_at) {
      return {
        'bg-white ba-border': role == 'user' || role == 'assistant',
        'bg-system-message-bg ba-thin-dark': role == 'system' || role === 'tool' || (role == 'assistant' && !content),
        'bg-light': this.selectedMessage ? created_at === this.selectedMessage?.created_at : false,
        'cursor-pointer': role == 'assistant' ? true : false,
      }
    },
    scrollToBottom() {
      this.$refs.messagesContainer.scrollTop = 0
    },
    handleUserMessageEnter(e) {
      if (e.shiftKey) {
        return
      }
      e.preventDefault()
      this.sendUserMessage()
    },
    async sendUserMessage() {
      if (this.cantSendUserMessage) return
      if (this.userMessage?.length > 0) {
        this.allMessages.push({
          id: crypto.randomUUID(),
          role: 'user',
          content: this.userMessage,
        })
        this.userMessage = ''
      }
      this.scrollToBottom()
      this.processing = true

      try {
        const updatedMessages = await this.processChat()
        this.allMessages = updatedMessages
      } catch (error) {
        if (error?.name === 'AbortError' || error?.technicalError?.name === 'AbortError') {
          // Aborted (e.g. user cleared the chat mid-request) — silent.
        } else {
          // Surface the actual backend error to the user instead of a silent
          // re-throw that bubbled into Vue's global error handler as a
          // confusing "response.json is not a function" trace.
          notify.error(error?.message || 'Agent request failed')
        }
      } finally {
        this.processing = false
      }
    },
    async processChat() {
      this.abortController = new AbortController()
      const data = {
        name: this.draft?.name,
        system_name: this.draft?.system_name,
        agent_config: this.activeVariant?.value,
        messages: this.allMessages,
        trace_id: this.traceId,
      }
      const endpoint = this.appStore.config?.agent?.endpoint
      const service = this.appStore.config?.agent?.service
      const credentials = this.appStore.config?.agent?.credentials
      const { trace_id: traceIdParam, ...payload } = data
      const response = await fetchData({
        method: 'POST',
        endpoint,
        service: `${service}/test` + (traceIdParam ? '?trace_id=' + traceIdParam : ''),
        credentials,
        body: JSON.stringify(payload),
        headers: { 'Content-Type': 'application/json' },
        signal: this.abortController.signal,
      })
      // `fetchData` returns either a Response or `{ error }` on failure;
      // surface the error through the caller's try/catch instead of crashing
      // on `response.json()` for a plain object. The extra `typeof` guard
      // catches any other non-Response shape (e.g. an aborted request that
      // resolved to `undefined`).
      if (response?.error) throw response.error
      if (typeof response?.json !== 'function') throw new Error('Empty response from agent test endpoint')
      const result = await response.json()
      const { trace_id, ...completionResult } = result

      this.traceId = trace_id

      return [...this.allMessages, completionResult]
    },
    async confirmMessage(selectedActions) {
      this.processing = true
      this.allMessages.push({
        id: crypto.randomUUID(),
        role: 'user',
        content: null,
        action_call_confirmations: selectedActions,
      })
      try {
        const data = {
          name: this.draft?.name,
          system_name: this.draft?.system_name,
          agent_config: this.activeVariant?.value,
          messages: this.allMessages,
          trace_id: this.traceId,
        }
        const confirmEndpoint = this.appStore.config?.agent?.endpoint
        const confirmService = this.appStore.config?.agent?.service
        const confirmCredentials = this.appStore.config?.agent?.credentials
        const { trace_id: confirmTraceId, ...confirmPayload } = data
        const confirmResponse = await fetchData({
          method: 'POST',
          endpoint: confirmEndpoint,
          service: `${confirmService}/test` + (confirmTraceId ? '?trace_id=' + confirmTraceId : ''),
          credentials: confirmCredentials,
          body: JSON.stringify(confirmPayload),
          headers: { 'Content-Type': 'application/json' },
        })
        if (confirmResponse?.error) throw confirmResponse.error
        if (typeof confirmResponse?.json !== 'function') throw new Error('Empty response from agent test endpoint')
        const confirmResult = await confirmResponse.json()
        const { trace_id, ...completionResult } = confirmResult
        this.traceId = trace_id
        this.allMessages = [...this.allMessages, completionResult]
      } catch (error) {

      } finally {
        this.processing = false
      }
    },
    clearChat() {
      // Abort any in-flight /test request so it can't write back into the
      // freshly-cleared state. Reset the trace id too — leaving it set
      // ties the next request to a server-side context that no longer has
      // any messages, which the backend rejects with
      // `list index out of range`.
      if (this.abortController) {
        this.abortController.abort()
        this.abortController = null
      }
      this.traceId = null
      this.allMessages = []
      this.reactions = {}
      this.processing = false
    },
    async saveMessage(index) {
      this.allMessages[index].content = this.messageToEditContent
      this.messageToEdit = null
      this.messageToEditContent = ''
    },
    deleteMessage(index) {
      this.allMessages.splice(index, 1)
    },
    reactToMessage(index, type) {
      this.reactions[index] = type
      if (!type) {
        this.feedbackModal = true
        return
      }

      this.feedbackConfirmModal = true
    },
    removeReaction(index) {
      delete this.reactions[index]
    },
    submitForm(form) {
      this.feedbackModal = false
      this.feedbackConfirmModal = true
    },
    copyMessage(message) {
      copyToClipboard(message.content)
      notify.copied(m.common_copiedToClipboard())
    },
  },
}
</script>

<style scoped>
.text-scroll::-webkit-scrollbar {
  inline-size: 6px;
}
.text-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.text-scroll::-webkit-scrollbar-thumb {
  background: transparent;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter,
.fade-leave-to {
  opacity: 0;
}

.expand-enter-active,
.expand-leave-active {
  transition:
    opacity var(--ds-duration-base) var(--ds-ease-out),
    max-height var(--ds-duration-base) var(--ds-ease-out);
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-block-size: 0;
}

.agents-drawer-preview__label {
  flex: 0 0 8.3333%;
  max-inline-size: 8.3333%;
}

.agents-drawer-preview__steps-scroll {
  overflow-block: auto;
  overflow-inline: hidden;
}

.agents-drawer-preview__messages-scroll {
  overflow-block: auto;
  max-block-size: 100%;
}

.agents-drawer-preview__step-row {
  text-transform: none;
}

.agents-drawer-preview__codemirror--sm {
  min-block-size: 50px;
}
.agents-drawer-preview__codemirror--md {
  min-block-size: 100px;
}
.agents-drawer-preview__codemirror--lg {
  max-block-size: 300px;
}

.agents-drawer-preview__divider {
  inline-size: 10px;
  block-size: 12px;
}

.agents-drawer-preview__processing {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.agents-drawer-preview__chevron {
  transition: transform var(--ds-duration-base) var(--ds-ease-out);
}
.agents-drawer-preview__chevron[data-expanded='true'] {
  transform: rotate(90deg);
}
</style>
