<template>
  <div class="cluster full-height" data-wrap="no" style="overflow: hidden; inline-size: 100%">
    <div class="flex-1 stack full-height" data-gap="0" style="min-inline-size: 0; overflow: hidden">
      <div class="stack full-height px-md pt-lg" data-gap="0">
        <div class="flex-1 ba-border border-radius-12 bg-white p-lg stack" data-gap="0" style="min-block-size: 0">
          <component :is="component" ref="componentRef" :selected-row="selectedRow" @select-row="selectRow" />
        </div>
      </div>
    </div>
    <div v-if="selectedRow" class="flex-none">
      <component :is="drawer" :selected-row="selectedRow" @close="selectedRow = null" @refresh="refresh" />
    </div>
  </div>
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
