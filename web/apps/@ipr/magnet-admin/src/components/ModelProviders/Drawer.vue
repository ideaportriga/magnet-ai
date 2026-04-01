<template lang="pug">
km-drawer-layout(storageKey="drawer-model-providers", noScroll)
  template(#tabs)
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
  .column.no-wrap.fit.q-gap-16(v-if='tab == "parameters"')
    .km-title General settings
    div
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Provider Name
      km-input(label='Provider Name', :model-value='provider?.name', @update:model-value='updateProviderProperty("name", $event)')
    div
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Display Name
      km-input(label='Display Name', :model-value='provider?.name', @update:model-value='updateProviderProperty("name", $event)')
    div
      .km-field.text-secondary-text.q-pb-xs.q-pl-8 Description
      km-input(label='Description', :model-value='provider?.description', @update:model-value='updateProviderProperty("description", $event)')
    div
      km-checkbox(label='Default', :model-value='false', disabled)
    q-separator
    .km-title Capabilities
    km-checkbox(label='JSON Mode', :model-value='false', disabled)
    km-checkbox(label='JSON Schema', :model-value='false', disabled)
    km-checkbox(label='Tool Calling', :model-value='false', disabled)
    km-checkbox(label='Reasoning', :model-value='false', disabled)
  .column.no-wrap.fit.q-gap-16(v-if='tab == "pricing"')
    .km-title Pricing
</template>
<script>
import { ref, computed } from 'vue'
import { useProviderDetailStore } from '@/stores/entityDetailStores'

export default {
  setup() {
    const providerStore = useProviderDetailStore()
    return {
      providerStore,
      tab: ref('parameters'),
      tabs: ref([
        { name: 'parameters', label: 'Parameters' },
        { name: 'pricing', label: 'Pricing' },
      ]),
    }
  },
  computed: {
    provider() {
      return this.providerStore.entity
    },
  },
  methods: {
    updateProviderProperty(key, value) {
      this.providerStore.updateProperty({ key, value })
    },
  },
}
</script>
