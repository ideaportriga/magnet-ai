<template>
  <km-inner-loading :showing="loading" />
  <layouts-details-layout v-if="!loading" :name="name" :description="description" :system-name="system_name" @update:name="name = $event" @update:description="description = $event" @update:system-name="system_name = $event">
    <template #content>
      <div class="stack full-height full-width overflow-auto km-flex-min-0" data-gap="lg">
        <agents-topic-details-prompts />
        <km-separator class="my-lg" />
        <agents-topic-details-actions />
      </div>
    </template>
  </layouts-details-layout>
</template>

<script>
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const { draft, isLoading, activeVariant, updateNestedListItemBySystemName } = useAgentEntityDetail()
    return {
      draft,
      isLoading,
      activeVariant,
      updateNestedListItemBySystemName,
    }
  },
  computed: {
    routeParams() {
      return this.$route.params
    },
    topic() {
      return (this.activeVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    name: {
      get() {
        return this.topic?.name || ''
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.system_name,
          data: {
            name: value,
          },
        })
      },
    },
    description: {
      get() {
        return this.topic?.description || ''
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.system_name,
          data: {
            description: value,
          },
        })
      },
    },
    system_name: {
      get() {
        return this.topic?.system_name || ''
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.system_name,
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
