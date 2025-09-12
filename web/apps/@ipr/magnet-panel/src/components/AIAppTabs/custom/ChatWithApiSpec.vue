<template lang="pug">
.col.q-pa-md.full-height.bg-light.row.justify-center
  .column.full-width(style='max-width: 800px')
    .col-auto.row.justify-between.items-center.q-gap-16
      .col
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 OpenAPI spec
        q-file.km-control.km-input.rounded-borders(
          :multiple='true',
          max-files='1',
          style='height: var(--prompt-input-height); flex: 1; border-radius: var(--chip-radius)',
          outlined,
          v-model='files',
          accept='.json, .yml',
          :disable='uploadOpenApiSpecsInProgress',
          dense,
          labelClass='km-heading-2'
        )
          template(#prepend)
            q-icon.q-mr-8(name='attach_file')
          template(#append)
            .self-center.center-flex
              q-btn.border-radius-6(
                color='primary',
                @click='uploadOpenApiSpecs',
                :disable='uploadOpenApiSpecsInProgress',
                unelevated,
                padding='6px 7px'
              )
                template(v-slot:default)
                  q-icon(name='fas fa-upload', size='var(--prompt-input-icon-size)')

    .row.justify-end.full-width.q-mt-sm
      km-btn.rounded-borders(
        size='sm',
        flat,
        :label='showAuthParams ? "Hide auth params" : "Show auth params"',
        :icon='showAuthParams ? "arrow_drop_up" : "arrow_drop_down"',
        @click='showAuthParams = !showAuthParams'
      )
    template(v-if='showAuthParams')
      .col-auto
        km-input(rows='5', :model-value='authParams', @input='authParams = $event', border-radius='8px', height='36px', type='textarea')

    template(v-if='uploadOpenApiSpecsInProgress')
      .col-auto.row.justify-center
        q-spinner-dots(size='62px', color='primary') 

    .col-auto
      .row.q-gap-16.no-wrap
        template(v-if='parsedSpec')
          km-btn(color='primary', link, @click='showParsedSpec = true') View parsed spec
        template(v-if='tools')
          km-btn(color='primary', link, @click='showTools = true') View function tools

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

  km-popup-confirm(:visible='showParsedSpec', title='Parsed spec', cancelButtonLabel='Cancel', @cancel='showParsedSpec = false')
    .row.justify-between.q-pt-8.q-pl-8
      .col-12.q-py-8
        km-codemirror(v-model='parsedSpecString', :readonly='true', language='json')
  km-popup-confirm(:visible='showTools', title='Function tools', cancelButtonLabel='Cancel', @cancel='showTools = false')
    .row.justify-between.q-pt-8.q-pl-8
      .col-12.q-py-8
        km-codemirror(v-model='toolsString', :readonly='true', language='json')
</template>
<script>
import { ref, computed } from 'vue'
import { useChatCompletion, usePromptTemplates } from '@/pinia'
import { storeToRefs } from 'pinia'

export default {
  props: {
    promptTemplateSystemMessage: {
      type: String,
    },
    mockDataDefault: {
      type: Object,
    },
    toolsDefault: {
      type: Object,
    },
  },
  setup(props) {
    const promptTemplatesStore = usePromptTemplates()
    const { items: promptTemplates } = storeToRefs(promptTemplatesStore)

    const chatCompletionStore = useChatCompletion()

    const mockData = props.mockDataDefault

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

    const parsedSpec = ref(null)

    const showParsedSpec = ref(false)

    const parsedSpecString = computed(() => {
      return JSON.stringify(parsedSpec.value, null, 2)
    })

    const tools = ref(props.toolsDefault)

    const showTools = ref(false)

    const toolsString = computed(() => {
      return JSON.stringify(tools.value, null, 2)
    })

    const authParams = ref('{}')

    const showAuthParams = ref(false)

    return {
      allMessages,
      messages,
      userMessage,
      displayedMessages,
      showAllMessages,
      processing,
      cantSendUserMessage,
      parsedSpec,
      showParsedSpec,
      parsedSpecString,
      tools,
      showTools,
      toolsString,
      files: ref([]),
      uploadOpenApiSpecsInProgress: ref(false),
      promptTemplates,
      systemPromptTemplate,
      mockData,
      authParams,
      showAuthParams,
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
      const authParams = JSON.parse(this.authParams)

      const data = {
        system_prompt_template: this.systemPromptTemplate.system_name,
        messages: this.allMessages,
        tools: this.tools,
        mock_data: this.mockData,
        api_spec: this.parsedSpec,
        auth_params: authParams,
      }
      const completionResult = await this.chatCompletionStore.chatCompletionsWithOpenapiFunctions({ data })

      return completionResult.messages
    },

    async uploadOpenApiSpecs() {
      this.uploadOpenApiSpecsInProgress = true

      try {
        const parseResult = await this.chatCompletionStore.parseOpenapiSpec(this.files[0])
        this.parsedSpec = parseResult.api_spec
        this.tools = parseResult.tools
      } finally {
        this.uploadOpenApiSpecsInProgress = false
      }
    },

    clearChat() {
      this.allMessages = []
    },
  },
}
</script>
