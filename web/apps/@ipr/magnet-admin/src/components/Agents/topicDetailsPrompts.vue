<template lang="pug">
div
  agents-topic-action-template-section
  q-separator.q-my-lg
  km-section(
    title='Topic advanced instructions',
    subTitle='Optional additional instructions on how to call actions inside the Topic.These instructions will be merged into Agent\'s Topic processing prompt inside the {TOPIC_INSTRUCTIONS} placeholder.'
  )
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Advanced instructions
      km-input(ref='input', rows='10', border-radius='8px', height='36px', type='textarea', v-model='instructions')
</template>

<script>
export default {
  emits: ['openTest'],
  setup() {},
  computed: {
    routeParams() {
      return this.$route.params
    },
    topic() {
      return (this.$store.getters.agentDetailVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.routeParams?.topicId)
    },
    system_name: {
      get() {
        return this.topic?.system_name || ''
      },
      set(value) {
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
