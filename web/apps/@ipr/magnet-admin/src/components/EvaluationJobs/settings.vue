<template lang="pug">
div(style='min-width: 300px')
  km-section(:title='m.section_variantBasicInfo()')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.common_promptTemplate() }}
      km-input(height='30px', :placeholder='m.common_promptTemplate()', readonly, :model-value='name')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.evaluation_variantName() }}
      .row.items-center
        .col
          km-input(height='30px', :placeholder='m.evaluation_variantName()', readonly, :model-value='variantLabel')
        .col-auto.q-ml-sm
          km-btn(
            flat,
            simple,
            :label='m.common_openVariant()',
            iconSize='16px',
            icon='fas fa-book',
            @click='navigate("/prompt-templates/" + this.evaluation?.tool?.id)'
          )

    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.common_description() }}
      km-input(height='30px', :placeholder='m.common_description()', readonly, :model-value='evaluationVariant?.description')
  km-section(:title='m.section_variantParameters()')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.evaluation_promptTemplateBody() }}
      km-input(
        ref='input',
        rows='10',
        :placeholder='m.prompts_typeYourText()',
        border-radius='8px',
        height='36px',
        type='textarea',
        :model-value='evaluationVariant?.text',
        readonly
      )
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md {{ m.common_model() }}
      km-input(height='30px', :placeholder='m.common_model()', readonly, :model-value='modelName')
    .row.q-mb-md
      .col.km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.evaluation_temperature() }}
        km-input(type='number', height='30px', :placeholder='m.evaluation_temperature()', readonly, :model-value='evaluationVariant?.temperature')
      .col.km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.evaluation_topP() }}
        km-input(type='number', height='30px', :placeholder='m.evaluation_topP()', readonly, :model-value='evaluationVariant?.topP')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.evaluation_respondWithJson() }}
      q-toggle(height='30px', :label='m.evaluation_respondWithJson()', :model-value='true', readonly)
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
