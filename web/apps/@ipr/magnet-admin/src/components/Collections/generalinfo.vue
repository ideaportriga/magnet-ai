<template lang="pug">
.q-pr-md
  km-section(title='Source settings', subTitle='Content source route and parameters')
    .col.q-pt-8
      .km-input-label.q-pb-xs.q-pl-8 Source type
      km-select(
        :options='config.source_type.options',
        v-model='source_type',
        ref='source_typeRef',
        :rules='config.source_type.rules',
        :disabled='isDisable'
      )
    template(v-for='item in config.source_type?.children[source_type]')
      .col.q-pt-8
        .km-input-label.q-pb-xs.q-pl-8 {{ item.label }}
          .km-description.text-secondary-text(v-if='item?.description') {{ item?.description }}
        component(:is='item.component', v-model='source_fields[item.field]', :readonly='isDisable', :disable='isDisable')
  <!-- CHUNKING -->
  q-separator.q-my-lg
  km-section(title='Chunking', subTitle='Configure how documents are split into smaller, manageable pieces for processing')
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
  km-section(title='Indexing', subTitle='Configure indexing methods to optimize document retrieval and search accuracy')
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
      .col.q-mt-sm
        .row.items-baseline
          .col-auto.q-mr-sm
            q-toggle(v-model='supportKeywordSearch', dense)
          .col Support keyword search
        .km-description.text-secondary-text.q-mt-sm Toggling this option enables direct keyword matching, which can be beneficial for some use cases. Note that keyword search capabilities depend on the underlying database implementation.
</template>

<script>
import { isEqual, orderBy, pickBy } from 'lodash'
import { ref } from 'vue'
import { useChroma } from '@shared'

export default {
  props: ['prompt'],
  emits: ['setProp', 'save', 'cancel', 'remove', 'openTest'],

  setup() {
    const { config, selectedRow } = useChroma('collections')
    const { items: promptTemplateItems } = useChroma('promptTemplates')

    return {
      showError: ref(false),
      selectedEntity: ref(),
      config,
      selectedRow,
      customFields: ref({}),
      promptTemplateItems,
    }
  },
  computed: {
    isDisable() {
      if (!this.selectedRow?.last_synced) return false
      const d = new Date(this.selectedRow.last_synced)
      return !isNaN(d.getTime())
    },
    source_fields: {
      get() {
        const source = this.$store.getters.knowledge?.source || {}
        
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
        this.$store.dispatch('updateKnowledge', { source: value })
      },
    },
    source_type: {
      get() {
        return this.$store.getters.knowledge?.source?.source_type || ''
      },
      set(value) {
        this.$store.dispatch('updateKnowledge', { source: { source_type: value } })
      },
    },

    // Chunking settings
    chunkingStrategy: {
      get() {
        return this.$store.getters.knowledge?.chunking?.strategy || 'recursive_character_text_splitting'
      },
      set(value) {
        console.log('value', value)
        this.$store.dispatch('updateKnowledge', { chunking: { strategy: value } })
      },
    },
    chunkSize: {
      get() {
        return this.$store.getters.knowledge?.chunking?.chunk_size || ''
      },
      set(value) {
        this.$store.dispatch('updateKnowledge', { chunking: { chunk_size: parseInt(value) } })
      },
    },
    chunkOverlap: {
      get() {
        return this.$store.getters.knowledge?.chunking?.chunk_overlap || ''
      },
      set(value) {
        this.$store.dispatch('updateKnowledge', { chunking: { chunk_overlap: parseInt(value) } })
      },
    },
    chunkTransformationEnabled: {
      get() {
        return this.$store.getters.knowledge?.chunking?.transformation_enabled || false
      },
      set(value) {
        this.$store.dispatch('updateKnowledge', { chunking: { transformation_enabled: value } })
      },
    },
    chunkTransformationPromptTemplate: {
      get() {
        return this.$store.getters.knowledge?.chunking?.transformation_prompt_template || ''
      },
      set(value) {
        this.$store.dispatch('updateKnowledge', { chunking: { transformation_prompt_template: value } })
      },
    },
    chunkTransformationPromptTemplateId() {
      return this.chunkTransformationPromptTemplateOptions.find((el) => el.system_name == this.chunkTransformationPromptTemplate)?.id
    },
    chunkTransformationPromptTemplateOptions() {
      return (this.promptTemplateItems ?? []).map((item) => ({
        label: item.name,
        value: item.id,
        system_name: item.system_name,
        category: item?.category,
        id: item.id,
      }))
    },
    chunkTransformationMethod: {
      get() {
        return this.$store.getters.knowledge?.chunking?.transformation_method || ''
      },
      set(value) {
        this.$store.dispatch('updateKnowledge', { chunking: { transformation_method: value } })
      },
    },
    chunkUsageMethod: {
      get() {
        return this.$store.getters.knowledge?.chunking?.chunk_usage_method || ''
      },
      set(value) {
        this.$store.dispatch('updateKnowledge', { chunking: { chunk_usage_method: value } })
      },
    },

    // Indexing settings
    supportSemanticSearch: {
      get() {
        if (!this.$store.getters.knowledge?.indexing) return true
        return this.$store.getters.knowledge?.indexing?.semantic_search_supported || false
      },
      set(value) {
        this.$store.dispatch('updateKnowledge', { indexing: { semantic_search_supported: value } })
      },
    },
    embeddingModel: {
      get() {
        return this.$store.getters.knowledge?.ai_model || ''
      },
      set(value) {
        this.$store.dispatch('updateKnowledge', { ai_model: value })
      },
    },
    embeddingModelOptions() {
      return (this.$store.getters['chroma/model'].items || []).filter((el) => el.type === 'embeddings')
    },
    supportKeywordSearch: {
      get() {
        return this.$store.getters.knowledge?.indexing?.fulltext_search_supported || false
      },
      set(value) {
        this.$store.dispatch('updateKnowledge', { indexing: { fulltext_search_supported: value } })
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
  watch: {
    customFields(newVal) {
      this.$store.dispatch('updateKnowledge', newVal)
    },
  },
  created() {},
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
