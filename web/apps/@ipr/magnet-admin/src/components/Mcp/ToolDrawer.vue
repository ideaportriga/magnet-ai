<template>
  <km-drawer-layout storage-key="drawer-mcp-tools">
    <template #tabs>
      <div class="pt-lg px-lg">
        <km-tabs v-model="tab" class="full-width" narrow-indicator dense align="left" no-caps content-class="km-tabs">
          <template v-for="t in tabs" :key="t">
            <km-tab :name="t.name" :label="t.label" />
          </template>
          <div class="fit" />
        </km-tabs>
      </div>
    </template>
    <template v-if="tab == &quot;details&quot;">
      <div class="stack fit">
        <div v-if="selectedRow" class="flex-1 fit">
          <div class="stack">
            <div class="basis-12 py-sm">
              <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_name() }}</div>
              <km-input :model-value="selectedRow.name" readonly />
            </div>
            <div class="basis-12 py-sm">
              <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_description() }}</div>
              <div class="km-textarea-relaxed">
                <km-input :model-value="selectedRow.description" type="textarea" rows="3" autogrow readonly />
              </div>
            </div>
            <div class="basis-12 py-sm">
              <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_type() }}</div>
              <km-input :model-value="selectedRow.type" readonly />
            </div>
          </div>
        </div>
      </div>
    </template>
    <template v-if="tab == &quot;test&quot;">
      <div class="pb-3xl">
        <div class="flex-none">
          <div class="cluster" data-justify="between">
            <div class="km-heading-7 mb-lg">{{ m.common_inputs() }}</div>
          </div>
          <div class="stack fit">
            <km-codemirror v-model="inputParametersString" :style="{ minHeight: &quot;150px&quot; }" :options="{ mode: &quot;application/json&quot; }" language="json" />
          </div>
          <div class="cluster full-width" data-justify="end">
            <km-btn class="my-sm border-radius-6" :disable="processing" unelevated padding="7px 8px" @click="testMcpTool">
              <template #default>
                <km-glyph name="send" size="16px" />
              </template>
            </km-btn>
          </div>
        </div>
        <template v-if="processing">
          <div class="flex" style="flex-direction: column; justify-content: center; align-items: center">
            <km-loader size="62px" />
          </div>
        </template>
        <div class="flex-none">
          <div class="cluster" data-justify="between">
            <div class="km-heading-7 mb-lg">{{ m.common_outputs() }}</div>
          </div>
          <div v-if="output" class="stack fit">
            <km-codemirror :model-value="JSON.stringify(output, null, 2)" :style="{ minHeight: &quot;150px&quot; }" :options="{ mode: &quot;application/json&quot; }" language="json" readonly />
          </div>
        </div>
      </div>
    </template>
  </km-drawer-layout>
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
