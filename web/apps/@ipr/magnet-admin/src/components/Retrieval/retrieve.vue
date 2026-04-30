<template>
  <!-- Knowledge sources section -->
  <km-section :title="m.label_knowledgeSources()" :sub-title="m.subtitle_selectKnowledgeSourcesRetrieval()">
    <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.label_knowledgeSources() }}</div>
    <km-select v-model="collectionSystemNames" height="auto" min-height="36px" :placeholder="m.common_selectKnowledgeSources()" multiple :options="collections" use-chips has-dropdown-search />
    <div class="mt-sm">
      <km-btn flat simple :label="m.common_openKnowledgeSources()" icon-size="16px" icon="book" @click="navigate(&quot;knowledge-sources&quot;)" />
    </div>
  </km-section>
  <km-separator class="my-lg" /><!-- Search capabilities section -->
  <km-section :title="m.retrieval_searchCapabilities()" :sub-title="m.subtitle_configureSearch()">
    <div class="stack" data-gap="lg">
      <div class="stack">
        <div class="cluster" data-align="baseline">
          <div class="flex-none mr-sm">
            <km-toggle v-model="allowMetadataFilter" dense />
          </div>
          <div class="flex-1 mb-sm">{{ m.retrieval_allowMetadataFiltering() }}</div>
        </div>
        <div class="km-description text-secondary-text mt-xs ml-sm">{{ m.retrieval_allowMetadataFilteringDesc() }}</div>
      </div>
      <div class="stack">
        <div class="cluster" data-align="baseline">
          <div class="flex-none mr-sm">
            <km-toggle :model-value="true" disable dense />
          </div>
          <div class="flex-1 mb-sm">{{ m.retrieval_useSemanticSearch() }}</div>
        </div>
        <div class="km-description text-secondary-text mt-xs ml-sm">{{ m.retrieval_useSemanticSearchDesc() }}</div>
      </div>
      <div class="stack">
        <div class="cluster" data-align="baseline">
          <div class="flex-none mr-sm">
            <km-toggle v-model="useKeywordSearch" dense />
          </div>
          <div class="flex-1 mb-sm">{{ m.retrieval_useKeywordSearch() }}</div>
        </div>
        <div class="km-description text-secondary-text mt-xs ml-sm">{{ m.retrieval_useKeywordSearchDesc() }}</div>
      </div>
    </div>
  </km-section>
  <km-separator class="my-lg" /><!-- Re-ranking section -->
  <km-section :title="m.retrieval_reRanking()" :sub-title="m.subtitle_reranking()">
    <div class="stack">
      <div>
        <div class="cluster" data-align="baseline">
          <div class="flex-none mr-sm">
            <km-toggle v-model="isReRanking" dense />
          </div>
          <div class="flex-1 mb-sm">{{ m.retrieval_reRankWithLlm() }}</div>
        </div>
      </div>
      <div class="full-width" />
      <template v-if="isReRanking">
        <div class="full-width mt-md">
          <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_llmModel() }}</div>
          <km-select v-model="reRankingModel" height="auto" min-height="36px" :placeholder="m.common_reRankModel()" :options="modelOptions" option-label="display_name" emit-value map-options option-value="system_name">
            <template #option="{ itemProps, opt, toggleOption }">
              <li class="km-item ba-border" v-bind="itemProps" dense @click="toggleOption(opt)">
                <div class="km-item-section">
                  <span class="km-item-label km-label">{{ opt.display_name }}</span>
                  <div v-if="opt.provider_system_name" class="mt-xs">
                    <km-chip tone="brand" size="sm" dense>{{ opt.provider_system_name }}</km-chip>
                  </div>
                </div>
              </li>
            </template>
          </km-select>
          <div class="km-field text-secondary-text">{{ m.retrieval_useLlmToRank() }}</div>
        </div>
        <km-separator class="my-md" />
        <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.retrieval_maxChunksForReranking() }}</div>
        <div style="max-inline-size: 200px">
          <km-input v-model="reRankingMaxChankRetrieve" type="number" height="30px" :placeholder="m.common_numberOfChunksToSelect()" />
        </div>
        <div class="km-description text-secondary-text pb-xs">{{ m.retrieval_rerankingChunksDesc() }}</div>
      </template>
    </div>
  </km-section>
  <km-separator class="my-lg" /><!-- Similarity score section -->
  <km-section :title="m.section_similarityScore()" :sub-title="m.subtitle_similarityScore()">
    <km-slider-card v-model="similarityScoreThreshold" :name="m.retrieval_similarityScoreThreshold()" :min="0" :max="1" :min-label="m.retrieval_unrelated()" :max-label="m.retrieval_similar()" :default-value="0.75" :description="m.retrieval_similarityScoreDesc()" />
  </km-section>
  <km-separator class="my-lg" />
  <km-section :title="m.section_chunkLimits()" :sub-title="m.subtitle_configureRetrieval()">
    <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_numberOfChunksToSelect() }}</div>
    <div style="max-inline-size: 200px">
      <km-input v-model="maxChunksRetrieved" type="number" height="30px" :placeholder="m.common_numberOfChunks()" />
    </div>
    <div class="km-description text-secondary-text pb-xs">{{ m.common_maxBestRetrievedChunks() }}</div>
  </km-section>
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
