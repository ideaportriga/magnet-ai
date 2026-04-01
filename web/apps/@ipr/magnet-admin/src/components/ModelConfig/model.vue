<template lang="pug">
div
  km-section(title='Model configuration', subTitle='Foundational model settings')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Provider
      km-select(
        height='auto',
        minHeight='30px',
        placeholder='Provider',
        :options='providerItems',
        v-model='provider',
        ref='providerRef',
        emit-value,
        map-options,
        option-value='id'
      )
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Name
      .full-width
        km-input(height='30px', placeholder='E.g. gpt-4o-mini', v-model='model', ref='modelRef')

  q-separator.q-my-lg(v-if='type === "prompts"')
  km-section(v-if='type === "prompts"', title='Structured data support', subTitle='Model specific features')
    .col-6.km-field.text-secondary-text.q-pb-xs.q-pl-8
      .row.items-center
        q-toggle(height='30px', placeholder='E.g. GPT 4o mini', v-model='json_mode', ref='json_modeRef')
        .km-field.text-secondary-text JSON mode
    .col-6.km-field.text-secondary-text.q-pb-xs.q-pl-8
      .row.items-center
        q-toggle(height='30px', placeholder='E.g. GPT 4o mini', v-model='json_schema', ref='json_schemaRef')
        .km-field.text-secondary-text JSON schema
    .col-6.km-field.text-secondary-text.q-pb-xs.q-pl-8
      .row.items-center
        q-toggle(height='30px', placeholder='E.g. GPT 4o mini', v-model='tool_calling', ref='json_schemaRef')
        .km-field.text-secondary-text Tool calling
    .col-6.km-field.text-secondary-text.q-pb-xs.q-pl-8
      .row.items-center
        q-toggle(height='30px', placeholder='E.g. GPT 4o mini', v-model='reasoning', ref='json_schemaRef')
        .km-field.text-secondary-text Reasoning
  q-separator.q-my-lg
  km-section(title='Additional information', subTitle='Useful information about the model')
    .row
      .col.km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mb-md Resources
        .full-width
          km-input(
            ref='resourcesRef',
            rows='10',
            placeholder='Type your text here',
            :model-value='resources',
            @input='resources = $event',
            border-radius='8px',
            height='36px',
            type='textarea'
          )
</template>

<script>
import { ref, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useModelConfigDetailStore } from '@/stores/entityDetailStores'
export default {
  props: [],
  emits: [],

  setup() {
    const queries = useEntityQueries()
    const modelConfigStore = useModelConfigDetailStore()
    const { data: providerData } = queries.provider.useList()
    const providerItems = computed(() => providerData.value?.items ?? [])

    return {
      modelConfigStore,
      providerItems,
      priceUnitOptions: ref([
        { label: 'Tokens', value: 'tokens' },
        { label: 'Characters', value: 'characters' },
        { label: 'Queries', value: 'queries' },
      ]),
    }
  },
  computed: {
    provider: {
      get() {
        return this.modelConfigStore.entity?.provider || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'provider', value })
      },
    },
    model: {
      get() {
        return this.modelConfigStore.entity?.ai_model || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'ai_model', value })
      },
    },
    json_mode: {
      get() {
        return this.modelConfigStore.entity?.json_mode || false
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'json_mode', value })
      },
    },
    json_schema: {
      get() {
        return this.modelConfigStore.entity?.json_schema || false
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'json_schema', value })
      },
    },
    tool_calling: {
      get() {
        return this.modelConfigStore.entity?.tool_calling || false
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'tool_calling', value })
      },
    },
    reasoning: {
      get() {
        return this.modelConfigStore.entity?.reasoning || false
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'reasoning', value })
      },
    },
    price_input_unit_name: {
      get() {
        return this.modelConfigStore.entity?.price_input_unit_name || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'price_input_unit_name', value })
      },
    },
    price_standard_input: {
      get() {
        return this.modelConfigStore.entity?.price_input || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'price_input', value: parseFloat(value) })
      },
    },
    price_standard_input_unit_count: {
      get() {
        return this.modelConfigStore.entity?.price_standard_input_unit_count || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'price_standard_input_unit_count', value: parseFloat(value) })
      },
    },
    price_cached_input: {
      get() {
        return this.modelConfigStore.entity?.price_cached || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'price_cached', value: parseFloat(value) })
      },
    },
    price_cached_input_unit_count: {
      get() {
        return this.modelConfigStore.entity?.price_cached_input_unit_count || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'price_cached_input_unit_count', value: parseFloat(value) })
      },
    },
    price_output_unit_name: {
      get() {
        return this.modelConfigStore.entity?.price_output_unit_name || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'price_output_unit_name', value })
      },
    },
    price_standard_output: {
      get() {
        return this.modelConfigStore.entity?.price_output || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'price_output', value: parseFloat(value) })
      },
    },
    price_standard_output_unit_count: {
      get() {
        return this.modelConfigStore.entity?.price_standard_output_unit_count || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'price_standard_output_unit_count', value: parseFloat(value) })
      },
    },
    price_reasoning_output: {
      get() {
        return this.modelConfigStore.entity?.price_reasoning || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'price_reasoning', value: parseFloat(value) })
      },
    },
    price_reasoning_output_unit_count: {
      get() {
        return this.modelConfigStore.entity?.price_reasoning_output_unit_count || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'price_reasoning_output_unit_count', value: parseFloat(value) })
      },
    },
    resources: {
      get() {
        return this.modelConfigStore.entity?.resources || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'resources', value })
      },
    },
    type: {
      get() {
        return this.modelConfigStore.entity?.type || ''
      },
      set(value) {
        this.modelConfigStore.updateProperty({ key: 'type', value })
      },
    },
  },
  created() {},
  methods: {},
}
</script>
