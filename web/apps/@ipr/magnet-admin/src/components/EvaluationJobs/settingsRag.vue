<template lang="pug">
div(style='min-width: 300px')
  km-section(title='Variant basic info')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md RAG name
      km-input(height='30px', placeholder='RAG name', readonly, :model-value='name')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Variant name
      .row
        .col
          km-input(height='30px', placeholder='Variant name', readonly, :model-value='variantLabel')
        .col-auto.q-ml-sm
          km-btn(
            flat,
            simple,
            label='Open variant',
            iconSize='16px',
            icon='fas fa-book',
            @click='navigate("/rag-tools/" + this.evaluation?.tool?.id)'
          )

    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Description
      km-input(height='30px', placeholder='description', readonly, :model-value='evaluationVariant?.description')
  km-section(title='Retrieval parameters')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Knowledge source
      km-select(
        height='auto',
        minHeight='36px',
        placeholder='Select knowledge sources',
        multiple,
        :options='collections',
        v-model='collectionSystemNames',
        use-chips,
        ref='sourecesRef',
        readonly
      )
    .row.q-mb-md
      .col.km-field.text-secondary-text.q-pb-xs.q-pl-8 Similarity score
        km-input(
          type='number',
          height='30px',
          placeholder='Similarity score',
          readonly,
          :model-value='evaluationVariant?.retrieve?.similarity_score_threshold'
        )
      .col.km-field.text-secondary-text.q-pb-xs.q-pl-8 No of chunks to select
        km-input(
          type='number',
          height='30px',
          placeholder='No of chunks to select',
          readonly,
          :model-value='evaluationVariant?.retrieve?.max_chunks_retrieved'
        )
    .row.q-mb-md
      .col.km-field.text-secondary-text.q-pb-xs.q-pl-8 Context window expansion size
        km-input(
          type='number',
          height='30px',
          placeholder='Context window expansion size',
          readonly,
          :model-value='evaluationVariant?.retrieve?.chunk_context_window_expansion_size'
        )
      .col

  km-section(title='Generation parameters')
    .row.q-mb-md
      .col.km-field.text-secondary-text.q-pb-xs.q-pl-8 System prompt template
        |
        km-select(
          height='auto',
          minHeight='36px',
          placeholder='Select Prompt Template',
          :options='promptTemplates',
          v-model='generateTemplate',
          hasDropdownSearch,
          option-value='system_name',
          option-label='name',
          emit-value,
          map-options,
          readonly,
          disabled
        )
  km-section(title='Language parameters')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Enable multi-lingual RAG
      q-toggle(height='30px', placeholder='Enable multi-lingual RAG', :model-value='evaluationVariant?.multilanguage?.enabled == true', readonly)
</template>

<script>
import { useChroma } from '@shared'

export default {
  setup() {
    const { publicItems } = useChroma('collections')
    const { items: promptTemplates } = useChroma('promptTemplates')
    return {
      publicItems,
      promptTemplates,
    }
  },
  computed: {
    evaluation: {
      get() {
        return this.$store.getters.evaluation
      },
    },
    evaluationVariant: {
      get() {
        return this.evaluation?.tool?.variant_object
      },
    },
    knowledgeSource() {
      return this.evaluationVariant?.retrieve?.collection_system_names
    },
    generateTemplate() {
      return this.evaluationVariant?.generate?.prompt_template
    },
    name() {
      return this.evaluation?.tool?.name
    },
    variantLabel() {
      const match = this.evaluationVariant?.variant?.match(/variant_(\d+)/)
      return `Variant ${match?.[1]}`
    },
    collectionSystemNames: {
      get() {
        return this.publicItems.filter((el) => (this.knowledgeSource || []).includes(el?.system_name))
      },
    },
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push({
          path: path,
          query: {
            variant: this.evaluationVariant?.variant,
          },
        })
      }
    },
  },
}
</script>
