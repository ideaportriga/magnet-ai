<template>
  <div
    class="stack fit bg-white"
    data-gap="0"
  >
    <div
      ref="messagesContainer"
      class="fit py-lg flex text-scroll"
      style="overflow-block: auto; max-block-size: 100%; flex-flow: column-reverse nowrap"
    >
      <template v-if="processing">
        <div
          class="flex"
          style="flex-direction: column; justify-content: center; align-items: center"
        >
          <km-loader
            size="62px"
          />
          <km-btn
            flat
            simple
            :label="m.panel_stop()"
            icon-size="16px"
            icon="close"
            @click="abortController.abort()"
          />
        </div>
      </template>
      <div
        class="stack px-lg"
        data-gap="lg"
      >
        <template v-if="welcomeMessage &amp;&amp; allMessages?.length === 0 &amp;&amp; !processing">
          <agent-message :message="{ role: &quot;welcome&quot;, content: welcomeMessage }" />
        </template>
        <template
          v-for="(message, index) in allMessages"
          :key="index"
        >
          <agent-message
            v-if="showAllMessages || message?.role === &quot;user&quot; || message?.role === &quot;assistant&quot;"
            :key="index"
            :message="message"
            :reaction="reactions[message.id]"
            :last-message="index === allMessages.length - 1"
            :live-mode="true"
            @copy="copyMessage"
            @like="like"
            @dislike="dislike"
            @confirm="confirmActions"
          />
        </template>
        <agent-feedback-modal
          :feedback-modal="feedbackModal"
          :feedback-confirm-modal="feedbackConfirmModal"
          @update:feedback-modal="feedbackModal = $event"
          @update:feedback-confirm-modal="feedbackConfirmModal = $event"
          @submit="react"
        />
      </div>
    </div>
    <div class="flex-none mt-md px-lg">
      <form @submit.prevent="sendUserMessage">
        <km-input
          ref="input"
          data-test="preview-input"
          autogrow
          :rows="1"
          :min-rows="1"
          :max-rows="10"
          :placeholder="m.placeholder_enterUserMessage()"
          :model-value="userMessage"
          border-radius="8px"
          height="36px"
          type="textarea"
          @input="userMessage = $event"
          @keydown.enter="handleUserMessageEnter"
        >
          <template #append>
            <km-btn
              data-test="preview-btn"
              type="submit"
              size="icon-xs"
              icon="send"
              icon-size="16px"
              icon-tone="inverse"
              :disable="cantSendUserMessage"
            />
          </template>
        </km-input>
        <template v-if="isShowHints">
          <div class="cluster mt-lg mb-sm">
            <div class="flex-1 km-heading-3">
              {{ m.common_youCanAskLikeThis() }}
            </div>
            <div class="flex-none">
              <km-btn
                flat
                tone="brand"
                @click="showHints = false"
              >
                <div class="km-button-text">
                  {{ m.common_dontShowHints() }}
                </div>
              </km-btn>
            </div>
          </div>
          <template v-if="$theme === &quot;default&quot;">
            <template
              v-for="(item, index) in sampleQuestion"
              :key="index"
            >
              <km-btn
                flat
                @click="refine(item)"
              >
                <div class="wrapped-text">
                  {{ item }}
                </div>
              </km-btn>
            </template>
          </template>
          <template v-else>
            <template
              v-for="(item, index) in sampleQuestion"
              :key="index"
            >
              <div class="flex">
                <km-btn
                  class="hint"
                  flat
                  tone="brand"
                  @click="refine(item)"
                >
                  <div class="wrapped-text">
                    {{ item }}
                  </div>
                </km-btn>
              </div>
            </template>
          </template>
        </template>
        <div class="cluster py-md">
          <div
            v-if="isUserMode"
            class="flex-none"
          >
            <km-btn
              flat
              simple
              icon="redo"
              icon-size="16px"
              @click="clearChat"
            />
            <km-tooltip
              anchor="top middle"
              self="bottom middle"
            >
              <div class="km-label">
                {{ m.panel_startNewConversation() }}
              </div>
            </km-tooltip>
          </div>
          <div
            v-if="!isUserMode"
            class="flex-none"
          >
            <km-btn
              flat
              simple
              :label="showAllMessages ? m.panel_hideDebugMessages() : m.panel_showAllMessages()"
              icon-size="16px"
              :icon="showAllMessages ? &quot;eye-off&quot; : &quot;eye&quot;"
              @click="showAllMessages = !showAllMessages"
            />
          </div>
        </div>
      </form>
    </div>
  </div>
</template>
<script>
import { useAgents, useAgentTab, useAuth, useAiApps } from '@/pinia'
import { m } from '@/paraglide/messages'
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { copyToClipboard } from '@ds/utils/clipboard'
import { notify } from '@shared/utils/notify'

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
      m,
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
      const ai_app = this.ai_app_param || 'standalone'
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
        notify.copied(m.common_copiedToClipboard())
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
      // this.feedbackConfirmModal = true
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
