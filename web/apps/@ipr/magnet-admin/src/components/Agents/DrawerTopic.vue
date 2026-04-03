<template lang="pug">
km-drawer-layout(storageKey="drawer-agents-topic")
  template(#header)
    .row.items-center
      km-btn(
        flat,
        simple,
        :label='m.agents_backToAgentPreview()',
        iconSize='16px',
        icon='fas fa-arrow-left',
        @click='activeTopic = null',
        color='secondary-text'
      )
    .km-heading-4.q-mt-md {{ m.agents_topicDetails() }}
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
      :label='m.agents_moreDetailsAndActions()'
    )
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
