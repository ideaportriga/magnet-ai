<template lang="pug">
.no-wrap.full-height(style='max-width: 500px; min-width: 500px !important')
  .row.full-height
    .col.full-height
      .column.full-height.q-pa-16.bg-white.bl-border
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

        q-separator.q-mb-md
        .km-heading-4.q-mb-lg Topic details
        .km-field.text-secondary-text.q-pb-sm.q-pl-8 Name
          km-input(ref='input', border-radius='8px', height='36px', type='text', v-model='name')
        .km-field.text-secondary-text.q-pb-sm.q-pl-8 System name
          km-input(ref='input', border-radius='8px', height='36px', type='text', v-model='system_name')
        .km-field.text-secondary-text.q-pb-sm.q-pl-8 LLM description
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
export default {
  computed: {
    routeParams() {
      return this.$route.params
    },
    activeTopic: {
      get() {
        return this.$store.getters.activeTopic
      },
      set(value) {
        this.$store.commit('setActiveTopic', value)
      },
    },
    topic() {
      return (this.$store.getters.agentDetailVariant?.value?.topics || [])?.find((topic) => topic?.system_name === this.activeTopic?.topic)
    },
    name: {
      get() {
        return this.topic?.name || ''
      },
      set(value) {
        this.$store.commit('updateNestedAgentDetailListItemBySystemName', {
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
