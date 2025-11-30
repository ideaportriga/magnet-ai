<template lang="pug">
<!-- Knowledge sources section -->
km-section(title='Knowledge sources', subTitle='Select one or multiple Knowledge sources to search')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 Knowledge sources
  km-select(
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
      q-separator.q-my-md
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Max number of chunks to retrieve for re-ranking
      div(style='max-width: 200px')
        km-input(type='number', height='30px', placeholder='Number of chunks to select', v-model='reRankingMaxChankRetrieve')
      .km-description.text-secondary-text.q-pb-4 If re-ranking is turned on, these chunks will be re-ordered to select the most relevant results.
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
km-section(title='Chunk limits', subTitle='Configure how chunks of content are retrieved and ranked')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 Number of chunks to select
  div(style='max-width: 200px')
    km-input(type='number', height='30px', placeholder='Number of chunks', v-model='maxChunksRetrieved')
  .km-description.text-secondary-text.q-pb-4 Max number of best retrieved chunks
</template>

<script>
import { isEqual, orderBy, pickBy } from 'lodash'
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
      reRankingLlmModel: ref(''),
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
        return this.$store.getters.retrievalVariant?.retrieve?.allow_metadata_filter || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'retrieve.allow_metadata_filter', value })
      },
    },
    useKeywordSearch: {
      get() {
        return this.$store.getters.retrievalVariant?.retrieve?.use_keyword_search || false
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'retrieve.use_keyword_search', value })
      },
    },
    isReRanking: {
      get() {
        return this.$store.getters.retrievalVariant?.retrieve?.rerank?.enabled || false
      },
      set(value) {
        console.log('value', value)
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'retrieve.rerank.enabled', value })
      },
    },
    reRankingModel: {
      get() {
        return this.$store.getters.retrievalVariant?.retrieve?.rerank?.model || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'retrieve.rerank.model', value })
      },
    },
    similarityScoreThreshold: {
      get() {
        return this.$store.getters.retrievalVariant?.retrieve?.similarity_score_threshold
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'retrieve.similarity_score_threshold', value })
      },
    },
    chunkContextWindowExpansionSize: {
      get() {
        return this.$store.getters.retrievalVariant?.retrieve?.chunk_context_window_expansion_size || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'retrieve.chunk_context_window_expansion_size', value })
      },
    },
    reRankingMaxChankRetrieve: {
      get() {
        return this.$store.getters.retrievalVariant?.retrieve?.rerank?.max_chunks_retrieved || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'retrieve.rerank.max_chunks_retrieved', value })
      },
    },
    maxChunksRetrieved: {
      get() {
        return this.$store.getters.retrievalVariant?.retrieve?.max_chunks_retrieved || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'retrieve.max_chunks_retrieved', value })
      },
    },
    collectionSystemNames: {
      get() {
        return this.collections.filter((el) =>
          (this.$store.getters.retrievalVariant?.retrieve?.collection_system_names || []).includes(el?.system_name)
        )
      },
      set(value) {
        value = (value || []).map((el) => {
          if (typeof el === 'string') {
            return el
          } else {
            return el?.system_name
          }
        })
        this.$store.dispatch('updateNestedRetrievalProperty', { path: 'retrieve.collection_system_names', value })
      },
    },

    hasChanges() {
      if (this.selectedRow?.id !== undefined) return !isEqual(this.prompt, this.selectedRow)
      else return true
    },
    hasError() {
      return !(this.prompt.name && this.prompt.text && this.prompt.description)
    },
    isNew() {
      return this.prompt && this.prompt.id === undefined
    },
    canSave() {
      return !!this.prompt.text && !!this.prompt.description && !!this.prompt.name
    },

    promptMetadata() {
      const views = this.$store.getters.views
      return Object.values(views).reduce((res, { entities }) => {
        Object.keys(entities).forEach((name) => {
          let controls = this.$store.getters.controls?.[name] ?? {}
          controls = pickBy(controls, (o) => o.fieldName || o.dataType)
          controls = orderBy(controls, ['label'])

          res[name] = { applet: entities[name], controls }
        })
        return res
      }, {})
    },

    metadataFields() {
      return this.promptMetadata[this.selectedEntity]?.controls ?? {}
    },
  },
  methods: {
    setProp(name, val) {
      this.$emit('setProp', { name, val })
    },
    save() {
      if (this.hasError) {
        this.showError = true
        return
      }
      this.showError = false
      this.$emit('save')
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
  },
}
</script>
