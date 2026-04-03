<template lang="pug">
.q-pr-md
  km-section(title='Source settings', subTitle='Content source route and parameters')
    .col.q-pt-8
      .km-input-label.q-pb-xs.q-pl-8 Source type
      km-select(
        :options='dynamicSourceTypeOptions',
        v-model='source_type',
        ref='source_typeRef',
        :rules='config.source_type.rules',
        :disabled='isDisable'
      )
    template(v-for='item in dynamicSourceTypeChildren[source_type]')
      .col.q-pt-8
        .km-input-label.q-pb-xs.q-pl-8 {{ item.label }}
          .km-description.text-secondary-text(v-if='item?.description') {{ item?.description }}
        component(:is='item.component', v-model='source_fields[item.field]', :readonly='isDisable', :disable='isDisable')
  <!-- CHUNKING -->
  q-separator.q-my-lg
  km-section(:title='m.section_chunking()', :subTitle='m.collections_chunkingSubtitle()')
    .column.q-gap-16
      .col
        .km-input-label.q-pb-xs Chunking strategy
        km-select(
          v-model='chunkingStrategy',
          :options='config.chunking_strategy.options',
          emit-value,
          map-options,
          option-value='value',
          option-label='label',
          :disabled='isDisable'
        )
        .km-description.text-secondary-text.q-mt-xs.q-ml-xs Chunking strategy defines how documents are divided into smaller chunks for better search results.
      .row.q-gap-16(v-if='chunkingStrategy === "recursive_character_text_splitting"')
        .col
          .km-input-label.q-pb-xs Chunk size
          km-input(v-model='chunkSize', type='number', :readonly='isDisable')
          .km-description.text-secondary-text.q-mt-xs.q-ml-xs Defines the maximum number of characters in each chunk when splitting.
        .col
          .km-input-label.q-pb-xs Chunk overlap
          km-input(v-model='chunkOverlap', type='number', :readonly='isDisable')
          .km-description.text-secondary-text.q-mt-xs.q-ml-xs Defines the overlap (in characters) between chunks when splitting.
      .col.q-mt-sm
        .row.items-baseline
          .col-auto.q-mr-sm
            q-toggle(v-model='chunkTransformationEnabled', dense, :disable='isDisable')
          .col Enable chunk LLM transformation
      .column.q-gap-16(v-if='chunkTransformationEnabled')
        .col
          km-select(
            v-model='chunkTransformationPromptTemplate',
            :options='chunkTransformationPromptTemplateOptions',
            hasDropdownSearch,
            emit-value,
            map-options,
            option-value='system_name',
            :disabled='isDisable'
          )
          .km-description.text-secondary-text.q-mt-xs.q-ml-xs Transforms document chunks before embedding to improve search quality. Note that this transformation can greatly increase latency and cost.
          .row.q-mt-sm
            .col-auto
              km-btn(
                :label='chunkTransformationPromptTemplate ? "Open Prompt Template" : "Open Prompt Templates Library"',
                iconSize='16px',
                icon='fas fa-comment-dots',
                @click='chunkTransformationPromptTemplate ? navigate(`prompt-templates/${chunkTransformationPromptTemplateId}`) : navigate("prompt-templates")'
              )
        .col
          .km-input-label.q-pb-xs How to apply transformation
          km-select(
            v-model='chunkTransformationMethod',
            :options='config.chunk_transformation_method.options',
            emit-value,
            map-options,
            option-value='value',
            option-label='label',
            :disabled='isDisable'
          )
          .km-description.text-secondary-text.q-mt-xs.q-ml-xs Defines how transformation is applied to the chunk. For example, you can prepend/append generated text to the chunk, or replace chunk content entirely.
        .col
          .km-input-label.q-pb-xs How to use chunks
          km-select(
            v-model='chunkUsageMethod',
            :options='config.chunk_usage_method.options',
            emit-value,
            map-options,
            option-value='value',
            option-label='label',
            :disabled='isDisable'
          )
          .km-description.text-secondary-text.q-mt-xs.q-ml-xs Defines which chunk is used for indexing and which for retrieval.

  <!-- INDEXING -->
  q-separator.q-my-lg
  km-section(:title='m.section_indexing()', :subTitle='m.collections_indexingSubtitle()')
    .column.q-gap-16
      .km-description.q-mt-sm Enabling both semantic search and keyword search activates hybrid search, which combines the benefits of both approaches, but will increase latency and cost of the search and the source sync.
      .col
        .row.items-baseline
          .col-auto.q-mr-sm
            q-toggle(v-model='supportSemanticSearch', dense, :disable='true')
          .col Support semantic search
        .km-description.text-secondary-text.q-mt-sm Create vector embeddings to support semantic search, which allows you to search for documents based on their meaning rather than just exact matches. Currently, cannot be turned off.
      .col(v-if='supportSemanticSearch')
        .km-input-label.q-pb-xs Embedding model
        km-select(
          v-model='embeddingModel',
          placeholder='Embedding Model',
          :options='embeddingModelOptions',
          optionValue='system_name',
          optionLabel='display_name',
          emit-value,
          mapOptions,
          :disabled='isDisable'
        )
          template(#option='{ itemProps, opt, selected, toggleOption }')
            q-item.ba-border(v-bind='itemProps', dense, @click='toggleOption(opt)')
              q-item-section
                q-item-label.km-label {{ opt.display_name }}
                .row.q-mt-xs(v-if='opt.provider_system_name')
                  q-chip(color='primary-light', text-color='primary', size='sm', dense) {{ opt.provider_system_name }}
      .col.q-mt-sm
        .row.items-baseline
          .col-auto.q-mr-sm
            q-toggle(v-model='supportKeywordSearch', dense)
          .col Support keyword search
        .km-description.text-secondary-text.q-mt-sm Toggling this option enables direct keyword matching, which can be beneficial for some use cases. Note that keyword search capabilities depend on the underlying database implementation.
</template>

<script setup>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useRouter, useRoute } from 'vue-router'
import { useEntityConfig } from '@/composables/useEntityConfig'
import { useEntityQueries } from '@/queries/entities'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { sourceTypeOptions, sourceTypeChildren } from '@/config/collections/collections'
import FileUrlUpload from '@/components/Collections/FileUrlUpload.vue'

const router = useRouter()
const route = useRoute()
const { config } = useEntityConfig('collections')
const queries = useEntityQueries()
const { draft, updateField } = useEntityDetail('collections')
const { data: promptTemplateListData } = queries.promptTemplates.useList()
const { data: modelListData } = queries.model.useList()

// Dynamic source type options from loaded plugins
const dynamicSourceTypeOptions = computed(() => sourceTypeOptions.value || [])
const dynamicSourceTypeChildren = computed(() => sourceTypeChildren.value || {})

const isDisable = computed(() => {
  if (!draft.value?.last_synced) return false
  const d = new Date(draft.value.last_synced)
  return !isNaN(d.getTime())
})

const source_fields = computed({
  get() {
    const source = draft.value?.source || {}

    // Transform Documentation arrays to comma-separated strings for display
    if (source.source_type === 'Documentation') {
      const transformed = { ...source }

      // Convert languages array to string
      if (Array.isArray(transformed.languages)) {
        transformed.languages = transformed.languages.join(', ')
      }

      // Convert sections array to string
      if (Array.isArray(transformed.sections)) {
        transformed.sections = transformed.sections.join(', ')
      }

      return transformed
    }

    return source
  },
  set(value) {
    updateField('source', value)
  },
})

const source_type = computed({
  get() { return draft.value?.source?.source_type || '' },
  set(value) { updateField('source', { ...(draft.value?.source || {}), source_type: value }) },
})

// Chunking settings
const chunkingStrategy = computed({
  get() { return draft.value?.chunking?.strategy || 'recursive_character_text_splitting' },
  set(value) { updateField('chunking.strategy', value) },
})
const chunkSize = computed({
  get() {
    const val = draft.value?.chunking?.chunk_size
    return val != null ? String(val) : ''
  },
  set(value) { updateField('chunking.chunk_size', parseInt(value)) },
})
const chunkOverlap = computed({
  get() {
    const val = draft.value?.chunking?.chunk_overlap
    return val != null ? String(val) : ''
  },
  set(value) { updateField('chunking.chunk_overlap', parseInt(value)) },
})
const chunkTransformationEnabled = computed({
  get() { return draft.value?.chunking?.transformation_enabled || false },
  set(value) { updateField('chunking.transformation_enabled', value) },
})
const chunkTransformationPromptTemplate = computed({
  get() { return draft.value?.chunking?.transformation_prompt_template || '' },
  set(value) { updateField('chunking.transformation_prompt_template', value) },
})
const chunkTransformationMethod = computed({
  get() { return draft.value?.chunking?.transformation_method || '' },
  set(value) { updateField('chunking.transformation_method', value) },
})
const chunkUsageMethod = computed({
  get() { return draft.value?.chunking?.chunk_usage_method || '' },
  set(value) { updateField('chunking.chunk_usage_method', value) },
})

const promptTemplateItems = computed(() => promptTemplateListData.value?.items ?? [])
const chunkTransformationPromptTemplateOptions = computed(() =>
  (promptTemplateItems.value ?? []).map((item) => ({
    label: item.name,
    value: item.id,
    system_name: item.system_name,
    category: item?.category,
    id: item.id,
  }))
)
const chunkTransformationPromptTemplateId = computed(() =>
  chunkTransformationPromptTemplateOptions.value.find((el) => el.system_name == chunkTransformationPromptTemplate.value)?.id
)

// Indexing settings
const supportSemanticSearch = computed({
  get() {
    if (!draft.value?.indexing) return true
    return draft.value?.indexing?.semantic_search_supported || false
  },
  set(value) { updateField('indexing.semantic_search_supported', value) },
})
const embeddingModel = computed({
  get() { return draft.value?.ai_model || '' },
  set(value) { updateField('ai_model', value) },
})
const embeddingModelOptions = computed(() =>
  (modelListData.value?.items ?? []).filter((el) => el.type === 'embeddings')
)
const supportKeywordSearch = computed({
  get() { return draft.value?.indexing?.fulltext_search_supported || false },
  set(value) { updateField('indexing.fulltext_search_supported', value) },
})

function navigate(path = '') {
  if (route.path !== `/${path}`) {
    router.push(`/${path}`)
  }
}
</script>
