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
    .column.fit.q-gap-16.q-pa-16(v-if='tab == "parameters"')
      .km-title General settings
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Provider Name
        km-input(label='Key', :model-value='key')
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Display Name
        km-input(label='Key', :model-value='key')
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Description
        km-input(label='Key', :model-value='key')
      div
        km-checkbox(label='Default', :model-value='key')
      q-separator
      .km-title Capabilities
      km-checkbox(label='JSON Mode', :model-value='key')
      km-checkbox(label='JSON Schema', :model-value='key')
      km-checkbox(label='Tool Calling', :model-value='key')
      km-checkbox(label='Reasoning', :model-value='key')
    .column.fit.q-gap-16.q-pa-16(v-if='tab == "pricing"')
      .km-title Pricing
</template>
<script setup>
import { ref } from 'vue'
const tab = ref('parameters')
const tabs = ref([
  { name: 'parameters', label: 'Parameters' },
  { name: 'pricing', label: 'Pricing' },
])
</script>