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
    .column.fit
      q-scroll-area.fit.q-px-16.q-py-32
        api-tools-test(v-if='tab == "test"')
        api-tools-input-details(v-if='tab == "details"', :selectedRow='selectedRow')
</template>
<script>
import { ref } from 'vue'
export default {
  props: {
    selectedRow: {
      type: Object,
      required: true,
    },
  },
  setup() {
    return {
      tab: ref('details'),
      tabs: ref([
        { name: 'details', label: 'Input Details' },
        { name: 'test', label: 'Test API Tool' },
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
        this.tabs = [{ name: 'test', label: 'Test API Tool' }]
      } else {
        this.tabs = [
          { name: 'details', label: 'Input Details' },
          { name: 'test', label: 'Test API Tool' },
        ]
      }
    },
  },
}
</script>
