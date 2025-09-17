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
      rows='14',
      border-radius='8px',
      height='36px',
      type='textarea',
      :model-value='JSON.stringify(showOriginalParameters ? apiTool.original_operation_definition : apiTool.parameters, null, 2)',
      readonly
    )
  q-separator.q-my-lg
  km-section(title='Mock', subTitle='Mock response for the API Tool')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Mock enabled
    km-toggle(v-model='mockResponseEnabled')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-lg Mock response
    km-input.full-width(rows='14', border-radius='8px', height='36px', type='textarea', v-model='mockContent')
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
    isProviderMock() {
      return this.apiTool.system_name === 'MOCK'
    },
    showOriginalParameters() {
      return this.selectedParameters.value === 'original'
    },
    mockResponseEnabled: {
      get() {
        return this.apiTool.mock_response_enabled || false
      },
      set(value) {
        this.$store.commit('setNestedApiServerProperty', { system_name: this.apiTool.system_name, path: 'mock_response_enabled', value })
      },
    },
    mockContent: {
      get() {
        return this.apiTool?.mock_response?.content || ''
      },
      set(value) {
        this.$store.commit('setNestedApiServerProperty', { system_name: this.apiTool.system_name, path: 'mock_response.content', value })
      },
    },
  },
}
</script>
