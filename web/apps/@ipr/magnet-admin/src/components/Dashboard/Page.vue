<template lang="pug">
.row.no-wrap.overflow-hidden.full-height
  .fit(style='overflow-y: auto')
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container.full-width
        .full-height.q-pb-md.relative-position.q-px-md.q-py-md
          .border.border-radius-12.bg-white.ba-border.q-pa-16.q-gap-16.full-width
            component(:is='component', ref='componentRef', @selectRow='selectRow', :selectedRow='selectedRow')
  component(:is='drawer', :selectedRow='selectedRow', @close='selectedRow = null', @refresh='refresh')
</template>
<script>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
export default {
  setup() {
    const route = useRoute()
    // const tab = ref('rag')
    // const tabs = ref([
    //   { name: 'rag', label: 'RAG Queries', icon: 'fas fa-file-circle-question' },
    //   { name: 'agent', label: 'Agent Conversations', icon: 'fa fa-robot' },
    //   { name: 'llm', label: 'LLM Calls', icon: 'fa fa-comment-dots' },
    // ])
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
