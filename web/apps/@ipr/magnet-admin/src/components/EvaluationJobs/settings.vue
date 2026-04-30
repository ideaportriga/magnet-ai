<template>
  <div style="min-inline-size: 300px">
    <km-section :title="m.section_variantBasicInfo()">
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
        {{ m.common_promptTemplate() }}
        <km-input height="30px" :placeholder="m.common_promptTemplate()" readonly :model-value="name" />
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
        {{ m.evaluation_variantName() }}
        <div class="cluster">
          <div class="flex-1">
            <km-input height="30px" :placeholder="m.evaluation_variantName()" readonly :model-value="variantLabel" />
          </div>
          <div class="flex-none ml-sm">
            <km-btn flat simple :label="m.common_openVariant()" icon-size="16px" icon="book" @click="navigate(&quot;/prompt-templates/&quot; + evaluation?.tool?.id)" />
          </div>
        </div>
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
        {{ m.common_description() }}
        <km-input height="30px" :placeholder="m.common_description()" readonly :model-value="evaluationVariant?.description" />
      </div>
    </km-section>
    <km-section :title="m.section_variantParameters()">
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
        {{ m.evaluation_promptTemplateBody() }}
        <km-input ref="input" rows="10" :placeholder="m.prompts_typeYourText()" border-radius="8px" height="36px" type="textarea" :model-value="evaluationVariant?.text" readonly />
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
        {{ m.common_model() }}
        <km-input height="30px" :placeholder="m.common_model()" readonly :model-value="modelName" />
      </div>
      <div class="evaluation-settings__field-grid mb-md">
        <div class="km-field text-secondary-text pb-xs pl-sm">
          {{ m.evaluation_temperature() }}
          <km-input type="number" height="30px" :placeholder="m.evaluation_temperature()" readonly :model-value="evaluationVariant?.temperature" />
        </div>
        <div class="km-field text-secondary-text pb-xs pl-sm">
          {{ m.evaluation_topP() }}
          <km-input type="number" height="30px" :placeholder="m.evaluation_topP()" readonly :model-value="evaluationVariant?.topP" />
        </div>
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm">
        {{ m.evaluation_respondWithJson() }}
        <km-toggle height="30px" :label="m.evaluation_respondWithJson()" :model-value="true" readonly />
      </div>
    </km-section>
  </div>
</template>

<script>
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { useEvaluationStore } from '@/stores/evaluationStore'

export default {
  setup() {
    const queries = useEntityQueries()
    const { data: modelData } = queries.model.useList()
    const modelItems = computed(() => modelData.value?.items ?? [])
    const evalStore = useEvaluationStore()

    return {
      m,
      modelItems,
      evalStore,
    }
  },
  computed: {
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
    name() {
      return this.evaluation?.tool?.name
    },
    model() {
      return this.evaluationVariant?.system_name_for_model
    },
    modelName() {
      return this.modelItems?.find((model) => model.system_name === this.model)?.display_name
    },
    variantLabel() {
      const match = this.evaluationVariant?.variant?.match(/variant_(\d+)/)
      return `${m.common_variant()} ${match?.[1]}`
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
.evaluation-settings__field-grid {
  display: grid;
  gap: var(--ds-space-md);
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 767px) {
  .evaluation-settings__field-grid {
    grid-template-columns: 1fr;
  }
}
</style>
