<template>
  <km-drawer-layout storage-key="drawer-api-tools">
    <template #tabs>
      <div class="pt-lg px-lg">
        <km-tabs v-model="tab" class="full-width" narrow-indicator dense align="left" no-caps content-class="km-tabs">
          <template v-for="t in tabs" :key="t.name">
            <km-tab :name="t.name" :label="t.label" />
          </template>
          <div class="fit" />
        </km-tabs>
      </div>
    </template>
    <api-tools-test v-if="tab == &quot;test&quot;" />
    <api-tools-input-details v-if="tab == &quot;details&quot;" :selected-row="selectedRow" />
  </km-drawer-layout>
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
