<template>
  <div class="full-width" />
  <km-section :title="m.section_apiDefinition()" :sub-title="m.subtitle_apiSpecification()">
    <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.apiTools_path() }}</div>
    <div class="cluster" data-gap="lg" data-wrap="no">
      <km-chip class="text-secondary-text" :label="apiTool.method" tone="neutral" round />
      <km-input class="full-width" :model-value="apiTool.path" readonly />
    </div>
    <div class="cluster mt-lg mb-xs" data-justify="between" data-align="end">
      <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.apiTools_operationDefinition() }}</div>
      <km-select-flat v-model="selectedParameters" :options="parametersOptions" />
    </div>
    <km-input class="full-width" rows="14" border-radius="8px" height="36px" type="textarea" :model-value="JSON.stringify(showOriginalParameters ? apiTool.original_operation_definition : apiTool.parameters, null, 2)" readonly />
  </km-section>
  <km-separator class="my-lg" />
  <km-section :title="m.section_mock()" :sub-title="m.subtitle_mockResponse()">
    <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.apiTools_mockEnabled() }}</div>
    <km-toggle v-model="mockResponseEnabled" />
    <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">{{ m.apiTools_mockResponse() }}</div>
    <km-input v-model="mockContent" class="full-width" rows="14" border-radius="8px" height="36px" type="textarea" />
  </km-section>
</template>

<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityDetail } from '@/composables/useEntityDetail'
export default {
  props: {
    apiTool: {
      type: Object,
      required: true,
    },
  },
  setup() {
    const { draft, updateField } = useEntityDetail('api_servers')
    const selectedParameters = ref({ label: m.apiTools_currentParameters(), value: 'current' })
    const parametersOptions = ref([
      { label: m.apiTools_currentParameters(), value: 'current' },
      { label: m.apiTools_originalParameters(), value: 'original' },
    ])
    return { m, selectedParameters, parametersOptions, draft, updateField }
  },
  computed: {
    toolIndex() {
      const tools = this.draft?.tools
      if (!tools) return -1
      return tools.findIndex((tool) => tool.system_name === this.apiTool.system_name)
    },
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
        if (this.toolIndex === -1) return
        this.updateField(`tools.${this.toolIndex}.mock_response_enabled`, value)
      },
    },
    mockContent: {
      get() {
        return this.apiTool?.mock_response?.content || ''
      },
      set(value) {
        if (this.toolIndex === -1) return
        this.updateField(`tools.${this.toolIndex}.mock_response.content`, value)
      },
    },
  },
}
</script>
