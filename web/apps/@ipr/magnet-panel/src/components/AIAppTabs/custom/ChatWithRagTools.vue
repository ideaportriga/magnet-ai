<template lang="pug">
.col.q-pa-md.full-height.bg-light.row.justify-center
  .column.full-width(style='max-width: 800px')
    .col-auto
      .row.q-gap-16.no-wrap
        template(v-if='tools')
          km-btn(color='primary', link, @click='showTools = true') View tools

    .col-auto.row.items-center.q-mt-md
      .km-field.text-secondary-text.q-mr-md Show internal messages
      q-toggle(v-model='showAllMessages', dense)

    .col.column.q-gap-12.q-mt-md.full-width
      template(v-for='(message, index) in messages')
        .ba-border.bg-white.border-radius-12.q-pa-lg.full-width
          .km-title {{ message.role }}

          template(v-if='message.role == "tool"')
            .km-field.q-mb-sm [Result for {{ message.tool_call_id }}]
            km-markdown(:source='message.content')

          template(v-else-if='!!message.content')
            //- .km-field.text-pre-wrap {{ message.content }}
            km-markdown(:source='message.content')

          template(v-else-if='!!message.tool_calls')
            .km-field.text-pre-wrap(style='overflow-wrap: break-word') {{ message.tool_calls }}

    template(v-if='processing')
      .col-auto.row.justify-center
        q-spinner-dots(size='62px', color='primary')

    .col-auto.q-mt-md
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
        .row.justify-end.q-py-md
          .col-auto.q-mr-md
            km-btn(flat, simple, label='Clear chat', iconSize='16px', icon='fas fa-eraser', @click='clearChat')
          .col-auto
            q-btn(type='submit', color='primary', :disable='cantSendUserMessage', unelevated, padding='6px 7px', style='maxheight: 28px')
              template(v-slot:default)
                q-icon(name='fas fa-paper-plane', size='16px')

  km-popup-confirm(:visible='showTools', title='Function tools', cancelButtonLabel='Cancel', @cancel='showTools = false')
    .row.justify-between.q-pt-8.q-pl-8
      .col-12.q-py-8
        km-codemirror(v-model='toolsString', :readonly='true', language='json')
</template>
<script>
import { ref, computed } from 'vue'
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
                  description: 'The user’s search query.',
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
