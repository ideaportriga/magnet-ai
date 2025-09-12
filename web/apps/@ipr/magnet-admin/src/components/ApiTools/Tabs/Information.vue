<template lang="pug">
.full-width
  km-section(title='API definition', subTitle='API specification for the API Tool')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Path
    .row.items-center.q-gap-16.no-wrap
      km-chip.text-secondary-text(:label='apiTool.method', color='light', round)
      km-input.full-width(:model-value='apiTool.path', readonly)

    .row.q-mt-lg.justify-between.items-end.q-mb-4
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 API Operation definition
      km-select-flat(:options='parametersOptions', v-model='selectedParameters')
    km-input.full-width(
      rows='18',
      border-radius='8px',
      height='36px',
      type='textarea',
      :model-value='JSON.stringify(showOriginalParameters ? apiTool.original_parameters : variantProps, null, 2)',
      readonly
    )
    
    template(v-if="isProviderMock")
      .row.q-mt-lg.justify-between.items-end.q-mb-4
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Mock response
      km-input.full-width(
        rows='18',
        border-radius='8px',
        height='36px',
        type='textarea',
        v-model='mockContent',
    )
</template>

<script>
import { ref } from 'vue'
export default {
  props: {
    apiTool: {
      type: Object,
      required: true,
    },
  },
  setup() {
    const selectedParameters = ref({ label: 'Current parameters', value: 'current' })
    const parametersOptions = ref([
      { label: 'Current parameters', value: 'current' },
      { label: 'Original parameters', value: 'original' },
    ])
    return { selectedParameters, parametersOptions }
  },
  computed: {
    variantProps() {
      return this.$store.getters.api_tool_variant?.value?.parameters
    },
    isProviderMock() {
      return this.$store.getters.api_tool.api_provider === "MOCK"
      
    },
    showOriginalParameters() {
      return this.selectedParameters.value === 'original'
    },
    mockContent: {
      get() {
        return this.$store.getters.api_tool?.mock?.content || ''
      },
      set(value) {
        this.$store.dispatch('updateApiToolProperty', { key: 'mock', value: { content: value } })
      },
    },
  },
}
</script>
