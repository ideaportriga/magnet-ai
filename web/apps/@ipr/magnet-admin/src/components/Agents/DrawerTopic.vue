<template lang="pug">
km-drawer-layout(storageKey="drawer-agents-topic")
  template(#header)
    .row.items-center
      km-btn(
        flat,
        simple,
        :label='`Back to Agent Preview`',
        iconSize='16px',
        icon='fas fa-arrow-left',
        @click='activeTopic = null',
        color='secondary-text'
      )
    .km-heading-4.q-mt-md Topic details
  .km-field.text-secondary-text.q-pb-sm.q-pl-8 Name
    km-input(ref='input', border-radius='8px', height='36px', type='text', v-model='name')
  .km-field.text-secondary-text.q-pb-sm.q-pl-8 System name
    km-input(ref='input', border-radius='8px', height='36px', type='text', v-model='system_name')
  .km-field.text-secondary-text.q-pb-sm.q-pl-8 Description for LLM
    km-input(ref='input', rows='10', border-radius='8px', height='36px', type='textarea', v-model='description')
  .row.items-center.justify-end
    .km-button-text.q-mb-xs.q-ml-sm.text-text-gray
    km-btn(
      flat,
      iconAfter='fas fa-arrow-right',
      @click='openTopicDetails',
      iconSize='16px',
      color='secondary-text',
      label='More details & Actions'
    )
</template>

<script>
import { useAgentDetailStore } from '@/stores/agentDetailStore'
export default {
  setup() {
    const agentStore = useAgentDetailStore()
    return { agentStore }
  },
  computed: {
    routeParams() {
      return this.$route.params
    },
    activeTopic: {
      get() {
        return this.agentStore.activeTopic
      },
      set(value) {
        this.agentStore.activeTopic = value
      },
    },
    topic() {
      return (this.agentStore.activeVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.activeTopic?.topic)
    },
    name: {
      get() {
        return this.topic?.name || ''
      },
      set(value) {
        this.agentStore.updateNestedListItemBySystemName({
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
        this.agentStore.updateNestedListItemBySystemName({
          arrayPath: 'topics',
          itemSystemName: this.system_name,
          data: {
            system_name: value,
          },
        })
        this.agentStore.activeTopic = {
          topic: value,
        }
      },
    },
    instructions: {
      get() {
        return this.topic?.instructions || ''
      },
      set(value) {
        this.agentStore.updateNestedListItemBySystemName({
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
        this.agentStore.updateNestedListItemBySystemName({
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
