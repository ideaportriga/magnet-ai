<template lang="pug">
div(style='min-width: 300px')
  km-section(title='Variant basic info')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Prompt template
      km-input(height='30px', placeholder='Prompt template', readonly, :model-value='name')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Variant name
      .row.items-center
        .col
          km-input(height='30px', placeholder='Variant name', readonly, :model-value='variantLabel')
        .col-auto.q-ml-sm
          km-btn(
            flat,
            simple,
            label='Open variant',
            iconSize='16px',
            icon='fas fa-book',
            @click='navigate("/prompt-templates/" + this.evaluation?.tool?.id)'
          )

    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Description
      km-input(height='30px', placeholder='description', readonly, :model-value='evaluationVariant?.description')
  km-section(title='Variant parameters')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Prompt template body
      km-input(
        ref='input',
        rows='10',
        placeholder='Type your text here',
        border-radius='8px',
        height='36px',
        type='textarea',
        :model-value='evaluationVariant?.text',
        readonly
      )
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Model
      km-input(height='30px', placeholder='Model', readonly, :model-value='modelName')
    .row.q-mb-md
      .col.km-field.text-secondary-text.q-pb-xs.q-pl-8 Temperature
        km-input(type='number', height='30px', placeholder='Temperature', readonly, :model-value='evaluationVariant?.temperature')
      .col.km-field.text-secondary-text.q-pb-xs.q-pl-8 Top P
        km-input(type='number', height='30px', placeholder='Top P', readonly, :model-value='evaluationVariant?.topP')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Respond with JSON
      q-toggle(height='30px', placeholder='Respond with JSON', :model-value='true', readonly)
</template>

<script>
export default {
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
    name() {
      return this.evaluation?.tool?.name
    },
    model() {
      return this.evaluationVariant?.system_name_for_model
    },
    modelName() {
      return this.$store.getters['chroma/model'].items?.find((model) => model.system_name === this.model)?.display_name
    },
    variantLabel() {
      const match = this.evaluationVariant?.variant?.match(/variant_(\d+)/)
      return `Variant ${match?.[1]}`
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
