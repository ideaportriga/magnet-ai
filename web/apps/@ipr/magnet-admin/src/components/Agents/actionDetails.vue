<template>
  <km-inner-loading :showing="loading" />
  <layouts-details-layout v-if="!loading" :name="name" :description="description" :system-name="system_name" @update:name="name = $event" @update:description="description = $event" @update:system-name="system_name = $event">
    <template #content>
      <div class="stack full-height full-width overflow-auto km-flex-min-0" data-gap="lg">
        <km-tabs v-if="tabs.length &gt; 1" v-model="tab" :items="tabs" class="bb-border full-width" narrow-indicator dense align="left" no-caps content-class="km-tabs" />
        <agents-action-details-general-settings v-if="tab == &quot;general-settings&quot;" />
        <agents-action-details-parameters v-if="tab == &quot;parameters&quot;" />
      </div>
    </template>
  </layouts-details-layout>
</template>

<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const { draft, isLoading, activeVariant, updateNestedListItemBySystemName } = useAgentEntityDetail()
    return {
      m,
      draft,
      isLoading,
      activeVariant,
      updateNestedListItemBySystemName,
      tab: ref('general-settings'),
    }
  },
  computed: {
    tabs() {
      const tabs = [{ value: 'general-settings', label: this.m.agents_generalSettings() }]
      if (this.action?.type == 'api') {
        tabs.push({ value: 'parameters', label: this.m.agents_parameters() })
      }
      return tabs
    },
    routeParams() {
      return this.$route.params
    },
    topic() {
      return (this.activeVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    action() {
      return this.topic?.actions?.find((action) => action?.system_name == this.routeParams?.actionId)
    },
    name: {
      get() {
        return this.action?.name || ''
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.topic?.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.system_name,
          data: {
            name: value,
          },
        })
      },
    },
    description: {
      get() {
        return this.action?.description || ''
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.topic?.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.system_name,
          data: {
            description: value,
          },
        })
      },
    },
    system_name: {
      get() {
        return this.action?.system_name || ''
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.topic?.system_name,
          subArrayKey: 'actions',
          subItemSystemName: this.system_name,
          data: {
            system_name: value,
          },
        })
      },
    },
    loading() {
      return this.isLoading || !this.draft?.id
    },
  },

}
</script>

<style>
.wobble {
  animation: ds-attention-wobble var(--ds-duration-attention) infinite;
}
</style>
