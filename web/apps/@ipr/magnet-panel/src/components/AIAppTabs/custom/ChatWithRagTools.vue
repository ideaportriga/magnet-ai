<template>
  <div
    class="flex-1 p-md full-height bg-light flex"
    style="justify-content: center"
  >
    <div
      class="stack full-width"
      style="max-inline-size: 800px"
    >
      <div class="flex-none">
        <div
          class="cluster"
          data-gap="lg"
          data-wrap="no"
        >
          <template v-if="tools">
            <km-btn
              tone="brand"
              link
              @click="showTools = true"
            >
              {{ m.panel_viewTools() }}
            </km-btn>
          </template>
        </div>
      </div>
      <div class="flex-none cluster mt-md">
        <div class="km-field text-secondary-text mr-md">
          {{ m.panel_showInternalMessages() }}
        </div>
        <km-toggle
          v-model="showAllMessages"
          dense
        />
      </div>
      <div
        class="flex-1 stack mt-md full-width"
        data-gap="md"
      >
        <template
          v-for="(message, index) in messages"
          :key="index"
        >
          <div class="ba-border bg-white border-radius-12 p-lg full-width">
            <div class="km-title">
              {{ message.role }}
            </div>
            <template v-if="message.role == &quot;tool&quot;">
              <div class="km-field mb-sm">
                {{ m.panel_toolResult({ toolCallId: message.tool_call_id }) }}
              </div>
              <km-markdown :source="message.content" />
            </template>
            <template v-else-if="!!message.content">
              <km-markdown :source="message.content" />
            </template>
            <template v-else-if="!!message.tool_calls">
              <div
                class="km-field text-pre-wrap"
                style="overflow-wrap: break-word"
              >
                {{ message.tool_calls }}
              </div>
            </template>
          </div>
        </template>
      </div>
      <template v-if="processing">
        <div
          class="flex-none cluster"
          data-justify="center"
        >
          <km-loader
            size="62px"
          />
        </div>
      </template>
      <div class="flex-none mt-md">
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
    <km-popup-confirm
      :visible="showTools"
      title="Function tools"
      cancel-button-label="Cancel"
      @cancel="showTools = false"
    >
      <div
        class="cluster pt-sm pl-sm"
        data-justify="between"
      >
        <div class="basis-12 py-sm">
          <km-codemirror
            v-model="toolsString"
            :readonly="true"
            language="json"
          />
        </div>
      </div>
    </km-popup-confirm>
  </div>
</template>
<script>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { usePromptTemplates, useRagTools, useChatCompletion } from '@/pinia'
import { storeToRefs } from 'pinia'

export default {
  props: {
    promptTemplateSystemMessage: {
      type: String,
    },
    ragTools: {
      type: String,
    },
  },
  setup(props) {
    const chatCompletionStore = useChatCompletion()

    const promptTemplatesStore = usePromptTemplates()
    const { items: promptTemplates } = storeToRefs(promptTemplatesStore)

    const systemPromptTemplate = computed(() => {
      return promptTemplates.value.find((promptTemplate) => promptTemplate.system_name == props.promptTemplateSystemMessage)
    })

    const allMessages = ref([])

    const displayedMessages = computed(() => {
      return allMessages.value.filter((message) => {
        if (message.role == 'user') {
          return true
        }

        if (message.role == 'assistant' && !!message.content) {
          return true
        }

        return false
      })
    })

    const userMessage = ref('')

    const showAllMessages = ref(false)

    const messages = computed(() => {
      if (showAllMessages.value) {
        return allMessages.value
      }

      return displayedMessages.value
    })

    const processing = ref(false)

    const cantSendUserMessage = computed(() => {
      return processing.value || !userMessage.value
    })

    const ragToolsStore = useRagTools()
    const { items: allRagTools } = storeToRefs(ragToolsStore)

    function createToolsDefinitions() {
      const selectedRagTools = allRagTools.value.filter((ragTool) => props.ragTools.includes(ragTool.system_name))

      const ragToolSystemNames = selectedRagTools.map((selectedRagTool) => selectedRagTool.system_name)
      const ragToolDescriptionLines = selectedRagTools.map(
        (selectedRagTool) => `\n- ${selectedRagTool.system_name}: ${selectedRagTool.name}. ${selectedRagTool.description}`
      )
      const functionToolDescription = `The RAG tools available:\n${ragToolDescriptionLines}`

      const toolsDefinitions = [
        {
          type: 'function',
          function: {
            name: 'rag_tool_answer',
            description: "Answer user's question based on search for information in specific knowledge sources.",
            parameters: {
              type: 'object',
              properties: {
                rag_tool: {
                  type: 'string',
                  enum: ragToolSystemNames,
                  description: functionToolDescription,
                },
                query: {
                  type: 'string',
                  description: "The user's search query.",
                },
              },
            },
          },
        },
      ]

      return toolsDefinitions
    }

    const tools = ref(createToolsDefinitions())

    const showTools = ref(false)

    const toolsString = computed(() => {
      return JSON.stringify(tools.value, null, 2)
    })

    const mockData = {}

    return {
      allMessages,
      messages,
      userMessage,
      displayedMessages,
      showAllMessages,
      processing,
      cantSendUserMessage,
      tools,
      showTools,
      toolsString,
      promptTemplates,
      systemPromptTemplate,
      mockData,
      chatCompletionStore,
      m,
    }
  },
  computed: {},
  methods: {
    handleUserMessageEnter(event) {
      if (event.shiftKey) {
        return
      }
      event.preventDefault()
      this.sendUserMessage()
    },

    async sendUserMessage() {
      if (this.cantSendUserMessage) {
        return
      }

      this.allMessages.push({
        role: 'user',
        content: this.userMessage,
      })
      this.userMessage = ''

      this.processing = true

      try {
        const updatedMessages = await this.processChat()
        this.allMessages = updatedMessages
      } finally {
        this.processing = false
      }
    },

    async processChat() {
      const data = {
        system_prompt_template: this.systemPromptTemplate.system_name,
        messages: this.allMessages,
        tools: this.tools,
        mock_data: this.mockData,
        api_spec: this.parsedSpec,
      }
      const completionResult = await this.chatCompletionStore.chatCompletionsWithOpenapiFunctions({ data })

      return completionResult.messages
    },

    clearChat() {
      this.allMessages = []
    },
  },
}
</script>
