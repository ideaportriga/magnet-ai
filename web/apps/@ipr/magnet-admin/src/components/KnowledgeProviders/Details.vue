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

<script>
import { ref, computed } from 'vue'
import { useChroma } from '@shared'
import { beforeRouteEnter } from '@/guards'

export default {
  beforeRouteEnter,
  setup() {
    const { selectedRow, ...useCollection } = useChroma('provider')
    
    return {
      tab: ref('knowledge-sources'),
      tabs: ref([
        { name: 'knowledge-sources', label: 'Knowledge Sources' },
        { name: 'settings', label: 'Settings' },
      ]),
      showInfo: ref(false),
      selectedRow,
      useCollection,
    }
  },
  computed: {
    provider() {
      return this.$store.getters.provider
    },
    name: {
      get() {
        return this.provider?.name || ''
      },
      set(value) {
        this.$store.commit('updateProviderProperty', { key: 'name', value })
      },
    },
    system_name: {
      get() {
        return this.provider?.system_name || ''
      },
      set(value) {
        this.$store.commit('updateProviderProperty', { key: 'system_name', value })
      },
    },
  },
  watch: {
    selectedRow: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          this.$store.commit('setProvider', newVal)
        }
      },
    },
  },
}
</script>