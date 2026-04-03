<template lang="pug">
km-drawer-layout(storageKey="drawer-api-tools")
  template(#tabs)
    .q-pt-16.q-px-16
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
  api-tools-test(v-if='tab == "test"')
  api-tools-input-details(v-if='tab == "details"', :selectedRow='selectedRow')
</template>
<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
export default {
  props: {
    selectedRow: {
      type: Object,
      default: null,
    },
  },
  setup() {
    return {
      m,
      tab: ref('details'),
      tabs: ref([
        { name: 'details', label: m.apiTools_inputDetails() },
        { name: 'test', label: m.apiTools_testApiTool() },
      ]),
    }
  },

  computed: {},
  watch: {},
  methods: {
    setTab(tab) {
      this.tab = tab
    },
    regulateTabs(parentTab) {
      if (parentTab === 'information') {
        this.tab = 'test'
        this.tabs = [{ name: 'test', label: m.apiTools_testApiTool() }]
      } else {
        this.tabs = [
          { name: 'details', label: m.apiTools_inputDetails() },
          { name: 'test', label: m.apiTools_testApiTool() },
        ]
      }
    },
  },
}
</script>
