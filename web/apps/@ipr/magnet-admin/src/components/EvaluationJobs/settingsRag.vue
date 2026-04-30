<template>
  <div style="min-inline-size: 300px">
    <km-section :title="m.section_variantBasicInfo()">
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
        {{ m.evaluation_ragName() }}
        <km-input height="30px" :placeholder="m.evaluation_ragName()" readonly :model-value="name" />
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
        {{ m.evaluation_variantName() }}
        <div class="cluster">
          <div class="flex-1">
            <km-input height="30px" :placeholder="m.evaluation_variantName()" readonly :model-value="variantLabel" />
          </div>
          <div class="flex-none ml-sm">
            <km-btn flat simple :label="m.common_openVariant()" icon-size="16px" icon="book" @click="navigate(&quot;/rag-tools/&quot; + evaluation?.tool?.id)" />
          </div>
        </div>
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
        {{ m.common_description() }}
        <km-input height="30px" :placeholder="m.common_description()" readonly :model-value="evaluationVariant?.description" />
      </div>
    </km-section>
    <km-section :title="m.evaluation_retrievalParameters()">
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
        {{ m.evaluation_knowledgeSource() }}
        <km-select ref="sourecesRef" v-model="collectionSystemNames" height="auto" min-height="36px" :placeholder="m.common_selectKnowledgeSources()" multiple :options="collections" use-chips readonly />
      </div>
      <div class="evaluation-settings-rag__field-grid mb-md">
        <div class="km-field text-secondary-text pb-xs pl-sm">
          {{ m.evaluation_similarityScore() }}
          <km-input type="number" height="30px" :placeholder="m.evaluation_similarityScore()" readonly :model-value="evaluationVariant?.retrieve?.similarity_score_threshold" />
        </div>
        <div class="km-field text-secondary-text pb-xs pl-sm">
          {{ m.evaluation_chunksToSelect() }}
          <km-input type="number" height="30px" :placeholder="m.evaluation_chunksToSelect()" readonly :model-value="evaluationVariant?.retrieve?.max_chunks_retrieved" />
        </div>
      </div>
      <div class="evaluation-settings-rag__field-grid mb-md">
        <div class="km-field text-secondary-text pb-xs pl-sm">
          {{ m.evaluation_contextWindowExpansionSize() }}
          <km-input type="number" height="30px" :placeholder="m.evaluation_contextWindowExpansionSize()" readonly :model-value="evaluationVariant?.retrieve?.chunk_context_window_expansion_size" />
        </div>
      </div>
    </km-section>
    <km-section :title="m.evaluation_generationParameters()">
      <div class="mb-md">
        <div class="km-field text-secondary-text pb-xs pl-sm">
          {{ m.evaluation_systemPromptTemplate() }}
          <km-select v-model="generateTemplate" height="auto" min-height="36px" :placeholder="m.evaluation_selectPromptTemplate()" :options="promptTemplates" has-dropdown-search option-value="system_name" option-label="name" emit-value map-options readonly disabled />
        </div>
      </div>
    </km-section>
    <km-section :title="m.evaluation_languageParameters()">
      <div class="km-field text-secondary-text pb-xs pl-sm">
        {{ m.ragTools_enableMultiLingualRag() }}
        <km-toggle height="30px" :label="m.ragTools_enableMultiLingualRag()" :model-value="evaluationVariant?.multilanguage?.enabled == true" readonly />
      </div>
    </km-section>
  </div>
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

<style scoped>
.evaluation-settings-rag__field-grid {
  display: grid;
  gap: var(--ds-space-md);
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 767px) {
  .evaluation-settings-rag__field-grid {
    grid-template-columns: 1fr;
  }
}
</style>
