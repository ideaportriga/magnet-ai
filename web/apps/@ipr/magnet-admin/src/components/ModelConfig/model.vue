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
import { ref } from 'vue'
import { useChroma } from '@shared'
export default {
  props: [],
  emits: [],

  setup() {
    const { items: providerItems } = useChroma('provider')

    return {
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
        return this.$store.getters['modelConfig/entity']?.provider || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'provider', value })
      },
    },
    model: {
      get() {
        return this.$store.getters['modelConfig/entity']?.ai_model || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'ai_model', value })
      },
    },
    json_mode: {
      get() {
        return this.$store.getters['modelConfig/entity']?.json_mode || false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'json_mode', value })
      },
    },
    json_schema: {
      get() {
        return this.$store.getters['modelConfig/entity']?.json_schema || false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'json_schema', value })
      },
    },
    tool_calling: {
      get() {
        return this.$store.getters['modelConfig/entity']?.tool_calling || false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'tool_calling', value })
      },
    },
    reasoning: {
      get() {
        return this.$store.getters['modelConfig/entity']?.reasoning || false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'reasoning', value })
      },
    },
    price_input_unit_name: {
      get() {
        return this.$store.getters['modelConfig/entity']?.price_input_unit_name || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_input_unit_name', value })
      },
    },
    price_standard_input: {
      get() {
        return this.$store.getters['modelConfig/entity']?.price_input || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_input', value: parseFloat(value) })
      },
    },
    price_standard_input_unit_count: {
      get() {
        return this.$store.getters['modelConfig/entity']?.price_standard_input_unit_count || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_standard_input_unit_count', value: parseFloat(value) })
      },
    },
    price_cached_input: {
      get() {
        return this.$store.getters['modelConfig/entity']?.price_cached || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_cached', value: parseFloat(value) })
      },
    },
    price_cached_input_unit_count: {
      get() {
        return this.$store.getters['modelConfig/entity']?.price_cached_input_unit_count || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_cached_input_unit_count', value: parseFloat(value) })
      },
    },
    price_output_unit_name: {
      get() {
        return this.$store.getters['modelConfig/entity']?.price_output_unit_name || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_output_unit_name', value })
      },
    },
    price_standard_output: {
      get() {
        return this.$store.getters['modelConfig/entity']?.price_output || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_output', value: parseFloat(value) })
      },
    },
    price_standard_output_unit_count: {
      get() {
        return this.$store.getters['modelConfig/entity']?.price_standard_output_unit_count || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_standard_output_unit_count', value: parseFloat(value) })
      },
    },
    price_reasoning_output: {
      get() {
        return this.$store.getters['modelConfig/entity']?.price_reasoning || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_reasoning', value: parseFloat(value) })
      },
    },
    price_reasoning_output_unit_count: {
      get() {
        return this.$store.getters['modelConfig/entity']?.price_reasoning_output_unit_count || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_reasoning_output_unit_count', value: parseFloat(value) })
      },
    },
    resources: {
      get() {
        return this.$store.getters['modelConfig/entity']?.resources || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'resources', value })
      },
    },
    type: {
      get() {
        return this.$store.getters['modelConfig/entity']?.type || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'type', value })
      },
    },
  },
  created() {},
  methods: {},
}
</script>
