<template lang="pug">
km-drawer-layout(storageKey="drawer-mcp-tools")
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
  template(v-if='tab == "details"')
    .column.fit
      .col.fit(v-if='selectedRow')
        .row.justify-between
          .col-12.q-py-8
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_name() }}
            km-input(:model-value='selectedRow.name', readonly)
          .col-12.q-py-8
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_description() }}
            .km-textarea-relaxed
              km-input(v-model='selectedRow.description', type='textarea', rows='3', autogrow, readonly)
          .col-12.q-py-8
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_type() }}
            km-input(:model-value='selectedRow.type', readonly)
  template(v-if='tab == "test"')
    .q-pb-32
      .col-auto
        .row.items-center.justify-between
          .km-heading-7.q-mb-16 {{ m.common_inputs() }}
        .column.fit
          km-codemirror(
            v-model='inputParametersString',
            :style='{ minHeight: "150px" }',
            :options='{ mode: "application/json" }',
            language='json'
          )
        .row.justify-end.full-width
          q-btn.q-my-6.border-radius-6(color='primary', @click='testMcpTool', :disable='processing', unelevated, padding='7px 8px')
            template(v-slot:default)
              q-icon(name='fas fa-paper-plane', size='16px')
      template(v-if='processing')
        .column.justify-center.items-center
          q-spinner-dots(size='62px', color='primary')

      .col-auto
        .row.items-center.justify-between
          .km-heading-7.q-mb-16 {{ m.common_outputs() }}
        .column.fit(v-if='output')
          km-codemirror(
            :model-value='JSON.stringify(output, null, 2)',
            :style='{ minHeight: "150px" }',
            :options='{ mode: "application/json" }',
            language='json',
            readonly
          )
</template>
<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { fetchData } from '@shared'
import { useRoute } from 'vue-router'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useAppStore } from '@/stores/appStore'
export default {
  props: {
    selectedRow: {
      type: Object,
      required: true,
    },
  },
  setup() {
    const route = useRoute()
    const { draft } = useEntityDetail('mcp_servers')
    const appStore = useAppStore()
    return {
      processing: ref(false),
      inputParametersString: ref('{}'),
      output: ref(''),
      tab: ref('details'),
      tabs: ref([
        { name: 'details', label: m.mcp_inputDetails() },
        { name: 'test', label: m.mcp_testMcpTool() },
      ]),
      route,
      draft,
      appStore,
      m,
    }
  },

  computed: {
    tool() {
      const tools = this.draft?.tools || []
      return tools.find((t) => t.name === this.route.params.name)
    },
  },
  watch: {},
  methods: {
    setTab(tab) {
      this.tab = tab
    },
    regulateTabs(parentTab) {
      if (parentTab === 'definition') {
        this.tab = 'test'
        this.tabs = [{ name: 'test', label: m.mcp_testMcpTool() }]
      } else {
        this.tabs = [
          { name: 'details', label: m.mcp_inputDetails() },
          { name: 'test', label: m.mcp_testMcpTool() },
        ]
      }
    },
    async testMcpTool() {
      if (this.processing) {
        return
      }

      let input = {}

      try {
        input = JSON.parse(this.inputParametersString)
      } catch (e) {
        this.appStore.setErrorMessage({
          technicalError: e,
          text: m.mcp_invalidJsonInput(),
        })
        return
      }

      this.processing = true
      try {
        const mcpId = this.draft?.id
        const endpoint = this.appStore.config?.mcp_servers?.endpoint
        const response = await fetchData({
          method: 'POST',
          service: `mcp_servers/${mcpId}/tools/${this.tool.name}/call`,
          credentials: 'include',
          body: JSON.stringify(input),
          endpoint,
          headers: { 'Content-Type': 'application/json' },
        })
        const res = await response.json()

        this.output = res
      } catch (e) {
        this.output = null
      } finally {
        this.processing = false
      }
    },
  },
}
</script>
