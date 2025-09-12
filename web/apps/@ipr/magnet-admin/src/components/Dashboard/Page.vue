<template lang="pug">
.row.no-wrap.overflow-hidden.full-height
  .fit(style="overflow-y: auto;")
    .row.no-wrap.full-height.justify-center.fit
      .col-auto.collection-container.full-width
        .full-height.q-pb-md.relative-position.q-px-md.q-py-md
          .border.border-radius-12.bg-white.ba-border.q-pa-16.q-gap-16.full-width
            .row.q-mb-12
              .col-auto.center-flex-y.full-width
                q-tabs.bb-border.full-width.q-mb-8(
                  v-model='tab',
                  narrow-indicator,
                  dense,
                  align='left',
                  active-color='primary',
                  indicator-color='primary',
                  active-bg-color='white',
                  no-caps,
                  content-class='km-tabs',
                  inline-label
                )
                  template(v-for='t in tabs')
                    q-tab(:name='t.name')
                      .row.q-gap-8.items-center.q-px-6
                        q-icon(:name='t.icon', :color='t.name === tab ? "primary" : "icon"')
                        .km-title {{ t.label }}
              .col-12
                component(:is='component', ref='componentRef', @selectRow='selectRow', :selectedRow='selectedRow')
  component(:is='drawer', :selectedRow='selectedRow', @close='selectedRow = null', @refresh='refresh')
</template>
<script>
import { ref } from 'vue'

export default {
  setup() {
    const tab = ref('rag')
    const tabs = ref([
      { name: 'rag', label: 'RAG Queries', icon: 'fas fa-file-circle-question' },
      { name: 'agent', label: 'Agent Conversations', icon: 'fa fa-robot' },
      { name: 'llm', label: 'LLM Calls', icon: 'fa fa-comment-dots' },
    ])
    return {
      tab,
      tabs,
      selectedRow: ref(null),
    }
  },

  computed: {
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
