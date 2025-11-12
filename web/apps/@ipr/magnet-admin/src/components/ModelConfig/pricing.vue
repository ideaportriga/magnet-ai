<template lang="pug">
div
  km-section(title='Pricing', subTitle='Pricing information about the model')
    .row.q-gap-16.q-mb-md
      .column
        .km-field.text-secondary-text.q-pl-8.q-mb-sm(style='min-width: 140px') Input units
          km-select(
            height='auto',
            minHeight='30px',
            v-model='price_input_unit_name',
            :options='priceUnitOptions',
            map-options,
            emit-value,
            option-value='value',
            option-label='label'
          )
      .column
        .full-width.row.q-gap-16.items-center
          .km-field.text-secondary-text.q-pl-8.q-mb-sm Price for {{ type === 'prompts' ? 'standard' : '' }} input {{ price_input_unit_name }}
            km-input(prefix='$', height='32px', v-model='price_standard_input', style='max-width: 200px')
          .text-secondary-text.q-mt-xs per
          km-input.q-mt-sm(height='32px', v-model='price_standard_input_unit_count', style='max-width: 150px')
          .text-secondary-text.q-mt-xs {{ price_input_unit_name }}
        .full-width.row.q-gap-16.items-center(v-if='type === "prompts"')
          .km-field.text-secondary-text.q-pl-8.q-mb-sm Price for cached input {{ price_input_unit_name }}
            km-input(prefix='$', height='32px', v-model='price_cached_input', style='max-width: 200px')
          .text-secondary-text.q-mt-xs per
          km-input.q-mt-sm(height='32px', v-model='price_cached_input_unit_count', style='max-width: 150px')
          .text-secondary-text.q-mt-xs {{ price_input_unit_name }}

    .row.q-gap-16.q-mb-md(v-if='type === "prompts"')
      .column
        .km-field.text-secondary-text.q-pl-8.q-mb-sm(style='min-width: 140px') Output units
          km-select(
            height='auto',
            minHeight='30px',
            v-model='price_output_unit_name',
            :options='priceUnitOptions',
            map-options,
            emit-value,
            option-value='value',
            option-label='label'
          )
      .column
        .full-width.row.q-gap-16.items-center
          .km-field.text-secondary-text.q-pl-8.q-mb-sm Price for {{ type === 'prompts' ? 'standard' : '' }} output {{ price_output_unit_name }}
            km-input(prefix='$', height='30px', v-model='price_standard_output', style='max-width: 200px')
          .text-secondary-text per
          km-input(height='32px', v-model='price_standard_output_unit_count', style='max-width: 150px')
          .text-secondary-text {{ price_output_unit_name }}
        .full-width.row.q-gap-16.items-center
          .km-field.text-secondary-text.q-pl-8.q-mb-sm Price for reasoning output {{ price_output_unit_name }}
            km-input(prefix='$', height='32px', v-model='price_reasoning_output', style='max-width: 200px')
          .text-secondary-text per
          km-input(height='32px', v-model='price_reasoning_output_unit_count', style='max-width: 150px')
          .text-secondary-text {{ price_output_unit_name }}
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
        return this.$store.getters['modelConfig/entity']?.model || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'model', value })
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
