<template lang="pug">
.column.fit.no-wrap.bg-white
  .fit.q-py-16.column.reverse.no-wrap.text-scroll(ref='messagesContainer', style='overflow-y: auto; max-height: 100%')
    template(v-if='processing')
      .column.justify-center.items-center
        q-spinner-dots(size='62px', color='primary')
        km-btn(flat, simple, label='Stop', iconSize='16px', icon='fas fa-times', @click='abortController.abort()')
    .column.no-wrap.q-px-16.q-gap-16
      template(v-if='welcomeMessage && allMessages?.length === 0 && !processing')
        agent-message(:message='{ role: "welcome", content: welcomeMessage }')
      template(v-for='(message, index) in allMessages')
        agent-message(
          v-if='showAllMessages || message?.role === "user" || message?.role === "assistant"',
          :message='message',
          :key='index',
          :reaction='reactions[message.id]',
          :lastMessage='index === allMessages.length - 1',
          @copy='copyMessage',
          @like='like',
          @dislike='dislike',
          @confirm='confirmActions',
          :liveMode='true'
        )
      agent-feedback-modal(
        :feedback-modal='feedbackModal',
        :feedback-confirm-modal='feedbackConfirmModal',
        @update:feedback-modal='feedbackModal = $event',
        @update:feedback-confirm-modal='feedbackConfirmModal = $event',
        @submit='react'
      )

  .col-auto.q-mt-md.q-px-16
    form(@submit.prevent='sendUserMessage')
      km-input(
        ref='input',
        rows='3',
        placeholder='Enter user message...',
        :model-value='userMessage',
        @input='userMessage = $event',
        border-radius='8px',
        height='36px',
        type='textarea',
        @keydown.enter='handleUserMessageEnter'
      )
      template(v-if='isShowHints')
        .row.items-center.q-mt-16.q-mb-8
          .col.km-heading-3 You can ask like this...
          .col-auto
            km-btn(flat, color='primary', @click='showHints = false')
              .km-button-text Don’t show hints

        template(v-if='$theme === "default"')
          template(v-for='(item, index) in sampleQuestion', :key='index')
            km-btn(flat, @click='refine(item)')
              .wrapped-text {{ item }}
        template(v-else)
          template(v-for='(item, index) in sampleQuestion', :key='index')
            .flex
              km-btn.hint(bg='transparent', color='primary', @click='refine(item)')
                .wrapped-text {{ item }}
      .row.justify-end.q-py-md.items-center.justify-between
        .col-auto.q-mr-md(v-if='isUserMode')
          km-btn(flat, simple, icon='fas fa-redo', iconSize='16px', @click='clearChat')
        .col-auto.q-mr-md(v-if='!isUserMode')
          km-btn(
            flat,
            simple,
            :label='showAllMessages ? "Hide debug messages" : "Show all messages"',
            iconSize='16px',
            :icon='showAllMessages ? "fas fa-eye-slash" : "fas fa-eye"',
            @click='showAllMessages = !showAllMessages'
          )
        .col-auto
          q-btn(type='submit', color='primary', :disable='cantSendUserMessage', unelevated, padding='6px 7px', style='maxheight: 28px')
            template(v-slot:default)
              q-icon(name='fas fa-paper-plane', size='16px')
</template>
<script>
import { useAgents, useAgentTab, useAuth, useAiApps } from '@/pinia'
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { copyToClipboard } from 'quasar'

export default {
  props: {
    agent: {
      type: String,
    },
    assistantTools: {
      type: Array,
    },
    promptTemplate: {
      type: Array,
    },
    endUserMode: {
      type: String,
      default: 'true',
    },
    tab: {
      type: Object,
    },
  },
  setup(props) {
    const authStore = useAuth()
    //const agentsStore = useAgents()
    const agentTabStore = useAgentTab()

    //const { items: agentList } = storeToRefs(agentsStore)
    const aiAppsStore = useAiApps()

    const userMessage = ref('')
    const showAllMessages = ref(false)
    const allMessages = ref([])
    const processing = ref(false)
    const messageToEdit = ref(null)
    const messageToEditContent = ref('')
    const hoverMessage = ref(null)
    const abortController = ref(null)
    const reactions = ref({})
    const feedbackModal = ref(false)
    const feedbackConfirmModal = ref(false)
    const showHints = ref(true)

    const isUserMode = computed(() => props.endUserMode === 'true')
    return {
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
      //agentList,
      traceId: ref(null),
      agentTabStore,
      authStore,
      feedbackModal,
      feedbackConfirmModal,
      aiAppsStore,
      showHints,
    }
  },
  computed: {
    panel() {
      return this.aiAppsStore.displayTab
    },
    isShowHints() {
      return (
        this.allMessages?.length == 0 &&
        this.showHints &&
        this.panel?.entityObject?.settings?.sample_questions?.enabled &&
        (!!this.panel?.entityObject?.settings?.sample_questions?.questions?.question1 ||
          !!this.panel?.entityObject?.settings?.sample_questions?.questions?.question2 ||
          !!this.panel?.entityObject?.settings?.sample_questions?.questions?.question3)
      )
    },
    sampleQuestion() {
      return this.panel?.entityObject?.settings?.sample_questions?.questions
    },
    client_id() {
      const ai_app = this.ai_app_param
      const tab = this.tab?.system_name
      const agent = this.agent
      const user = this.authStore.userInfo?.user_id
      if (user) {
        return `${ai_app}-${tab}-${agent}-${user}`
      }
      return ''
    },
    ai_app_param() {
      return this.$route.query.ai_app || window?.magnetai_ai_app
    },
    conversationId() {
      return this.agentTabStore.conversationId
    },
    messages() {
      if (this.showAllMessages) return this.allMessages
      return this.allMessages.filter((message) => {
        return message.role == 'user' || (message.role == 'assistant' && !!message.content)
      })
    },
    cantSendUserMessage() {
      if (this.processing) return true
      if (this.isUserMode && this?.userMessage.length === 0) return true
      return false
    },
    welcomeMessage() {
      return this.panel?.entityObject?.settings?.welcome_message
    },
  },
  watch: {
    isUserMode(val) {
      if (val) {
        this.showAllMessages = false
      }
    },
  },
  async mounted() {
    try {
      this.processing = true
      const conversation = await this.getLastConversation()
      if (conversation && conversation.messages) {
        this.allMessages = conversation?.messages
      }
    } catch (error) {
      console.error('Error loading messages', error)
    } finally {
      this.processing = false
    }
  },
  methods: {
    refine(question) {
      this.userMessage = question
    },
    copyMessage(message_id) {
      const message = this.allMessages.find((message) => message.id === message_id)
      if (message.role === 'assistant') {
        copyToClipboard(message.content)
        this.agentTabStore.reportCopyUsage({ conversation_id: this.conversationId, message_id: message.id })
        this.$q.notify({
          message: 'Copied to clipboard',
          color: 'primary',
          icon: 'fas fa-copy',
          timeout: 1000,
        })
      }
    },
    async getLastConversation() {
      if (!this.client_id) return
      const conversation = await this.agentTabStore.getLastRelevantConversation(this.client_id)
      this.agentTabStore.conversationId = conversation?.id || null
      return conversation
    },
    messageStyles(role, content) {
      return {
        'bg-white ba-border': role == 'user' || role == 'assistant',
        'bg-system-message-bg ba-thin-dark': role == 'system' || role === 'tool' || (role == 'assistant' && !content),
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

      this.allMessages.push({
        role: 'user',
        content: this.userMessage,
      })

      const userMessage = this.userMessage
      this.userMessage = ''

      this.scrollToBottom()
      this.processing = true

      try {
        const messages = await this.processChat(userMessage)
        console.log('messages', messages)
        this.allMessages.pop()
        this.allMessages.push(...messages)
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
    async processChat(userMessage) {
      this.abortController = new AbortController()

      let result = null
      if (!this.conversationId) {
        const data = await this.agentTabStore.createConversation({
          agent: this.agent,
          user_message_content: userMessage,
          client_id: this.client_id,
        })
        this.agentTabStore.conversationId = data?.id
        result = data?.messages || []
      } else {
        const data = await this.agentTabStore.addUserMessageToConversation({
          conversation_id: this.conversationId,
          user_message_content: userMessage,
        })

        result = [data.user_message, data.assistant_message]
      }
      return result
    },
    clearChat() {
      this.allMessages = []
      this.agentTabStore.conversationId = null
    },
    async saveMessage(index) {
      this.allMessages[index].content = this.messageToEditContent
      this.messageToEdit = null
      this.messageToEditContent = ''
    },
    deleteMessage(index) {
      this.allMessages.splice(index, 1)
    },
    async react(message_id, feedback) {
      this.feedbackModal = false
      this.feedbackConfirmModal = false
      const res = await this.agentTabStore.sendFeedback({
        conversation_id: this.conversationId,
        message_id,
        feedback,
      })
      if (res) {
        this.reactions[message_id] = feedback.type
      }
    },
    like(message_id) {
      this.react(message_id, { type: 'like' })
      this.feedbackConfirmModal = true
    },
    dislike(message_id) {
      console.log('dislike', message_id)
      this.feedbackModal = message_id
    },
    async confirmActions(ids) {
      this.scrollToBottom()
      this.processing = true
      try {
        const data = await this.agentTabStore.addUserMessageToConversation({
          conversation_id: this.conversationId,
          action_call_confirmations: ids,
        })

        const messages = Object.values(data)
          .filter((message) => message.id)
          .sort((a) => (a.role === 'user' ? -1 : 1))

        this.allMessages.push(...messages)
      } finally {
        this.processing = false
      }
    },
  },
}
</script>
