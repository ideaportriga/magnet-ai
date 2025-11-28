<template lang="pug">
.column.q-pa-md
  .km-heading-3.text-center.q-pb-md.text-li Upload 2 invoices (PDF) to get difference explanation
  .q-px-16.q-pt-16.bg-user-input-bg
    .row.justify-between.items-center.q-gap-16.flex-
      q-file.km-control.km-input.rounded-borders(
        :multiple='true',
        max-files='2',
        style='height: var(--prompt-input-height); flex: 1; border-radius: var(--chip-radius)',
        outlined,
        label='Upload Files',
        v-model='files',
        accept='.pdf',
        dense,
        labelClass='km-heading-2'
      )
        //template(v-slot:append)
          //q-icon(name='attach_file')
          //km-btn(label='Run', @click='run', :disable='inProgress')
        template(#prepend)
          template(v-if='$theme === "default"')
            q-icon.q-mr-8(name='attach_file')
          template(v-else)
            km-icon.q-mr-8(name='attach_file', :width='$theme === "salesforce" ? "16" : "24"', :height='$theme === "salesforce" ? "16" : "24"')
        template(#append)
          .self-center.center-flex
            q-btn.border-radius-6(
              color='primary',
              @click='run',
              :disable='inProgress',
              unelevated,
              :padding='$theme != "salesforce" ? "6px 7px" : "9px 17px 9px 17px"'
            )
              template(v-slot:default)
                q-icon(name='fas fa-search', size='var(--prompt-input-icon-size)')
    .row.justify-end.full-width
      .km-field(style='line-height: 18px') File format: pdf
  template(v-if='debugInfo')
    .row.justify-end.full-width.q-mt-sm
      km-btn.rounded-borders(
        size='sm',
        flat,
        :label='showDebugInfo ? "Hide debug info" : "Show debug info"',
        :icon='showDebugInfo ? "arrow_drop_up" : "arrow_drop_down"',
        @click='showDebugInfo = !showDebugInfo'
      )
    template(v-if='showDebugInfo')
      .q-mt-sm.border.border-radius-12.bg-white.q-pa-lg.q-pa-lg
        .km-heading-2.q-mt-md Text to JSON prompt template params:
          km-codemirror(v-model='debugInfo.promptTemplateTextToJson', :readonly='true', language='json')
        .km-heading-2.q-mt-md Explanation prompt template params:
          km-codemirror(v-model='debugInfo.promptTemplateExplain', :readonly='true', language='json')
        .km-heading-2.q-mt-md Invoices parsed content:
          km-codemirror(v-model='debugInfo.filesContent', :readonly='true', language='json')
        .km-heading-2.q-mt-md Invoices JSON content:
          km-codemirror(v-model='debugInfo.filesContentJson', :readonly='true', language='json')

  template(v-if='inProgress')
    .row.full-width.justify-center.q-mt-sm
      q-spinner-dots(size='31px', color='primary')
  template(v-if='answer')
    .q-mt-sm.border.border-radius-12.bg-white.q-pa-lg
      km-markdown(:source='answer')
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
