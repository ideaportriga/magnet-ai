<template lang="pug">
div(style='min-width: 300px')
  km-section(:title='m.section_variantBasicInfo()')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.evaluation_ragName() }}
      km-input(height='30px', :placeholder='m.evaluation_ragName()', readonly, :model-value='name')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.evaluation_variantName() }}
      .row
        .col
          km-input(height='30px', :placeholder='m.evaluation_variantName()', readonly, :model-value='variantLabel')
        .col-auto.q-ml-sm
          km-btn(
            flat,
            simple,
            :label='m.common_openVariant()',
            iconSize='16px',
            icon='fas fa-book',
            @click='navigate("/rag-tools/" + this.evaluation?.tool?.id)'
          )

    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.common_description() }}
      km-input(height='30px', :placeholder='m.common_description()', readonly, :model-value='evaluationVariant?.description')
  km-section(:title='m.evaluation_retrievalParameters()')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.evaluation_knowledgeSource() }}
      km-select(
        height='auto',
        minHeight='36px',
        :placeholder='m.common_selectKnowledgeSources()',
        multiple,
        :options='collections',
        v-model='collectionSystemNames',
        use-chips,
        ref='sourecesRef',
        readonly
      )
    .row.q-mb-md
      .col.km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.evaluation_similarityScore() }}
        km-input(
          type='number',
          height='30px',
          :placeholder='m.evaluation_similarityScore()',
          readonly,
          :model-value='evaluationVariant?.retrieve?.similarity_score_threshold'
        )
      .col.km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.evaluation_chunksToSelect() }}
        km-input(
          type='number',
          height='30px',
          :placeholder='m.evaluation_chunksToSelect()',
          readonly,
          :model-value='evaluationVariant?.retrieve?.max_chunks_retrieved'
        )
    .row.q-mb-md
      .col.km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.evaluation_contextWindowExpansionSize() }}
        km-input(
          type='number',
          height='30px',
          :placeholder='m.evaluation_contextWindowExpansionSize()',
          readonly,
          :model-value='evaluationVariant?.retrieve?.chunk_context_window_expansion_size'
        )
      .col

  km-section(:title='m.evaluation_generationParameters()')
    .row.q-mb-md
      .col.km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.evaluation_systemPromptTemplate() }}
        |
        km-select(
          height='auto',
          minHeight='36px',
          :placeholder='m.evaluation_selectPromptTemplate()',
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
  km-section(:title='m.evaluation_languageParameters()')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.ragTools_enableMultiLingualRag() }}
      q-toggle(height='30px', :label='m.ragTools_enableMultiLingualRag()', :model-value='evaluationVariant?.multilanguage?.enabled == true', readonly)
</template>

<script>
import { useEntityQueries } from '@/queries/entities'
import { m } from '@/paraglide/messages'
import { useEvaluationStore } from '@/stores/evaluationStore'

export default {
  setup() {
    const queries = useEntityQueries()
    const { data: collectionsListData } = queries.collections.useList()
    const { data: promptTemplatesListData } = queries.promptTemplates.useList()
    const evalStore = useEvaluationStore()
    return {
      m,
      collectionsListData,
      promptTemplatesListData,
      evalStore,
    }
  },
  computed: {
    publicItems() {
      return (this.collectionsListData?.items ?? []).map((item) => ({
        ...item,
        value: item.id,
        label: item.name,
      }))
    },
    promptTemplates() {
      return this.promptTemplatesListData?.items ?? []
    },
    evaluation: {
      get() {
        return this.evalStore.evaluation
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
      return `${m.common_variant()} ${match?.[1]}`
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
