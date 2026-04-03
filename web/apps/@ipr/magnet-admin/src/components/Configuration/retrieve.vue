<template lang="pug">
<!-- Knowledge sources section -->
km-section(:title='m.label_knowledgeSources()', :subTitle='m.subtitle_selectKnowledgeSourcesRag()')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.label_knowledgeSources() }}
  km-select(
    data-test='knowledge-sources',
    height='auto',
    minHeight='36px',
    :placeholder='m.common_selectKnowledgeSources()',
    multiple,
    :options='collections',
    v-model='collectionSystemNames',
    use-chips,
    hasDropdownSearch
  )
  .row.q-mt-sm
    .col-auto
      km-btn(flat, simple, :label='m.common_openKnowledgeSources()', iconSize='16px', icon='fas fa-book', @click='navigate("knowledge-sources")')
q-separator.q-my-lg

<!-- Search capabilities section -->
km-section(
  :title='m.ragTools_searchCapabilities()',
  :subTitle='m.subtitle_configureSearch()'
)
  .column.q-gap-16
    .column
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='allowMetadataFilter', dense)
        .col.q-mb-sm {{ m.ragTools_allowMetadataFiltering() }}
      .km-description.text-secondary-text.q-mt-xs.q-ml-sm {{ m.ragTools_allowMetadataFilteringDesc() }}
    .column
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(:model-value='true', disable, dense)
        .col.q-mb-sm {{ m.ragTools_useSemanticSearch() }}
      .km-description.text-secondary-text.q-mt-xs.q-ml-sm {{ m.ragTools_useSemanticSearchDesc() }}
    .column
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='useKeywordSearch', dense)
        .col.q-mb-sm {{ m.ragTools_useKeywordSearch() }}
      .km-description.text-secondary-text.q-mt-xs.q-ml-sm {{ m.ragTools_useKeywordSearchDesc() }}
q-separator.q-my-lg

<!-- Semantic cache section -->
km-section(:title='m.section_semanticCache()', :subTitle='m.subtitle_semanticCache()')
  .column
    .col.q-mb-md
      q-chip.km-small-chip(color='primary-light', text-color='primary', :label='m.common_upcomingFeature()')
    .col
      q-toggle(v-model='semanticCache', disable, dense) 
q-separator.q-my-lg

<!-- Re-ranking section -->
km-section(
  :title='m.ragTools_reRanking()',
  :subTitle='m.subtitle_reranking()'
)
  .column
    .col
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='isReRanking', dense)
        .col.q-mb-sm {{ m.ragTools_reRankWithLlm() }}
    .col
    template(v-if='isReRanking')
      .col.q-mt-md
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_llmModel() }}
        km-select(
          height='auto',
          minHeight='36px',
          :placeholder='m.common_reRankModel()',
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
        .km-field.text-secondary-text {{ m.ragTools_useLlmToRank() }}
      q-separator.q-my-md
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.ragTools_maxChunksForReranking() }}
      div(style='max-width: 200px')
        km-input(type='number', height='30px', :placeholder='m.common_numberOfChunksToSelect()', v-model='reRankingMaxChankRetrieve')
      .km-description.text-secondary-text.q-pb-4 {{ m.ragTools_rerankingChunksDesc() }}

q-separator.q-my-lg

<!-- Similarity score section -->
km-section(:title='m.section_similarityScore()', :subTitle='m.subtitle_similarityScore()')
  km-slider-card(
    v-model='similarityScoreThreshold',
    :name='m.ragTools_similarityScoreThreshold()',
    :min='0',
    :max='1',
    :minLabel='m.ragTools_unrelated()',
    :maxLabel='m.ragTools_similar()',
    :defaultValue='0.75',
    :description='m.ragTools_similarityScoreDesc()'
  )
q-separator.q-my-lg

<!-- Chunk limits section -->
km-section(:title='m.section_chunkLimits()', :subTitle='m.subtitle_controlChunks()')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.ragTools_numberOfChunksToSelect() }}
  div(style='max-width: 200px')
    km-input(type='number', height='30px', :placeholder='m.common_numberOfChunksToSelect()', v-model='maxChunksRetrieved')
  .km-description.text-secondary-text.q-pb-4 {{ m.ragTools_maxChunksToLlm() }}
  q-separator.q-my-lg
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.ragTools_numberOfAddedChunks() }}
  div(style='max-width: 200px')
    km-input(type='number', height='30px', :placeholder='m.common_numberOfChunksToSelect()', v-model='chunkContextWindowExpansionSize')
  .km-description.text-secondary-text.q-pb-4 {{ m.ragTools_addedChunksDesc() }}
</template>

<script>
import { m } from '@/paraglide/messages'
import { ref, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'

export default {
  props: ['prompt', 'selectedRow'],
  emits: ['setProp', 'save', 'cancel', 'remove', 'openTest'],

  setup() {
    const queries = useEntityQueries()
    const { activeVariant, updateVariantField } = useVariantEntityDetail('rag_tools')
    const { options: catalogCollections } = useCatalogOptions('collections')
    const { data: modelListData } = queries.model.useList()

    return {
      m,
      activeVariant,
      updateVariantField,
      catalogCollections,
      modelListData,
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
    }
  },
  computed: {
    collections() {
      return this.catalogCollections.map((item) => ({
        ...item,
        value: item.id,
        label: item.name,
      }))
    },
    modelOptions() {
      return (this.modelListData?.items ?? []).filter((el) => el.type === 're-ranking')
    },
    allowMetadataFilter: {
      get() {
        return this.activeVariant?.retrieve?.allow_metadata_filter || false
      },
      set(value) {
        this.updateVariantField('retrieve.allow_metadata_filter', value)
      },
    },
    useKeywordSearch: {
      get() {
        return this.activeVariant?.retrieve?.use_keyword_search || false
      },
      set(value) {
        this.updateVariantField('retrieve.use_keyword_search', value)
      },
    },
    isReRanking: {
      get() {
        return this.activeVariant?.retrieve?.rerank?.enabled || false
      },
      set(value) {
        this.updateVariantField('retrieve.rerank.enabled', value)
      },
    },
    reRankingModel: {
      get() {
        return this.activeVariant?.retrieve?.rerank?.model || ''
      },
      set(value) {
        this.updateVariantField('retrieve.rerank.model', value)
      },
    },
    reRankingMaxChankRetrieve: {
      get() {
        return this.activeVariant?.retrieve?.rerank?.max_chunks_retrieved || ''
      },
      set(value) {
        this.updateVariantField('retrieve.rerank.max_chunks_retrieved', value)
      },
    },
    similarityScoreThreshold: {
      get() {
        return this.activeVariant?.retrieve?.similarity_score_threshold
      },
      set(value) {
        this.updateVariantField('retrieve.similarity_score_threshold', value)
      },
    },
    chunkContextWindowExpansionSize: {
      get() {
        return this.activeVariant?.retrieve?.chunk_context_window_expansion_size || 0
      },
      set(value) {
        this.updateVariantField('retrieve.chunk_context_window_expansion_size', value)
      },
    },
    maxChunksRetrieved: {
      get() {
        return this.activeVariant?.retrieve?.max_chunks_retrieved || ''
      },
      set(value) {
        this.updateVariantField('retrieve.max_chunks_retrieved', value)
      },
    },
    collectionSystemNames: {
      get() {
        return this.collections.filter((el) => (this.activeVariant?.retrieve?.collection_system_names || []).includes(el?.system_name))
      },
      set(value) {
        value = (value || []).map((el) => {
          if (typeof el === 'string') {
            return el
          } else {
            return el?.system_name
          }
        })
        this.updateVariantField('retrieve.collection_system_names', value)
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
