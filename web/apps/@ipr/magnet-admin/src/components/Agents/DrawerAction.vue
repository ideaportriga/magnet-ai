<template>
  <km-drawer-layout storage-key="drawer-agents-action" no-scroll>
    <template #header>
      <div class="cluster">
        <km-btn flat simple :label="m.agents_backToAgentPreview()" icon-size="16px" icon="arrow-left" tone="subtle" @click="activeTopic = null" />
      </div>
    </template>
    <div class="cluster">
      <km-tabs v-if="tabs.length &gt; 1" v-model="tab" narrow-indicator dense align="left" no-caps content-class="km-tabs-dense">
        <template v-for="t in tabs" :key="t.name">
          <km-tab :name="t.name" :label="t.label" />
        </template>
      </km-tabs>
    </div>
    <div class="stack full-height full-width overflow-auto mb-md mt-lg" data-gap="lg" style="max-block-size: calc(100vb - 220px) !important">
      <div class="cluster full-height full-width" data-gap="lg">
        <div class="flex-1 full-height full-width">
          <div class="stack items-center full-height full-width overflow-auto" data-gap="lg">
            <div class="flex-none full-width">
              <template v-if="tab == &quot;general-settings&quot;">
                <agents-action-details-general-settings-drawer />
              </template>
              <template v-if="tab == &quot;advanced-settings&quot;">
                <agents-action-details-advanced-settings-drawer :action="action" />
              </template>
              <template v-if="tab == &quot;parameters&quot;">
                <agents-action-details-parameters-drawer />
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </km-drawer-layout>
</template>

<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'

export default {
  setup() {
    const tab = ref('general-settings')
    const { activeVariant, activeTopic: activeTopicRef } = useAgentEntityDetail()
    return { m, tab, activeVariant, activeTopicRef }
  },
  computed: {
    activeTopic: {
      get() {
        return this.activeTopicRef
      },
      set(value) {
        this.activeTopicRef = value
      },
    },
    routeParams() {
      return this.$route.params
    },
    topic() {
      return (this.activeVariant?.value?.topics || []).find((topic) => topic?.system_name === this.routeParams.topicId)
    },
    action() {
      return this.topic?.actions?.find((act) => act?.system_name === this.activeTopic?.action)
    },
    tabs() {
      const tabs = [
        { name: 'general-settings', label: m.agents_generalSettings() },
        { name: 'advanced-settings', label: m.agents_advancedSettings() },
      ]
      if (this.action?.type === 'api' || this.action?.type === 'mcp_tool') {
        tabs.push({ name: 'parameters', label: m.agents_parameters() })
      }
      return tabs
    },
  },
}
</script>

<style>
.wobble {
  animation: ds-attention-wobble var(--ds-duration-attention) infinite;
}
</style>
