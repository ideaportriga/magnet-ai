<template lang="pug">
div
  agents-topic-action-template-section
  q-separator.q-my-lg
  km-section(
    :title='m.agents_topicAdvancedInstructions()',
    :subTitle='m.agents_topicAdvancedInstructionsSubtitle()'
  )
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.agents_advancedInstructionsLabel() }}
      km-input(ref='input', rows='10', border-radius='8px', height='36px', type='textarea', v-model='instructions')
</template>

<script>
import { m } from '@/paraglide/messages'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
export default {
  emits: ['openTest'],
  setup() {
    const { activeVariant, updateNestedListItemBySystemName } = useAgentEntityDetail()
    return { m, activeVariant, updateNestedListItemBySystemName }
  },
  computed: {
    routeParams() {
      return this.$route.params
    },
    topic() {
      return (this.activeVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
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
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
  },
}
</script>
