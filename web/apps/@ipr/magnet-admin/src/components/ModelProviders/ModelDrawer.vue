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
    .column.fit.q-gap-16.overflow-auto.q-pa-16(v-if='tab == "settings"')
      .km-title General settings
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Display Name
        km-input(label='Display Name', :model-value='display_name', @update:model-value='display_name = $event')
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Description
        km-input(label='Description', :model-value='description', @update:model-value='description = $event')
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 System Name
        km-input(label='System Name', :model-value='system_name', @update:model-value='system_name = $event')
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Provider
        km-input(label='Provider', :model-value='provider', disabled)
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 AI Model
        km-input(label='AI Model', :model-value='model', @update:model-value='model = $event')
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Type
        km-input(label='Type', :model-value='type', @update:model-value='type = $event')
      div
        km-checkbox(label='Default', :model-value='is_default', disabled)
      q-separator
      .km-title Capabilities
      km-checkbox(label='JSON Mode', :model-value='json_mode', @update:model-value='json_mode = $event')
      km-checkbox(label='JSON Schema', :model-value='json_schema', @update:model-value='json_schema = $event')
      km-checkbox(label='Tool Calling', :model-value='tool_calling', @update:model-value='tool_calling = $event')
      km-checkbox(label='Reasoning', :model-value='reasoning', @update:model-value='reasoning = $event')
    .column.fit.q-gap-16.overflow-auto.q-pa-16(v-if='tab == "pricing"')
      .km-title Input Pricing
      .row.items-center.q-gap-8
        .text-secondary-text Unit
        km-select.col(height='32px', :options='priceUnitOptions', v-model='price_input_unit_name', style='max-width: 200px')
      .row.items-center.q-gap-8
        .text-secondary-text Standard input
        km-input(prefix='$', height='32px', v-model='price_standard_input', style='max-width: 200px')
        .text-secondary-text per
        km-input(height='32px', v-model='price_standard_input_unit_count', style='max-width: 150px')
        .text-secondary-text {{ price_input_unit_name }}
      .row.items-center.q-gap-8
        .text-secondary-text Cached input
        km-input(prefix='$', height='32px', v-model='price_cached_input', style='max-width: 200px')
        .text-secondary-text per
        km-input(height='32px', v-model='price_cached_input_unit_count', style='max-width: 150px')
        .text-secondary-text {{ price_input_unit_name }}
      q-separator.q-my-16
      .km-title Output Pricing
      .row.items-center.q-gap-8
        .text-secondary-text Unit
        km-select.col(height='32px', :options='priceUnitOptions', v-model='price_output_unit_name', style='max-width: 200px')
      .row.items-center.q-gap-8
        .text-secondary-text Standard output
        km-input(prefix='$', height='32px', v-model='price_standard_output', style='max-width: 200px')
        .text-secondary-text per
        km-input(height='32px', v-model='price_standard_output_unit_count', style='max-width: 150px')
        .text-secondary-text {{ price_output_unit_name }}
      .row.items-center.q-gap-8
        .text-secondary-text Reasoning output
        km-input(prefix='$', height='32px', v-model='price_reasoning_output', style='max-width: 200px')
        .text-secondary-text per
        km-input(height='32px', v-model='price_reasoning_output_unit_count', style='max-width: 150px')
        .text-secondary-text {{ price_output_unit_name }}
      q-separator.q-my-16
      .km-title Resources
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Documentation URL
        km-input(label='Resources', :model-value='resources', @update:model-value='resources = $event')
</template>
<script>
import { ref } from 'vue'

export default {
  setup() {
    return {
      tab: ref('settings'),
      tabs: ref([
        { name: 'settings', label: 'Settings' },
        { name: 'pricing', label: 'Pricing' },
      ]),
      priceUnitOptions: ref([
        { label: 'Tokens', value: 'tokens' },
        { label: 'Characters', value: 'characters' },
        { label: 'Queries', value: 'queries' },
      ]),
    }
  },
  computed: {
    modelConfig() {
      return this.$store.getters['modelConfig/entity']
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
        return this.modelConfig?.provider || ''
      },
      set(value) {
        this.$store.commit('modelConfig/updateEntityProperty', { key: 'provider', value })
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
  },
}
</script>
