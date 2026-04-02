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
import { ref, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useEntityDetail } from '@/composables/useEntityDetail'
export default {
  props: [],
  emits: [],

  setup() {
    const queries = useEntityQueries()
    const { draft, updateField } = useEntityDetail('model')
    const { data: providerData } = queries.provider.useList()
    const providerItems = computed(() => providerData.value?.items ?? [])

    return {
      draft,
      updateField,
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
        return this.draft?.provider || ''
      },
      set(value) {
        this.updateField('provider', value)
      },
    },
    model: {
      get() {
        return this.draft?.model || ''
      },
      set(value) {
        this.updateField('model', value)
      },
    },
    json_mode: {
      get() {
        return this.draft?.json_mode || false
      },
      set(value) {
        this.updateField('json_mode', value)
      },
    },
    json_schema: {
      get() {
        return this.draft?.json_schema || false
      },
      set(value) {
        this.updateField('json_schema', value)
      },
    },
    tool_calling: {
      get() {
        return this.draft?.tool_calling || false
      },
      set(value) {
        this.updateField('tool_calling', value)
      },
    },
    price_input_unit_name: {
      get() {
        return this.draft?.price_input_unit_name || ''
      },
      set(value) {
        this.updateField('price_input_unit_name', value)
      },
    },
    price_standard_input: {
      get() {
        return this.draft?.price_input || ''
      },
      set(value) {
        this.updateField('price_input', parseFloat(value))
      },
    },
    price_standard_input_unit_count: {
      get() {
        return this.draft?.price_standard_input_unit_count || ''
      },
      set(value) {
        this.updateField('price_standard_input_unit_count', parseFloat(value))
      },
    },
    price_cached_input: {
      get() {
        return this.draft?.price_cached || ''
      },
      set(value) {
        this.updateField('price_cached', parseFloat(value))
      },
    },
    price_cached_input_unit_count: {
      get() {
        return this.draft?.price_cached_input_unit_count || ''
      },
      set(value) {
        this.updateField('price_cached_input_unit_count', parseFloat(value))
      },
    },
    price_output_unit_name: {
      get() {
        return this.draft?.price_output_unit_name || ''
      },
      set(value) {
        this.updateField('price_output_unit_name', value)
      },
    },
    price_standard_output: {
      get() {
        return this.draft?.price_output || ''
      },
      set(value) {
        this.updateField('price_output', parseFloat(value))
      },
    },
    price_standard_output_unit_count: {
      get() {
        return this.draft?.price_standard_output_unit_count || ''
      },
      set(value) {
        this.updateField('price_standard_output_unit_count', parseFloat(value))
      },
    },
    price_reasoning_output: {
      get() {
        return this.draft?.price_reasoning || ''
      },
      set(value) {
        this.updateField('price_reasoning', parseFloat(value))
      },
    },
    price_reasoning_output_unit_count: {
      get() {
        return this.draft?.price_reasoning_output_unit_count || ''
      },
      set(value) {
        this.updateField('price_reasoning_output_unit_count', parseFloat(value))
      },
    },
    resources: {
      get() {
        return this.draft?.resources || ''
      },
      set(value) {
        this.updateField('resources', value)
      },
    },
    type: {
      get() {
        return this.draft?.type || ''
      },
      set(value) {
        this.updateField('type', value)
      },
    },
  },
  created() {},
  methods: {},
}
</script>
