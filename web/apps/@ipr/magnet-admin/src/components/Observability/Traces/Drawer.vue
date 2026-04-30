<template>
  <km-drawer-layout v-if="open" storage-key="drawer-observability-traces">
    <template #header>
      <div class="cluster km-heading-6 text-black" data-gap="xs">{{ span?.name }}</div>
      <div class="mt-sm" style="font-size: 13px">{{ span?.description }}</div>
      <div v-if="trace?.type == &quot;rag&quot; &amp;&amp; trace?.id == span?.parent_id &amp;&amp; trace?.spans?.[0]?.id == span?.id" class="stack mt-md" data-gap="2xl">
        <div class="stack" data-gap="xs">
          <div class="km-input-label text-text-grey">{{ m.common_question() }}</div>
          <div class="km-heading-2">{{ traceMetadata.question }}</div>
        </div>
        <div class="stack" data-gap="xs">
          <div class="km-input-label text-text-grey">{{ m.common_language() }}</div>
          <div class="km-heading-2">{{ traceMetadata.language }}</div>
        </div>
        <div class="stack" data-gap="xs">
          <div class="km-input-label text-text-grey">{{ m.common_chunksRetrieved() }}</div>
          <div class="km-heading-2">{{ traceMetadata.chunks_retrieved }}</div>
        </div>
        <div class="stack" data-gap="xs">
          <div class="km-input-label text-text-grey">{{ m.common_answer() }}</div>
          <div class="km-heading-2">{{ traceMetadata.answer }}</div>
        </div>
      </div>
    </template>
    <template #tabs>
      <km-tabs v-model="tab" narrow-indicator dense align="left" no-caps content-class="km-tabs">
        <template v-for="t in filteredTabs" :key="t">
          <km-tab :name="t.name" :label="t.label" />
        </template>
      </km-tabs>
    </template>
    <template v-if="tab == &quot;error&quot;">
      <div class="ba-border border-radius-8 p-sm bg-light" style="border-color: var(--ds-color-danger-solid); word-break: break-all; white-space: break-spaces">{{ span?.status_message }}</div>
    </template>
    <template v-else-if="tab == &quot;input_output&quot;">
      <template v-if="span?.type == &quot;search&quot;">
        <observability-traces-search-input-output :span="span" />
      </template>
      <template v-else-if="span?.type == &quot;embed&quot;">
        <observability-traces-embed-input-output :span="span" />
      </template>
      <template v-else-if="span?.type == &quot;chat&quot;">
        <observability-traces-chat-completion-input-output :span="span" />
      </template>
      <template v-else-if="span?.type == &quot;rerank&quot;">
        <observability-traces-rerank-input-output :span="span" />
      </template>
      <template v-else-if="span?.name == &quot;Fuse search results&quot;">
        <observability-traces-fuse-results-input-output :span="span" />
      </template>
      <template v-else-if="span?.name == &quot;Select top results&quot;">
        <observability-traces-top-results-input-output :span="span" />
      </template>
      <template v-else>
        <div v-if="span?.input || span?.output" class="stack" data-gap="3xl">
          <observability-traces-default-span-renderer :value="span?.input" :label="m.common_inputs()" />
          <observability-traces-default-span-renderer :value="span?.output" :label="m.common_outputs()" />
        </div>
      </template>
    </template>
    <template v-else-if="tab == &quot;prompt_template&quot;">
      <div class="stack" data-gap="2xl">
        <div class="stack" data-gap="xs">
          <div class="km-input-label text-text-grey">{{ m.common_name() }}</div>
          <div class="km-heading-2">{{ span?.prompt_template?.display_name }}</div>
        </div>
        <div v-if="span?.prompt_template?.variant" class="stack" data-gap="xs">
          <div class="km-input-label text-text-grey">{{ m.common_variant() }}</div>
          <div class="km-heading-2">{{ span?.prompt_template?.variant }}</div>
        </div>
      </div>
    </template>
    <template v-else-if="tab == &quot;tools&quot;">
      <div v-if="span?.extra_data?.tools &amp;&amp; span?.extra_data?.tools.length &gt; 0" class="stack" data-gap="3xl">
        <observability-traces-tools-list :tools="span?.extra_data?.tools" />
      </div>
    </template>
    <template v-else-if="tab == &quot;model&quot;">
      <div class="stack" data-gap="2xl">
        <div class="stack" data-gap="xs">
          <div class="km-input-label text-text-grey">{{ m.common_provider() }}</div>
          <div class="km-heading-2">{{ providerName }}</div>
        </div>
        <div class="stack" data-gap="xs">
          <div class="km-input-label text-text-grey">{{ m.common_llmName() }}</div>
          <div class="km-heading-2">{{ span?.model?.parameters?.llm }}</div>
        </div>
        <div v-if="span?.model?.parameters?.temperature != undefined" class="stack" data-gap="xs">
          <div class="km-input-label text-text-grey">{{ m.evaluation_temperature() }}</div>
          <div class="km-heading-2">{{ span?.model?.parameters?.temperature }}</div>
        </div>
        <div v-if="span?.model?.parameters?.top_p != undefined" class="stack" data-gap="xs">
          <div class="km-input-label text-text-grey">{{ m.common_topP() }}</div>
          <div class="km-heading-2">{{ span?.model?.parameters?.top_p }}</div>
        </div>
      </div>
    </template>
  </km-drawer-layout>
</template>

<script>
import { defineComponent, ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'

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
    const queries = useEntityQueries()
    const { data: providerData } = queries.provider.useList()
    const providerItems = computed(() => providerData.value?.items ?? [])

    return {
      m,
      tab: ref('input_output'),
      tabs: ref([
        { name: 'error', label: m.trace_tabError(), availableFor: [] },
        { name: 'input_output', label: m.trace_tabInputsOutputs(), availableFor: ['span', 'search', 'embed', 'rerank', 'chat', 'tool'] },
        { name: 'prompt_template', label: m.entity_promptTemplate(), availableFor: ['chat'] },
        { name: 'tools', label: m.common_tools(), availableFor: ['chat'] },
        { name: 'model', label: m.trace_tabModel(), availableFor: ['embed', 'rerank', 'chat'] },
      ]),
      providerItems,
    }
  },
  computed: {
    traceMetadata() {
      return this.trace?.extra_data || {}
    },
    filteredTabs() {
      return this.tabs.filter(
        (tab) =>
          (!this.span?.repeat_count &&
            tab.availableFor.includes(this.span?.type) &&
            (tab.name != 'input_output' || (tab.name == 'input_output' && (this.span?.input || this.span?.output)))) ||
          (tab.name === 'error' && this.span?.status === 'error')
      )
    },
    providerName() {
      const observationProviderName = this.span?.model?.provider
      const observationProviderDisplayName = this.span?.model?.provider_display_name
      const provider = (this.providerItems || []).find((option) => option.id == observationProviderName)
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
