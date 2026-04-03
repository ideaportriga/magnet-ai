<template lang="pug">
.row.no-wrap.full-height(style='overflow: hidden; width: 100%')
  .col.column.no-wrap.full-height(style='min-width: 0; overflow: hidden')
    .column.full-height.q-px-md.q-pt-16
      .col.ba-border.border-radius-12.bg-white.q-pa-16.column(style='min-height: 0')
        component(:is='component', ref='componentRef', @selectRow='selectRow', :selectedRow='selectedRow')
  .col-auto(v-if='selectedRow')
    component(:is='drawer', :selectedRow='selectedRow', @close='selectedRow = null', @refresh='refresh')
</template>
<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useRoute } from 'vue-router'
export default {
  setup() {
    const route = useRoute()
    return {
      route,
      selectedRow: ref(null),
    }
  },

  computed: {
    tab() {
      return this.route.params.tab
    },
    component() {
      if (this.tab === 'rag') return 'dashboard-tab-rag'
      if (this.tab === 'agent') return 'dashboard-tab-agent'
      if (this.tab === 'llm') return 'dashboard-tab-llm'
      return null
    },
    drawer() {
      if (this.tab === 'rag') return 'dashboard-drawer-rag'
      if (this.tab === 'agent') return 'dashboard-drawer-agent'
      if (this.tab === 'llm') return 'dashboard-drawer-llm'
      return null
    },
  },
  watch: {
    tab() {
      this.selectedRow = null
    },
  },
  methods: {
    selectRow(row) {
      this.selectedRow = row
    },
    refresh() {
      this.$refs.componentRef.refresh()
    },
  },
}
</script>

<style lang="stylus" scoped></style>
