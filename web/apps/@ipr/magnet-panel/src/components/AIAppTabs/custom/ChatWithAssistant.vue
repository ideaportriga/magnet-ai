<template>
  <div
    class="stack fit bg-light"
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
        data-gap="sm"
      >
        <template
          v-for="(message, index) in allMessages"
          :key="index"
        >
          <div
            v-if="showAllMessages || message.role === &quot;user&quot; || (message.role === &quot;assistant&quot; &amp;&amp; !!message.content)"
            class="border-radius-12 p-lg full-width"
            :class="messageStyles(message.role, message.content)"
            @mouseover="hoverMessage = index"
            @mouseleave="hoverMessage = null"
          >
            <div
              class="cluster mb-sm"
              :style="{ height: &quot;34px&quot; }"
              data-justify="between"
            >
              <div class="km-title text-capitalize">
                {{ message.role }}
              </div>
              <div
                v-if="message.role !== &quot;system&quot; &amp;&amp; hoverMessage === index &amp;&amp; !isUserMode"
                class="cluster"
                data-gap="sm"
              >
                <km-btn
                  class="self-start"
                  icon="edit"
                  icon-tone="brand"
                  icon-size="12px"
                  flat
                  :tooltip="m.common_edit()"
                  @click="((messageToEdit = index), (messageToEditContent = message.content))"
                />
                <km-btn
                  v-if="!messageToEdit"
                  icon="delete"
                  icon-tone="brand"
                  icon-size="12px"
                  flat
                  :tooltip="m.common_delete()"
                  @click="deleteMessage(index)"
                />
              </div>
            </div>
            <template v-if="message.role == &quot;tool&quot;">
              <div class="km-field mb-sm">
                {{ m.panel_toolResult({ toolCallId: message.tool_call_id }) }}
              </div>
            </template>
            <template v-if="!!message.content">
              <template v-if="messageToEdit === index">
                <km-input
                  v-model="messageToEditContent"
                  class="bg-light"
                  rows="5"
                  type="textarea"
                />
                <div
                  class="cluster pt-sm"
                  data-justify="end"
                  data-gap="sm"
                >
                  <km-btn
                    flat
                    simple
                    :label="m.panel_discardEdit()"
                    icon-size="16px"
                    icon="close"
                    @click="messageToEdit = null"
                  />
                  <km-btn
                    flat
                    simple
                    :label="m.common_save()"
                    icon-size="16px"
                    icon="save"
                    @click="saveMessage(index)"
                  />
                </div>
              </template>
              <template v-else>
                <km-markdown
                  :source="message.content"
                  style="overflow-wrap: break-word"
                />
              </template>
            </template>
            <template v-else-if="!!message.tool_calls">
              <div
                class="km-field text-pre-wrap"
                style="overflow-wrap: break-word"
              >
                {{ message.tool_calls }}
              </div>
            </template>
            <div
              v-if="message.role === &quot;assistant&quot; &amp;&amp; !!message.content"
              class="cluster"
              data-justify="end"
              data-gap="sm"
            >
              <km-btn
                class="border-radius-6"
                icon="thumbs-up"
                icon-size="16px"
                size="xs"
                flat
                :class="reactions[index] === true ? &quot;bg-like-bg&quot; : &quot;bg-white&quot;"
                @click="reactToMessage(index, true)"
              />
              <km-btn
                class="border-radius-6"
                icon="thumbs-down"
                icon-size="16px"
                size="xs"
                flat
                :class="reactions[index] === false ? &quot;bg-dislike-bg&quot; : &quot;bg-white&quot;"
                @click="reactToMessage(index, false)"
              />
            </div>
          </div>
        </template>
      </div>
    </div>
    <div class="flex-none mt-md px-lg">
      <form @submit.prevent="sendUserMessage">
        <km-input
          ref="input"
          rows="10"
          :placeholder="m.placeholder_enterUserMessage()"
          :model-value="userMessage"
          border-radius="8px"
          height="36px"
          type="textarea"
          @input="userMessage = $event"
          @keydown.enter="handleUserMessageEnter"
        />
        <div
          class="cluster py-md"
          data-justify="end"
        >
          <div class="flex-none mr-md">
            <km-btn
              flat
              simple
              :label="m.panel_clearChat()"
              icon-size="16px"
              icon="eraser"
              @click="clearChat"
            />
          </div>
          <div
            v-if="!isUserMode"
            class="flex-none mr-md"
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
          <div class="flex-none">
            <km-btn
              type="submit"
              :disable="cantSendUserMessage"
              unelevated
              padding="6px 7px"
              style="max-block-size: 28px"
            >
              <template #default>
                <km-glyph
                  name="send"
                  size="16px"
                />
              </template>
            </km-btn>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>
<script>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
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
      m,
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
