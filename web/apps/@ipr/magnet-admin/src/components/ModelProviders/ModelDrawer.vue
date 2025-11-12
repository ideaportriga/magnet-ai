<template lang="pug">
.column.bg-white.fit.bl-border.height-100.fit(style='min-width: 500px; max-width: 500px')
  .col.q-pt-16
    .row.no-wrap.full-width.q-px-16
      q-tabs.bb-border.full-width(
        v-model='tab',
        narrow-indicator,
        dense,
        align='left',
        active-color='primary',
        indicator-color='primary',
        active-bg-color='white',
        no-caps,
        content-class='km-tabs'
      )
        template(v-for='t in tabs')
          q-tab(:name='t.name', :label='t.label')
        .fit
    .column.fit.q-gap-16.overflow-auto.q-pa-16(v-if='tab == "parameters"')
      .km-title General settings
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Name
        km-input(:model-value='model', @update:model-value='model = $event')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs Name used by provider to identify the model
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Display name
        km-input(:model-value='display_name', @update:model-value='display_name = $event')
        .km-description.text-secondary-text.q-pl-8.q-pt-xs Internal name used across Magnet AI
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 System name
        km-input(:model-value='system_name', readonly)
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Type
        km-select(height='32px', :options='categoryOptions', :model-value='type', @update:model-value='type = $event', emit-value, map-options)
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Description
        km-input(:model-value='description', @update:model-value='description = $event')
      div.q-mt-8
        .row.items-center.q-gap-8
          km-checkbox(label='Default Model', :model-value='is_default', dense, disable)
          q-icon(name='o_info', size='16px', color='secondary-text')
            q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') If marked as Default, model will be selected by default on related tools
          .q-ml
            km-btn(flat, label='Edit defaults', color='primary', @click='goToDefaultModels')
      q-separator.q-my-16
      
      // Features section for prompts models
      template(v-if='type === "prompts"')
        .km-title Features
        km-checkbox(label='JSON mode', :model-value='json_mode', @update:model-value='json_mode = $event')
        km-checkbox(label='Structured Outputs', :model-value='json_schema', @update:model-value='json_schema = $event')
        km-checkbox(label='Tool calling', :model-value='tool_calling', @update:model-value='tool_calling = $event')
        km-checkbox(label='Reasoning', :model-value='reasoning', @update:model-value='reasoning = $event')
      
      // Vector configuration for embeddings models
      template(v-if='type === "embeddings"')
        .km-title Vector Configuration
        div
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Vector Size
          km-input(
            height='32px',
            type='number',
            placeholder='E.g. 1536',
            :model-value='vectorSize',
            @update:model-value='vectorSize = $event'
          )
          .km-description.text-secondary-text.q-pl-8.q-pt-xs Dimension of the embedding vector. Common values: 1536 (ada-002), 1024 (embed-3-small), 3072 (embed-3-large)
    
    .column.fit.q-gap-16.overflow-auto.q-pa-16(v-if='tab == "pricing"')
      .km-title Inputs
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Input units
        km-select(height='32px', :options='priceUnitOptions', :model-value='price_input_unit_name', @update:model-value='price_input_unit_name = $event', emit-value, map-options)
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Price for standard input
        .row.items-center.q-gap-8.no-wrap
          km-input(prefix='$', height='32px', :model-value='price_standard_input', @update:model-value='price_standard_input = $event', style='max-width: 120px')
          .text-secondary-text per
          km-input(height='32px', :model-value='price_standard_input_unit_count', @update:model-value='price_standard_input_unit_count = $event', style='max-width: 120px')
          .text-secondary-text {{ price_input_unit_name }}
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Price for cached input
        .row.items-center.q-gap-8.no-wrap
          km-input(prefix='$', height='32px', :model-value='price_cached_input', @update:model-value='price_cached_input = $event', style='max-width: 120px')
          .text-secondary-text per
          km-input(height='32px', :model-value='price_cached_input_unit_count', @update:model-value='price_cached_input_unit_count = $event', style='max-width: 120px')
          .text-secondary-text {{ price_input_unit_name }}
      q-separator.q-my-16
      .km-title Outputs
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Output units
        km-select(height='32px', :options='priceUnitOptions', :model-value='price_output_unit_name', @update:model-value='price_output_unit_name = $event', emit-value, map-options)
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Price for standard output
        .row.items-center.q-gap-8.no-wrap
          km-input(prefix='$', height='32px', :model-value='price_standard_output', @update:model-value='price_standard_output = $event', style='max-width: 120px')
          .text-secondary-text per
          km-input(height='32px', :model-value='price_standard_output_unit_count', @update:model-value='price_standard_output_unit_count = $event', style='max-width: 120px')
          .text-secondary-text {{ price_output_unit_name }}
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Price for cached output
        .row.items-center.q-gap-8.no-wrap
          km-input(prefix='$', height='32px', :model-value='price_reasoning_output', @update:model-value='price_reasoning_output = $event', style='max-width: 120px')
          .text-secondary-text per
          km-input(height='32px', :model-value='price_reasoning_output_unit_count', @update:model-value='price_reasoning_output_unit_count = $event', style='max-width: 120px')
          .text-secondary-text {{ price_output_unit_name }}
  .col-auto.q-pa-16(v-if='isEntityChanged')
    .row.justify-end.q-gap-8
      km-btn(flat, label='Cancel', color='primary', @click='cancelChanges', data-test='Cancel')
      km-btn(label='Save', @click='save', data-test='Save')

q-inner-loading(:showing='loading')

</template>
<script>
import { ref } from 'vue'
import { useChroma } from '@shared'
import { categoryOptions } from '../../config/model/model.js'

export default {
  setup() {
    const { items, update, create, selectedRow, ...useCollection } = useChroma('model')

    return {
      tab: ref('parameters'),
      tabs: ref([
        { name: 'parameters', label: 'Parameters' },
        { name: 'pricing', label: 'Pricing' },
      ]),
      priceUnitOptions: ref([
        { label: 'Tokens', value: 'tokens' },
        { label: 'Characters', value: 'characters' },
        { label: 'Queries', value: 'queries' },
      ]),
      categoryOptions,
      loading: ref(false),
      items,
      update,
      create,
      selectedRow,
      useCollection,
    }
  },
  computed: {
    modelConfig() {
      return this.$store.getters['modelConfig/entity']
    },
    isEntityChanged() {
      return this.$store.getters['modelConfig/isEntityChanged']
    },
    display_name: {
      get() {
        return this.modelConfig?.display_name || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'display_name', value })
      },
    },
    description: {
      get() {
        return this.modelConfig?.description || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'description', value })
      },
    },
    system_name: {
      get() {
        return this.modelConfig?.system_name || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'system_name', value })
      },
    },
    provider: {
      get() {
        return this.modelConfig?.provider_name || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'provider_name', value })
      },
    },
    provider_system_name: {
      get() {
        return this.modelConfig?.provider_system_name || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'provider_system_name', value })
      },
    },
    model: {
      get() {
        return this.modelConfig?.ai_model || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'ai_model', value })
      },
    },
    type: {
      get() {
        return this.modelConfig?.type || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'type', value })
      },
    },
    is_default: {
      get() {
        return this.modelConfig?.is_default || false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'is_default', value })
      },
    },
    json_mode: {
      get() {
        return this.modelConfig?.json_mode || false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'json_mode', value })
      },
    },
    json_schema: {
      get() {
        return this.modelConfig?.json_schema || false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'json_schema', value })
      },
    },
    tool_calling: {
      get() {
        return this.modelConfig?.tool_calling || false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'tool_calling', value })
      },
    },
    reasoning: {
      get() {
        return this.modelConfig?.reasoning || false
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'reasoning', value })
      },
    },
    price_input_unit_name: {
      get() {
        return this.modelConfig?.price_input_unit_name || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_input_unit_name', value })
      },
    },
    price_standard_input: {
      get() {
        return this.modelConfig?.price_input || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_input', value: parseFloat(value) })
      },
    },
    price_standard_input_unit_count: {
      get() {
        return this.modelConfig?.price_standard_input_unit_count || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_standard_input_unit_count', value: parseFloat(value) })
      },
    },
    price_cached_input: {
      get() {
        return this.modelConfig?.price_cached || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_cached', value: parseFloat(value) })
      },
    },
    price_cached_input_unit_count: {
      get() {
        return this.modelConfig?.price_cached_input_unit_count || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_cached_input_unit_count', value: parseFloat(value) })
      },
    },
    price_output_unit_name: {
      get() {
        return this.modelConfig?.price_output_unit_name || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_output_unit_name', value })
      },
    },
    price_standard_output: {
      get() {
        return this.modelConfig?.price_output || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_output', value: parseFloat(value) })
      },
    },
    price_standard_output_unit_count: {
      get() {
        return this.modelConfig?.price_standard_output_unit_count || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_standard_output_unit_count', value: parseFloat(value) })
      },
    },
    price_reasoning_output: {
      get() {
        return this.modelConfig?.price_reasoning || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_reasoning', value: parseFloat(value) })
      },
    },
    price_reasoning_output_unit_count: {
      get() {
        return this.modelConfig?.price_reasoning_output_unit_count || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'price_reasoning_output_unit_count', value: parseFloat(value) })
      },
    },
    resources: {
      get() {
        return this.modelConfig?.resources || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'resources', value })
      },
    },
    vectorSize: {
      get() {
        const configs = this.modelConfig?.configs || {}
        return configs.vector_size || 1536
      },
      set(value) {
        const configs = this.modelConfig?.configs || {}
        const newConfigs = { ...configs, vector_size: parseInt(value) || 1536 }
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'configs', value: newConfigs })
      },
    },
  },
  methods: {
    async save() {
      this.loading = true
      try {
        await this.$store.dispatch('modelConfig/saveEntity')
        this.$q.notify({
          position: 'top',
          message: 'Model has been saved.',
          color: 'positive',
          textColor: 'black',
          timeout: 1000,
        })
      } catch (error) {
        console.error('Error saving model:', error)
        this.$q.notify({
          position: 'top',
          message: 'Error saving model.',
          color: 'negative',
          textColor: 'white',
          timeout: 2000,
        })
      } finally {
        this.loading = false
      }
    },
    cancelChanges() {
      this.$store.commit('modelConfig/revertEntity')
    },
    goToDefaultModels() {
      this.$router.push({ name: 'ModelProviders', query: { tab: 'DefaultModels' } })
    },
  },
}
</script>
