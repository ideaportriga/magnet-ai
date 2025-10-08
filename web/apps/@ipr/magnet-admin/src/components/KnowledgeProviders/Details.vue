<template lang="pug">
  layouts-details-layout(:contentContainerStyle='{ maxWidth: "1200px", margin: "0 auto" }')
    template(#header)
      .col
        .row.items-center
          km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', :model-value='name', @change='name = $event')
        .row.items-center.q-pl-6
          q-icon.col-auto(name='o_info', color='text-secondary')
            q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
          km-input-flat.col.km-description.text-black.full-width(
            placeholder='Enter system name',
            v-model='system_name',
            @focus='showInfo = true',
            @blur='showInfo = false'
          )
        .km-description.text-secondary.q-pl-6(v-if='showInfo') It is highly recommended to fill in system name only once and not change it later.
    template(#content)
      .full-width
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
        .column.q-gap-16.overflow-auto.q-pt-lg.q-pb-lg
          knowledge-providers-knowledge-sources(v-if='tab == "knowledge-sources"')
          knowledge-providers-settings(v-if='tab == "settings"')
  </template>
  
  <script setup>
  import {ref} from 'vue'
  const tab = ref('knowledge-sources')
  const tabs = ref([
    { name: 'knowledge-sources', label: 'Knowledge Sources' },
    { name: 'settings', label: 'Settings' },
  ])
  
  
  </script>