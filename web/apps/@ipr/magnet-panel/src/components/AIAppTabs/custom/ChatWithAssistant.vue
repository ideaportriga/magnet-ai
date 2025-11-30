<template lang="pug">
.column.fit.bg-light.no-wrap
  .fit.q-py-16.column.reverse.no-wrap.text-scroll(ref='messagesContainer', style='overflow-y: auto; max-height: 100%')
    template(v-if='processing')
      .column.justify-center.items-center
        q-spinner-dots(size='62px', color='primary')
        km-btn(flat, simple, label='Stop', iconSize='16px', icon='fas fa-times', @click='abortController.abort()')
    .column.no-wrap.q-px-16.q-gap-8
      template(v-for='(message, index) in allMessages')
        .border-radius-12.q-pa-lg.full-width(
          @mouseover='hoverMessage = index',
          @mouseleave='hoverMessage = null',
          v-if='showAllMessages || message.role === "user" || (message.role === "assistant" && !!message.content)',
          :class='messageStyles(message.role, message.content)'
        )
          .row.justify-between.q-mb-sm.items-center(:style='{ height: "34px" }')
            .km-title.text-capitalize {{ message.role }}
            .row.q-gap-8(v-if='message.role !== "system" && hoverMessage === index && !isUserMode')
              km-btn.self-start(
                icon='fas fa-pen',
                iconColor='primary',
                iconSize='12px',
                flat,
                @click='((messageToEdit = index), (messageToEditContent = message.content))',
                tooltip='Edit'
              )
              km-btn(
                icon='fas fa-trash',
                iconColor='primary',
                iconSize='12px',
                flat,
                @click='deleteMessage(index)',
                tooltip='Delete',
                v-if='!messageToEdit'
              )

          template(v-if='message.role == "tool"')
            .km-field.q-mb-sm [Result for {{ message.tool_call_id }}]

          template(v-if='!!message.content')
            //- .km-field.text-pre-wrap {{ message.content }}
            template(v-if='messageToEdit === index')
              km-input.bg-light(v-model='messageToEditContent', rows='5', type='textarea')
              .row.justify-end.q-gap-8.q-pt-sm
                km-btn(flat, simple, label='Discard Edit', iconSize='16px', icon='fas fa-times', @click='messageToEdit = null')
                km-btn(flat, simple, label='Save', iconSize='16px', icon='fas fa-save', @click='saveMessage(index)')
            template(v-else) 
              km-markdown(:source='message.content', style='overflow-wrap: break-word')

          template(v-else-if='!!message.tool_calls')
            .km-field.text-pre-wrap(style='overflow-wrap: break-word') {{ message.tool_calls }}
          .row.justify-end.q-gap-8(v-if='message.role === "assistant" && !!message.content')
            km-btn.border-radius-6(
              svgIcon='like',
              iconColor='primary',
              iconSize='12px',
              size='xs',
              flat,
              @click='reactToMessage(index, true)',
              :class='reactions[index] === true ? "bg-like-bg" : "bg-white"'
            )
            km-btn.border-radius-6(
              svgIcon='dislike',
              iconColor='primary',
              iconSize='12px',
              size='xs',
              flat,
              @click='reactToMessage(index, false)',
              :class='reactions[index] === false ? "bg-dislike-bg" : "bg-white"'
            )

  .col-auto.q-mt-md.q-px-16
    form(@submit.prevent='sendUserMessage')
      km-input(
        ref='input',
        rows='10',
        placeholder='Enter user message...',
        :model-value='userMessage',
        @input='userMessage = $event',
        border-radius='8px',
        height='36px',
        type='textarea',
        @keydown.enter='handleUserMessageEnter'
      )
      .row.justify-end.q-py-md.items-center
        .col-auto.q-mr-md
          km-btn(flat, simple, label='Clear chat', iconSize='16px', icon='fas fa-eraser', @click='clearChat')
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
import { ref, computed } from 'vue'
import { useChatCompletion, usePromptTemplates, useRagTools } from '@/pinia'
import { storeToRefs } from 'pinia'

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
    const chatCompletionStore = useChatCompletion()

    const ragToolsStore = useRagTools()
    const { items: ragList } = storeToRefs(ragToolsStore)

    const promptTemplatesStore = usePromptTemplates()
    const { items: promptTemplatesList } = storeToRefs(promptTemplatesStore)

    const userMessage = ref('')
    const showAllMessages = ref(false)
    const allMessages = ref([])
    const processing = ref(false)
    const messageToEdit = ref(null)
    const messageToEditContent = ref('')
    const hoverMessage = ref(null)
    const abortController = ref(null)
    const reactions = ref({})

    const isUserMode = computed(() => props.endUserMode === 'true')
    return {
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
      chatCompletionStore,
    }
  },
  computed: {
    systemPromptTemplate() {
      return this.promptTemplatesList.find((template) => template.system_name == this.promptTemplate)
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
      //if (this.userMessage?.length === 0 && this.allMessages.length <= 1) return true
      return false
    },
  },
  watch: {
    isUserMode(val) {
      if (val) {
        this.showAllMessages = false
      }
    },
  },
  methods: {
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
      if (this.userMessage?.length > 0) {
        this.allMessages.push({
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
      const authParams = JSON.parse(this.authParams || '{}')
      const data = {
        system_prompt_template: this.systemPromptTemplate.system_name,
        messages: this.allMessages,
        mock_data: this.mockData,
        api_spec: this.parsedSpec,
        auth_params: authParams,
      }
      const completionResult = await this.chatCompletionStore.chatCompletionsWithAssistantTools({ data, signal: this.abortController.signal })
      return completionResult.messages
    },
    clearChat() {
      this.allMessages = []
    },
    async saveMessage(index) {
      this.allMessages[index].content = this.messageToEditContent
      this.messageToEdit = null
      this.messageToEditContent = ''
    },
    deleteMessage(index) {
      this.allMessages.splice(index, 1)
    },
    reactToMessage(index, reaction) {
      this.reactions[index] = reaction
    },
    removeReaction(index) {
      delete this.reactions[index]
    },
  },
}
</script>
