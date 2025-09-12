<template lang="pug">
.no-wrap.full-height.justify-center.q-py-16.q-pl-16.q-pr-xs.bg-white.fit.relative-position.bl-border(
  style='max-width: 500px; min-width: 500px !important',
  v-if='open'
)
  .column.full-height.no-wrap
    .row.q-gap-4.items-center.km-heading-6.text-black.q-mb-md {{ span?.name }}
    .row.q-mb-sm(style='font-size: 13px') {{ span?.description }}
    .column.q-gap-24(v-if='trace?.type == "rag" && trace?.id == span?.parent_id && trace?.spans?.[0]?.id == span?.id')
      .column.q-gap-6
        .km-input-label.text-text-grey Question
        .km-heading-2 {{ traceMetadata.question }}
      .column.q-gap-6
        .km-input-label.text-text-grey Language
        .km-heading-2 {{ traceMetadata.language }}
      .column.q-gap-6
        .km-input-label.text-text-grey Chunks retrieved
        .km-heading-2 {{ traceMetadata.chunks_retrieved }}
      .column.q-gap-6
        .km-input-label.text-text-grey Answer
        .km-heading-2 {{ traceMetadata.answer }}
    .row.q-mb-md
      q-tabs(
        v-model='tab',
        narrow-indicator,
        dense,
        align='left',
        active-color='primary',
        indicator-color='primary',
        no-caps,
        content-class='km-tabs'
      )
        template(v-for='t in filteredTabs')
          q-tab(:name='t.name', :label='t.label')
    q-scroll-area.fit.q-pr-md
      template(v-if='tab == "error"')
        .row.ba-border.border-radius-8.q-pa-sm.bg-light(style='border-color: #ff0000; word-break: break-all; white-space: break-spaces') {{ span?.status_message }}
      template(v-else-if='tab == "input_output"')
        template(v-if='span?.type == "search"')
          observability-traces-vector-search-input-output(:span='span')
        template(v-else-if='span?.type == "embed"')
          observability-traces-embed-input-output(:span='span')
        template(v-else-if='span?.type == "chat"')
          observability-traces-chat-completion-input-output(:span='span')
        template(v-else-if='span?.type == "rerank"')
          observability-traces-rerank-input-output(:span='span')
        template(v-else)
          .column.q-gap-32(v-if='span?.input || span?.output')
            observability-traces-default-span-renderer(:value='span?.input', label='Inputs')
            observability-traces-default-span-renderer(:value='span?.output', label='Outputs')
      template(v-else-if='tab == "prompt_template"')
        .column.q-gap-24
          .column.q-gap-6
            .km-input-label.text-text-grey Name
            .km-heading-2 {{ span?.prompt_template?.display_name }}
          .column.q-gap-6(v-if='span?.prompt_template?.variant')
            .km-input-label.text-text-grey Variant
            .km-heading-2 {{ span?.prompt_template?.variant }}
      template(v-else-if='tab == "model"')
        .column.q-gap-24
          .column.q-gap-6
            .km-input-label.text-text-grey Provider
            .km-heading-2 {{ providerName }}
          .column.q-gap-6
            .km-input-label.text-text-grey LLM name
            .km-heading-2 {{ span?.model?.parameters?.llm }}
          .column.q-gap-6(v-if='span?.model?.parameters?.temperature != undefined')
            .km-input-label.text-text-grey Temperature
            .km-heading-2 {{ span?.model?.parameters?.temperature }}
          .column.q-gap-6(v-if='span?.model?.parameters?.top_p != undefined')
            .km-input-label.text-text-grey Top P
            .km-heading-2 {{ span?.model?.parameters?.top_p }}
</template>

<script>
import { defineComponent, ref } from 'vue'
import store from '@/store'

export default defineComponent({
  props: {
    open: Boolean,
    trace: {
      type: Object,
      default: () => ({}),
    },
    span: {
      type: Object,
      default: () => ({}),
    },
  },
  setup() {
    return {
      tab: ref('input_output'),
      tabs: ref([
        { name: 'error', label: 'Error', availableFor: [] },
        { name: 'input_output', label: 'Inputs & Outputs', availableFor: ['span', 'search', 'embed', 'rerank', 'chat', 'tool'] },
        { name: 'prompt_template', label: 'Prompt Template', availableFor: ['chat'] },
        { name: 'model', label: 'Model', availableFor: ['embed', 'rerank', 'chat'] },
      ]),
    }
  },
  computed: {
    traceMetadata() {
      return this.trace?.extra_data || {}
    },
    filteredTabs() {
      return this.tabs.filter(
        (tab) =>
          (!this.span?.repeat_count && tab.availableFor.includes(this.span?.type) &&
            (tab.name != 'input_output' || (tab.name == 'input_output' && (this.span?.input || this.span?.output)))) ||
          (tab.name === 'error' && this.span?.status === 'error')
      )
    },
    providerName() {
      const observationProviderName = this.span?.model?.provider
      const observationProviderDisplayName = this.span?.model?.provider_display_name
      const provider = (store.getters['chroma/provider'].items || []).find((option) => option.id == observationProviderName)
      return provider?.label || observationProviderDisplayName || observationProviderName
    },
  },
  watch: {
    span: {
      handler() {
        if (this.span?.status === 'error') {
          this.tab = 'error'
        } else {
          this.tab = 'input_output'
        }
      },
    },
  },
})
</script>
