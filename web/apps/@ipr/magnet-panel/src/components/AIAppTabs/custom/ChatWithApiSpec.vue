<template>
  <div
    class="flex-1 p-md full-height bg-light flex"
    style="justify-content: center"
  >
    <div
      class="stack full-width"
      data-gap="0"
      style="max-inline-size: 800px"
    >
      <div
        class="flex-none cluster"
        data-justify="between"
        data-gap="lg"
      >
        <div class="flex-1">
          <div class="km-field text-secondary-text pb-xs pl-sm">
            {{ m.panel_openApiSpec() }}
          </div>
          <km-file-picker
            v-model="files"
            class="km-control km-input rounded-borders"
            :multiple="true"
            max-files="1"
            style="block-size: var(--prompt-input-height); flex: 1; border-radius: var(--chip-radius)"
            outlined
            accept=".json, .yml"
            :disable="uploadOpenApiSpecsInProgress"
            dense
            label-class="km-heading-2"
          >
            <template #prepend>
              <km-glyph
                class="mr-sm"
                name="attach"
              />
            </template>
            <template #append>
              <div class="self-center center-flex">
                <km-btn
                  class="border-radius-6"
                  :disable="uploadOpenApiSpecsInProgress"
                  unelevated
                  padding="6px 7px"
                  @click="uploadOpenApiSpecs"
                >
                  <template #default>
                    <km-glyph
                      name="upload"
                      size="var(--prompt-input-icon-size)"
                    />
                  </template>
                </km-btn>
              </div>
            </template>
          </km-file-picker>
        </div>
      </div>
      <div
        class="cluster full-width mt-sm"
        data-justify="end"
      >
        <km-btn
          class="rounded-borders"
          size="sm"
          flat
          :label="showAuthParams ? m.panel_hideAuthParams() : m.panel_showAuthParams()"
          :icon="showAuthParams ? &quot;chevron-up&quot; : &quot;chevron-down&quot;"
          @click="showAuthParams = !showAuthParams"
        />
      </div>
      <template v-if="showAuthParams">
        <div class="flex-none">
          <km-input
            rows="5"
            :model-value="authParams"
            border-radius="8px"
            height="36px"
            type="textarea"
            @input="authParams = $event"
          />
        </div>
      </template>
      <template v-if="uploadOpenApiSpecsInProgress">
        <div
          class="flex-none flex"
          style="justify-content: center"
        >
          <km-loader
            size="62px"
          />
        </div>
      </template>
      <div class="flex-none">
        <div
          class="cluster"
          data-gap="lg"
          data-wrap="no"
        >
          <template v-if="parsedSpec">
            <km-btn
              tone="brand"
              link
              @click="showParsedSpec = true"
            >
              {{ m.panel_viewParsedSpec() }}
            </km-btn>
          </template>
          <template v-if="tools">
            <km-btn
              tone="brand"
              link
              @click="showTools = true"
            >
              {{ m.panel_viewFunctionTools() }}
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
          class="flex-none flex"
          style="justify-content: center"
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
      :visible="showParsedSpec"
      title="Parsed spec"
      cancel-button-label="Cancel"
      @cancel="showParsedSpec = false"
    >
      <div
        class="cluster pt-sm pl-sm"
        data-justify="between"
      >
        <div class="basis-12 py-sm">
          <km-codemirror
            v-model="parsedSpecString"
            :readonly="true"
            language="json"
          />
        </div>
      </div>
    </km-popup-confirm>
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
