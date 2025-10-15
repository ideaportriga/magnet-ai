<template lang="pug">
<!-- Knowledge sources section -->
km-section(title='Knowledge sources', subTitle='Select one or multiple Knowledge sources to ground your RAG.')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 Knowledge sources
  km-select(
    data-test='knowledge-sources',
    height='auto',
    minHeight='36px',
    placeholder='Select knowledge sources',
    multiple,
    :options='collections',
    v-model='collectionSystemNames',
    use-chips,
    hasDropdownSearch
  )
  .row.q-mt-sm
    .col-auto
      km-btn(flat, simple, label='Open Knowledge sources', iconSize='16px', icon='fas fa-book', @click='navigate("knowledge-sources")')
q-separator.q-my-lg

<!-- Search capabilities section -->
km-section(
  title='Search capabilities',
  subTitle='Configure how search will be performed. To activate hybrid search, enable both semantic and keyword search.'
)
  .column.q-gap-16
    .column
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='allowMetadataFilter', dense)
        .col.q-mb-sm Allow metadata filtering
      .km-description.text-secondary-text.q-mt-xs.q-ml-sm Allow to use filtering by metadata to exclude documents, that are not relevant to the search.
    .column
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(:model-value='true', disable, dense)
        .col.q-mb-sm Use semantic (vector) search
      .km-description.text-secondary-text.q-mt-xs.q-ml-sm Use vector embeddings to search documents semantically, based on their meaning rather than just exact matches. Currently, cannot be turned off.
    .column
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='useKeywordSearch', dense)
        .col.q-mb-sm Use keyword search
      .km-description.text-secondary-text.q-mt-xs.q-ml-sm Use direct keyword matching. Note that keyword search capabilities depend on the underlying database implementation.
q-separator.q-my-lg

<!-- Semantic cache section -->
km-section(title='Semantic cache', subTitle='Semantic caching helps improve performance and maintain high response quality')
  .column
    .col.q-mb-md
      q-chip.km-small-chip(color='primary-light', text-color='primary', label='Upcoming feature')
    .col
      q-toggle(v-model='semanticCache', disable, dense) 
q-separator.q-my-lg

<!-- Re-ranking section -->
km-section(
  title='Re-ranking',
  subTitle='Re-ranking significantly improves search results by selecting most relevant chunks in two steps. Makes an extra call to LLM.'
)
  .column
    .col
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='isReRanking', dense)
        .col.q-mb-sm Re-rank with LLM
    .col
    template(v-if='isReRanking')
      .col.q-mt-md
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 LLM model
        km-select(
          height='auto',
          minHeight='36px',
          placeholder='Re-rank Model',
          v-model='reRankingModel',
          :options='modelOptions',
          optionLabel='display_name',
          emit-value,
          mapOptions,
          optionValue='system_name'
        )
          template(#option='{ itemProps, opt, selected, toggleOption }')
            q-item.ba-border(v-bind='itemProps', dense, @click='toggleOption(opt)')
              q-item-section
                q-item-label.km-label {{ opt.display_name }}
                .row.q-mt-xs(v-if='opt.provider_system_name')
                  q-chip(color='primary-light', text-color='primary', size='sm', dense) {{ opt.provider_system_name }}
        .km-field.text-secondary-text Use LLM to rank candidate results. Makes extra calls to LLM
q-separator.q-my-lg

<!-- Similarity score section -->
km-section(title='Similarity score', subTitle='How strictly a user query should match retrieved documents.')
  km-slider-card(
    v-model='similarityScoreThreshold',
    name='Similarity score threshold',
    :min='0',
    :max='1',
    minLabel='Unrelated',
    maxLabel='Similar',
    :defaultValue='0.75',
    description='Minimum similarity score needed for a chunk to be retrieved. We recommend using lower threshold if re-ranking is on.'
  )
q-separator.q-my-lg

<!-- Chunk limits section -->
km-section(title='Chunk limits', subTitle='Control how many chunks are passed to the language model')
  template(v-if='isReRanking')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Max number of chunks to retrieve for re-ranking
    div(style='max-width: 200px')
      km-input(type='number', height='30px', placeholder='Number of chunks to select', v-model='reRankingMaxChankRetrieve')
    .km-description.text-secondary-text.q-pb-4 If re-ranking is turned on, these chunks will be re-ordered to select the most relevant results.

    q-separator.q-my-lg
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 Number of chunks to select
  div(style='max-width: 200px')
    km-input(type='number', height='30px', placeholder='Number of chunks to select', v-model='maxChunksRetrieved')
  .km-description.text-secondary-text.q-pb-4 Max number of best retrieved chunks to send to LLM
  q-separator.q-my-lg
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 Number of added chunks
  div(style='max-width: 200px')
    km-input(type='number', height='30px', placeholder='Context window expansion size', v-model='chunkContextWindowExpansionSize')
  .km-description.text-secondary-text.q-pb-4 Number of chunks to add before and after each chunk when sending to LLM for better context understanding
</template>

<script>
import { ref } from 'vue'
import { useChroma } from '@shared'

export default {
  props: ['prompt', 'selectedRow'],
  emits: ['setProp', 'save', 'cancel', 'remove', 'openTest'],

  setup() {
    const { publicItems, publicSelected, publicSelectedOptionsList } = useChroma('collections')

    return {
      publicItems,
      publicSelected,
      publicSelectedOptionsList,
      test: ref(true),
      iconPicker: ref(false),
      showError: ref(false),
      selectedEntity: ref(),
      promptInput: ref(null),
      llm: ref(true),
      semanticCache: ref(false),
      reRankingChoice: ref('cross'),
      reRankingCrossModel: ref(''),
      cacheCollection: ref('Helpdesk Cache'),
      allowBypassCache: ref(false),
      collections: publicItems,
    }
  },
  computed: {
    modelOptions() {
      return (this.$store.getters['chroma/model'].items || []).filter((el) => el.type === 're-ranking')
    },
    allowMetadataFilter: {
      get() {
        return this.$store.getters.ragVariant?.retrieve?.allow_metadata_filter || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'retrieve.allow_metadata_filter', value })
      },
    },
    useKeywordSearch: {
      get() {
        return this.$store.getters.ragVariant?.retrieve?.use_keyword_search || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'retrieve.use_keyword_search', value })
      },
    },
    isReRanking: {
      get() {
        return this.$store.getters.ragVariant?.retrieve?.rerank?.enabled || false
      },
      set(value) {
        console.log('value', value)
        this.$store.dispatch('updateNestedRagProperty', { path: 'retrieve.rerank.enabled', value })
      },
    },
    reRankingModel: {
      get() {
        return this.$store.getters.ragVariant?.retrieve?.rerank?.model || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'retrieve.rerank.model', value })
      },
    },
    reRankingMaxChankRetrieve: {
      get() {
        return this.$store.getters.ragVariant?.retrieve?.rerank?.max_chunks_retrieved || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'retrieve.rerank.max_chunks_retrieved', value })
      },
    },
    similarityScoreThreshold: {
      get() {
        return this.$store.getters.ragVariant?.retrieve?.similarity_score_threshold
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'retrieve.similarity_score_threshold', value })
      },
    },
    chunkContextWindowExpansionSize: {
      get() {
        return this.$store.getters.ragVariant?.retrieve?.chunk_context_window_expansion_size || 0
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'retrieve.chunk_context_window_expansion_size', value })
      },
    },
    maxChunksRetrieved: {
      get() {
        return this.$store.getters.ragVariant?.retrieve?.max_chunks_retrieved || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedRagProperty', { path: 'retrieve.max_chunks_retrieved', value })
      },
    },
    collectionSystemNames: {
      get() {
        return this.collections.filter((el) => (this.$store.getters.ragVariant?.retrieve?.collection_system_names || []).includes(el?.system_name))
      },
      set(value) {
        console.log('value', value)
        value = (value || []).map((el) => {
          if (typeof el === 'string') {
            return el
          } else {
            return el?.system_name
          }
        })
        this.$store.dispatch('updateNestedRagProperty', { path: 'retrieve.collection_system_names', value })
      },
    },
  },
  methods: {
    setProp(name, val) {
      this.$emit('setProp', { name, val })
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
  },
}
</script>
