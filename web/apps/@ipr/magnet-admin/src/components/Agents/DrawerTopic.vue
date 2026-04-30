<template>
  <km-drawer-layout storage-key="drawer-agents-topic">
    <template #header>
      <div class="cluster">
        <km-btn flat simple :label="m.agents_backToAgentPreview()" icon-size="16px" icon="arrow-left" tone="subtle" @click="activeTopic = null" />
      </div>
      <div class="km-heading-4 mt-md">{{ m.agents_topicDetails() }}</div>
    </template>
    <div class="km-field text-secondary-text pb-sm pl-sm">
      Name
      <km-input ref="input" v-model="name" border-radius="8px" height="36px" type="text" />
    </div>
    <div class="km-field text-secondary-text pb-sm pl-sm">
      System name
      <km-input ref="input" v-model="system_name" border-radius="8px" height="36px" type="text" />
    </div>
    <div class="km-field text-secondary-text pb-sm pl-sm">
      Description for LLM
      <km-input ref="input" v-model="description" rows="10" border-radius="8px" height="36px" type="textarea" />
    </div>
    <div class="cluster" data-justify="end">
      <div class="km-button-text mb-xs ml-sm text-text-gray" />
      <km-btn flat icon-after="arrow-right" icon-size="16px" tone="subtle" :label="m.common_moreDetailsAndActions()" @click="openTopicDetails" />
    </div>
  </km-drawer-layout>
</template>

<script>
import { m } from '@/paraglide/messages'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
export default {
  setup() {
    const { activeVariant, activeTopic: activeTopicRef, updateNestedListItemBySystemName } = useAgentEntityDetail()
    return { m, activeVariant, activeTopicRef, updateNestedListItemBySystemName }
  },
  computed: {
    routeParams() {
      return this.$route.params
    },
    activeTopic: {
      get() {
        return this.activeTopicRef
      },
      set(value) {
        this.activeTopicRef = value
      },
    },
    topic() {
      return (this.activeVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.activeTopic?.topic)
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
    system_name: {
      get() {
        return this.topic?.system_name || ''
      },
      set(value) {
        if (!value?.length) return
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.system_name,
          data: {
            system_name: value,
          },
        })
        this.activeTopicRef = {
          topic: value,
        }
      },
    },
    instructions: {
      get() {
        return this.topic?.instructions || ''
      },
      set(value) {
        this.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.system_name,
          data: {
            instructions: value,
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
  },
  methods: {
    openTopicDetails() {
      this.navigate(`agents/${this.routeParams?.id}/topics/${this.activeTopic.topic}`)
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
  },
}
</script>
