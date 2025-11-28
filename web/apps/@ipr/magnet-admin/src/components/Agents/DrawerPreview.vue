<template lang="pug">
.no-wrap.full-height(:style='!selectedMessage ? "max-width:500px; min-width:500px !important" : "max-width:1000px; min-width:1000px !important"')
  .row.full-height
    .col.full-height(v-if='selectedMessage')
      .column.full-height.q-py-16.bg-white.bl-border
        .col-auto.q-pl-16.q-pr-8
          .row
            .col.km-field.text-secondary-text
            .col-auto.q-ml-sm
              q-btn(icon='close', flat, dense, @click='selectedMessage = null')
          q-separator.q-mb-xs
        .col
          .column.fit.no-wrap.bg-white
            .fit.column.no-wrap.text-scroll.q-pl-16.q-pr-8(ref='messagesContainer', style='overflow-y: auto; max-height: 100%')
              q-timeline
                q-timeline-entry(
                  v-for='(step, index) in selectedMessagePrepared',
                  :key='step.started_at',
                  :icon='step.icon',
                  :color='expandedStep[index] ? "status-ready-text" : "primary"'
                )
                  template(v-slot:subtitle)
                    .row.items-center.justify-between(style='text-transform: none !important')
                      .col.q-mr-md
                        km-chip(
                          iconColor='icon',
                          hoverColor='primary',
                          labelClass='km-heading-2',
                          flat,
                          dense,
                          iconSize='16px',
                          hoverBg='primary-bg',
                          @click='step.type === "classification" || (step.type === "topic_completion" && !step?.details?.action_call_requests) ? null : toggleExpand(index)'
                        )
                          .row.items-center.justify-center.full-width
                            q-icon(
                              v-if='!(step.type === "classification" || (step.type === "topic_completion" && !step?.details?.action_call_requests))',
                              name='fas fa-chevron-right',
                              flat,
                              :style='{ transform: expandedStep[index] ? "rotate(90deg)" : "rotate(0deg)", transition: "0.2s" }'
                            )
                            .q-ml-sm.text-secondary-text.cursor-pointer {{ step?.typeLabel }}

                      .col-auto.q-mr-md.km-field {{ step?.duration_seconds }}
                  .column.q-gap-8
                    template(v-if='step.type === "classification"')
                      .col
                        .row
                          .col-1.q-mr-md
                            .km-field.text-secondary-text Intent
                          .col
                            km-chip(:label='step.details.intent', color='light')
                      .col(v-if='step.details?.topic')
                        .row
                          .col-1.q-mr-md
                            .km-field.text-secondary-text Topic
                          .col
                            km-chip(:label='step.details?.topic', color='light')
                      .col
                        .row
                          .col-auto.q-mr-md
                            .km-field.text-secondary-text Reason
                          .col-auto
                            | {{ step.details.reason }}
                    template(v-else-if='step.type === "topic_completion"')
                      .col
                        .row
                          .col-auto.q-mr-md
                            .km-field.text-secondary-text Topic
                          .col {{ step.details.topic.name }}
                      .col
                        .row
                          .col-auto.q-mr-md
                            .km-field.text-secondary-text Topic Description
                          .col-auto {{ step.details.topic.description }}

                        .q-mt-sm(v-if='step.details?.action_call_requests')
                          q-slide-transition
                            .q-mt-sm(v-if='step.details?.action_call_requests && expandedStep[index]')
                              .text-secondary-text(v-for='rq in step.details.action_call_requests')
                                .row.q-mb-sm.items-center
                                  km-chip(:label='rq.action_type', color='light')
                                  .q-ml-sm {{ rq.function_name }}
                                .km-field.text-secondary-text Request
                                km-codemirror(:model-value='stringify(rq.arguments)', readonly, style='min-height: 100px')

                    template(v-else-if='step.type === "topic_action_call"')
                      .q-mt-sm(v-if='step.details')
                        .text-secondary-text
                          .row.q-mb-sm.items-center
                            km-chip(:label='step.details.request.action_type', color='light')
                            .q-ml-sm {{ step.details.request.function_name }}
                          .km-field.text-secondary-text(v-if='step.details?.request && !expandedStep[index]') Request
                            km-codemirror(:model-value='stringify(step.details.request.arguments)', readonly, style='min-height: 50px')
                      div(v-if='step.details')
                        q-slide-transition
                          div(v-if='step.details?.request && expandedStep[index]')
                            .km-field.text-secondary-text Request
                            km-codemirror(:model-value='stringify(step?.details?.request)', readonly, style='min-height: 100px')
                            .km-field.text-secondary-text Response
                            km-codemirror(:model-value='stringify(step?.details?.response)', readonly, style='min-height: 100px')

                    template(v-else)
                      km-codemirror(v-model='step.detailsJSON', style='max-height: 300px', readonly)

    .col-auto(v-if='selectedMessage')
      .row.items-center.full-height
        .bg-white(style='width: 10px; height: 12px')
    .col.q-pa-16.bg-white.full-height
      .column.full-height
        .col-auto.km-heading-7.q-mb-xs
          .row
            .col Agent Preview
          q-separator.q-mb-md
        .col
          .column.fit.no-wrap.bg-white
            .fit.q-py-16.column.reverse.no-wrap.text-scroll(ref='messagesContainer', style='overflow-y: auto; max-height: 100%')
              template(v-if='processing')
                .column.justify-center.items-center
                  q-spinner-dots(size='62px', color='primary')
                  km-btn(flat, simple, label='Stop', iconSize='16px', icon='fas fa-times', @click='abortController.abort()')
              .column.no-wrap.q-px-16.q-gap-8
                template(v-for='(message, index) in allMessages')
                  agent-message(
                    :isSelected='selectedMessage?.id === message?.id',
                    :message='message',
                    v-if='showAllMessages || message?.role === "user" || message?.role === "assistant"',
                    :previewMode='true',
                    @copy='copyMessage(message)',
                    @save='saveMessage(index)',
                    @delete='deleteMessage(index)',
                    @focus='message?.role === "assistant" ? (selectedMessage = message) : null',
                    :lastMessage='index === allMessages.length - 1',
                    @confirm='confirmMessage($event)'
                  )
                //- agent-confirmation(

                //- )
                //- agent-confirmation(
                //-   :multiple='true',
                //- )
            agents-feedback-modal(
              :feedbackModal='feedbackModal',
              :feedbackConfirmModal='feedbackConfirmModal',
              @update:feedbackModal='feedbackModal = $event',
              @update:feedbackConfirmModal='feedbackConfirmModal = $event',
              @submit='submitForm'
            )
            .col-auto.q-mt-md.q-px-16
              form(@submit.prevent='sendUserMessage')
                km-input(
                  ref='input',
                  rows='8',
                  placeholder='Type your question here...',
                  :model-value='userMessage',
                  @input='userMessage = $event',
                  border-radius='8px',
                  height='36px',
                  type='textarea',
                  @keydown.enter='handleUserMessageEnter'
                )
                template(v-if='isShowHints')
                  .row.items-center.q-mt-sm
                    .col.km-heading-3 You can ask like this...
                    .col-auto
                      km-btn(flat, color='primary', @click='showHints = false')
                        .km-button-text Don’t show hints
                  template(v-for='(item, index) in sampleQuestion', :key='index')
                    km-btn(flat, @click='refine(item)')
                      .wrapped-text {{ item }}
                .row.justify-end.q-py-md.items-center
                  .col-auto.q-mr-md
                    km-btn(flat, simple, iconSize='16px', icon='fas fa-rotate-right', @click='clearChat')
                  .col
                  .col-auto
                    q-btn(type='submit', color='primary', :disable='cantSendUserMessage', unelevated, padding='6px 7px', style='maxheight: 28px')
                      template(v-slot:default)
                        q-icon(name='fas fa-paper-plane', size='16px')
</template>
<script>
import { useChroma } from '@shared'
import { copyToClipboard } from 'quasar'
import _ from 'lodash'
import { uid } from 'quasar'
import { ref, computed } from 'vue'

export default {
  props: {
    ragTools: {
      type: Array,
    },
    assistantTools: {
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
    const { items: ragList } = useChroma('rag_tools')
    const { items: promptTemplatesList } = useChroma('promptTemplates')
    const { items: assistantToolsList } = useChroma('assistant_tools')

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

    const isUserMode = computed(() => props.endUserMode === 'true')
    return {
      ragList,
      promptTemplatesList,
      userMessage,
      showAllMessages,
      allMessages,
      processing,
      assistantToolsList,
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
          icon: step.type === 'classification' ? 'fas fa-layer-group' : step.type === 'topic_completion' ? 'fas fa-microchip' : 'fas fa-code',
          typeLabel: step.type === 'classification' ? 'Classification' : step.type === 'topic_completion' ? 'Topic Completion' : 'Topic Action Call',
        }
      })
    },
    isShowHints() {
      // if messages are empty and sample questions are enabled
      return (
        this.allMessages?.length <= 1 &&
        this.showHints &&
        this.$store.getters.agentDetailVariant?.value?.settings?.sample_questions?.enabled &&
        (!!this.$store.getters.agentDetailVariant?.value?.settings?.sample_questions?.questions?.question1 ||
          !!this.$store.getters.agentDetailVariant?.value?.settings?.sample_questions?.questions?.question2 ||
          !!this.$store.getters.agentDetailVariant?.value?.settings?.sample_questions?.questions?.question3)
      )
    },
    sampleQuestion() {
      return this.$store.getters.agentDetailVariant?.value?.settings?.sample_questions?.questions
    },
    welcomeMessage() {
      return this.$store.getters.agentDetailVariant?.value?.settings?.welcome_message
    },
    systemPromptTemplate() {
      return this.promptTemplatesList.find((template) => template.system_name == this.promptTemplate)
    },
    assistantToolsNames() {
      //filter through list to verify tool exists
      return this.assistantToolsList.filter((tool) => this.assistantTools?.includes(tool.system_name))
    },
    //TODO: remove this
    assistantToolsDefinitions() {
      const assistantTools = this.assistantToolsList.filter((tool) => this.assistantTools?.includes(tool.system_name))
      return assistantTools.map((tool) => tool.definition)
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
      return this.$store.getters.agentTestSetItem
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
        id: uid(),
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
          id: uid(),
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
        if (error?.technicalError?.name === 'AbortError') {
          console.warn('Request was aborted')
        } else {
          throw ('Request failed:', error)
        }
      } finally {
        this.processing = false
      }
    },
    async processChat() {
      this.abortController = new AbortController()
      const data = {
        name: this.$store.getters.agent_detail?.name,
        system_name: this.$store.getters.agent_detail?.system_name,
        agent_config: this.$store.getters.agentDetailVariant?.value,
        messages: this.allMessages,
        trace_id: this.traceId,
      }
      const { trace_id, ...completionResult } = await this.$store.dispatch('testAgent', data)

      this.traceId = trace_id

      return [...this.allMessages, completionResult]
    },
    async confirmMessage(selectedActions) {
      this.processing = true
      this.allMessages.push({
        id: uid(),
        role: 'user',
        content: null,
        action_call_confirmations: selectedActions,
      })
      try {
        const data = {
          name: this.$store.getters.agent_detail?.name,
          system_name: this.$store.getters.agent_detail?.system_name,
          agent_config: this.$store.getters.agentDetailVariant?.value,
          messages: this.allMessages,
          trace_id: this.traceId,
        }
        const { trace_id, ...completionResult } = await this.$store.dispatch('testAgent', data)
        this.traceId = trace_id
        this.allMessages = [...this.allMessages, completionResult]
      } catch (error) {
        console.error(error)
      } finally {
        this.processing = false
      }
    },
    clearChat() {
      this.allMessages = []
      this.reactions = {}
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
      this.$q.notify({
        message: 'Copied to clipboard',
        color: 'primary',
        icon: 'fas fa-copy',
        timeout: 1000,
      })
    },
  },
}
</script>

<style scoped>
.text-scroll::-webkit-scrollbar {
  width: 6px;
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
  transition: all 0.2s ease;
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}
</style>
