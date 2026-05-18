<template>
  <div
    class="stack p-md"
    data-gap="0"
  >
    <div class="km-heading-3 text-center pb-md text-li">
      Upload 2 invoices (PDF) to get difference explanation
    </div>
    <div class="px-lg pt-lg bg-user-input-bg">
      <div
        class="cluster flex-"
        data-justify="between"
        data-gap="lg"
      >
        <km-file-picker
          v-model="files"
          class="km-control km-input rounded-borders"
          :multiple="true"
          max-files="2"
          style="block-size: var(--prompt-input-height); flex: 1; border-radius: var(--chip-radius)"
          outlined
          label="Upload Files"
          accept=".pdf,.docx,.doc,.pptx,.xlsx,.xls,.html,.htm,.txt,.md,.eml,.png,.jpg,.jpeg,.gif,.webp,.bmp,.tiff"
          dense
          label-class="km-heading-2"
        >
          <!--template(v-slot:append)
          //q-icon(name='attach')
          //km-btn(label='Run', @click='run', :disable='inProgress')
          -->
          <template #prepend>
            <template v-if="$theme === &quot;default&quot;">
              <km-glyph
                class="mr-sm"
                name="attach"
              />
            </template>
            <template v-else>
              <km-glyph
                name="attach"
                size="16px"
              />
            </template>
          </template>
          <template #append>
            <div class="self-center center-flex">
              <km-btn
                class="border-radius-6"
                :disable="inProgress"
                unelevated
                :padding="$theme != &quot;salesforce&quot; ? &quot;6px 7px&quot; : &quot;9px 17px 9px 17px&quot;"
                @click="run"
              >
                <template #default>
                  <km-glyph
                    name="search"
                    size="var(--prompt-input-icon-size)"
                  />
                </template>
              </km-btn>
            </div>
          </template>
        </km-file-picker>
      </div>
      <div
        class="cluster full-width"
        data-justify="end"
      >
        <div
          class="km-field"
          style="line-height: 18px"
        >
          File format: pdf
        </div>
      </div>
    </div>
    <template v-if="debugInfo">
      <div
        class="cluster full-width mt-sm"
        data-justify="end"
      >
        <km-btn
          class="rounded-borders"
          size="sm"
          flat
          :label="showDebugInfo ? &quot;Hide debug info&quot; : &quot;Show debug info&quot;"
          :icon="showDebugInfo ? &quot;chevron-up&quot; : &quot;chevron-down&quot;"
          @click="showDebugInfo = !showDebugInfo"
        />
      </div>
      <template v-if="showDebugInfo">
        <div class="mt-sm ba-border border-radius-12 bg-white p-lg">
          <div class="km-heading-2 mt-md">
            Text to JSON prompt template params:
            <km-codemirror
              v-model="debugInfo.promptTemplateTextToJson"
              :readonly="true"
              language="json"
            />
          </div>
          <div class="km-heading-2 mt-md">
            Explanation prompt template params:
            <km-codemirror
              v-model="debugInfo.promptTemplateExplain"
              :readonly="true"
              language="json"
            />
          </div>
          <div class="km-heading-2 mt-md">
            Invoices parsed content:
            <km-codemirror
              v-model="debugInfo.filesContent"
              :readonly="true"
              language="json"
            />
          </div>
          <div class="km-heading-2 mt-md">
            Invoices JSON content:
            <km-codemirror
              v-model="debugInfo.filesContentJson"
              :readonly="true"
              language="json"
            />
          </div>
        </div>
      </template>
    </template>
    <template v-if="inProgress">
      <div
        class="cluster full-width mt-sm"
        data-justify="center"
      >
        <km-loader
          size="31px"
        />
      </div>
    </template>
    <template v-if="answer">
      <div class="mt-sm ba-border border-radius-12 bg-white p-lg">
        <km-markdown :source="answer" />
      </div>
    </template>
  </div>
</template>

<script>
import { ref } from 'vue'
import { usePromptTemplates, useChatCompletion } from '@/pinia'
import { storeToRefs } from 'pinia'

export default {
  props: {
    promptTemplateSystemName: {
      type: String,
    },
    promptTemplateSystemNameTextToJson: {
      type: String,
    },
    promptTemplateSystemNameExplain: {
      type: String,
    },
  },
  setup() {
    const promptTemplatesStore = usePromptTemplates()
    const { items: promptTemplates } = storeToRefs(promptTemplatesStore)

    const chatCompletionStore = useChatCompletion()

    return {
      promptTemplates,
      files: ref([]),
      answer: ref(null),
      inProgress: ref(false),
      showDebugInfo: ref(false),
      filesContent: ref(null),
      filesContentJson: ref(null),
      promptTemplatesStore,
      chatCompletionStore,
    }
  },
  computed: {
    promptTemplateTextToJson() {
      return this.getPromptTemplate(this.promptTemplateSystemNameTextToJson)
    },
    promptTemplateExplain() {
      return this.getPromptTemplate(this.promptTemplateSystemNameExplain)
    },
    debugInfo() {
      return {
        promptTemplateTextToJson: JSON.stringify(this.promptTemplateTextToJson, null, 2),
        promptTemplateExplain: JSON.stringify(this.promptTemplateExplain, null, 2),
        filesContent: JSON.stringify(this.filesContent, null, 2),
        filesContentJson: JSON.stringify(this.filesContentJson, null, 2),
      }
    },
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },

    async run() {
      this.answer = null
      this.filesContent = null
      this.filesContentJson = null
      this.showDebugInfo = false

      if (!this.promptTemplateExplain) {
        throw Error('Explanation prompt template missing')
      }

      if (this.files?.length !== 2) {
        throw Error('Exactly 2 files should be picked')
      }

      this.inProgress = true

      try {
        let [invoice1, invoice2] = await Promise.all([
          await this.chatCompletionStore.parsePdf(this.files[0]),
          await this.chatCompletionStore.parsePdf(this.files[1]),
        ])

        this.filesContent = {
          invoice1,
          invoice2,
        }

        if (this.promptTemplateTextToJson) {
          const [invoice1Json, invoice2Json] = await Promise.all([await this.invoiceTextToJson(invoice1), await this.invoiceTextToJson(invoice2)])

          this.filesContentJson = {
            invoice1: invoice1Json,
            invoice2: invoice2Json,
          }
        }

        const promptTemplate = this.promptTemplateExplain
        const userMessage = JSON.stringify(this.filesContentJson ?? this.filesContent)

        const answer = await this.executePromptTemplate(promptTemplate, userMessage)

        this.answer = answer
      } finally {
        this.inProgress = false
      }
    },
    async invoiceTextToJson(invoiceParsed) {
      const promptTemplate = this.promptTemplateTextToJson
      const userMessage = invoiceParsed.pages.join('\n\n')

      const invoiceJson = await this.executePromptTemplate(promptTemplate, userMessage)

      return invoiceJson
    },
    async executePromptTemplate(promptTemplate, text) {
      const invoiceJson = await this.chatCompletionStore.enhanceText({
        prompt: promptTemplate.text,
        text,
        temperature: promptTemplate.temperature,
        topP: promptTemplate.topP,
        maxTokens: parseInt(promptTemplate.maxTokens),
        system_name_for_model: promptTemplate.system_name_for_model,
      })

      return invoiceJson
    },
    getPromptTemplate(systemName) {
      if (!systemName || !this.promptTemplates) {
        return null
      }

      const promptTemplate = this.promptTemplates.find((el) => el.system_name === systemName)

      if (!promptTemplate) {
        return null
      }

      const activeVariant = promptTemplate.variants.find((variant) => variant.variant === promptTemplate.active_variant)

      return {
        promptTemplate,
        ...activeVariant,
      }
    },
  },
}
</script>
