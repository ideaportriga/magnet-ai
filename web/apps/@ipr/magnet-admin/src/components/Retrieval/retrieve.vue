<template lang="pug">
<!-- Knowledge sources section -->
km-section(:title='m.label_knowledgeSources()', :subTitle='m.subtitle_selectKnowledgeSourcesRetrieval()')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.label_knowledgeSources() }}
  km-select(
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
  :title='m.retrieval_searchCapabilities()',
  :subTitle='m.subtitle_configureSearch()'
)
  .column.q-gap-16
    .column
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='allowMetadataFilter', dense)
        .col.q-mb-sm {{ m.retrieval_allowMetadataFiltering() }}
      .km-description.text-secondary-text.q-mt-xs.q-ml-sm {{ m.retrieval_allowMetadataFilteringDesc() }}
    .column
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(:model-value='true', disable, dense)
        .col.q-mb-sm {{ m.retrieval_useSemanticSearch() }}
      .km-description.text-secondary-text.q-mt-xs.q-ml-sm {{ m.retrieval_useSemanticSearchDesc() }}
    .column
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='useKeywordSearch', dense)
        .col.q-mb-sm {{ m.retrieval_useKeywordSearch() }}
      .km-description.text-secondary-text.q-mt-xs.q-ml-sm {{ m.retrieval_useKeywordSearchDesc() }}
q-separator.q-my-lg

<!-- Re-ranking section -->
km-section(
  :title='m.retrieval_reRanking()',
  :subTitle='m.subtitle_reranking()'
)
  .column
    .col
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='isReRanking', dense)
        .col.q-mb-sm {{ m.retrieval_reRankWithLlm() }}
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
        .km-field.text-secondary-text {{ m.retrieval_useLlmToRank() }}
      q-separator.q-my-md
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.retrieval_maxChunksForReranking() }}
      div(style='max-width: 200px')
        km-input(type='number', height='30px', :placeholder='m.common_numberOfChunksToSelect()', v-model='reRankingMaxChankRetrieve')
      .km-description.text-secondary-text.q-pb-4 {{ m.retrieval_rerankingChunksDesc() }}
q-separator.q-my-lg

<!-- Similarity score section -->
km-section(:title='m.section_similarityScore()', :subTitle='m.subtitle_similarityScore()')
  km-slider-card(
    v-model='similarityScoreThreshold',
    :name='m.retrieval_similarityScoreThreshold()',
    :min='0',
    :max='1',
    :minLabel='m.retrieval_unrelated()',
    :maxLabel='m.retrieval_similar()',
    :defaultValue='0.75',
    :description='m.retrieval_similarityScoreDesc()'
  )
q-separator.q-my-lg
km-section(:title='m.section_chunkLimits()', :subTitle='m.subtitle_configureRetrieval()')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_numberOfChunksToSelect() }}
  div(style='max-width: 200px')
    km-input(type='number', height='30px', :placeholder='m.common_numberOfChunks()', v-model='maxChunksRetrieved')
  .km-description.text-secondary-text.q-pb-4 {{ m.common_maxBestRetrievedChunks() }}
</template>

<script>
import { m } from '@/paraglide/messages'
import { isEqual, orderBy, pickBy } from 'lodash'
import { ref, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import chromaConfig from '@/config/entityFieldConfig'

export default {
  props: ['prompt', 'selectedRow'],
  emits: ['setProp', 'save', 'cancel', 'remove', 'openTest'],

  setup() {
    const queries = useEntityQueries()
    const { activeVariant, updateVariantField } = useVariantEntityDetail('retrieval')
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
      reRankingLlmModel: ref(''),
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
        return this.activeVariant?.retrieve?.chunk_context_window_expansion_size || ''
      },
      set(value) {
        this.updateVariantField('retrieve.chunk_context_window_expansion_size', value)
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
        return (this.collections || []).filter((el) =>
          (this.activeVariant?.retrieve?.collection_system_names || []).includes(el?.system_name)
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
        this.updateVariantField('retrieve.collection_system_names', value)
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
      const res = {}
      Object.keys(chromaConfig).forEach((name) => {
        let controls = chromaConfig[name]?.config ?? {}
        controls = pickBy(controls, (o) => o.fieldName || o.dataType)
        controls = orderBy(Object.values(controls), ['label'])
        res[name] = { applet: chromaConfig[name], controls }
      })
      return res
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
