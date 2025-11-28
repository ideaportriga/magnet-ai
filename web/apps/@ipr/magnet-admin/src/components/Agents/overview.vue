<template lang="pug">
div
  .column.items-center.full-height.full-width.q-gap-16.overflow-auto
    .row.km-heading-4 Configure your Agent
    .row.km-paragraph Make sure your Agent has all the essential parts to start working!

    .row.q-gap-16.full-width.items-center
      .col
        km-card(
          icon='fas fa-tag',
          label='Topics',
          description='Areas of Agent capabilities that include one or multiple Actions',
          actionLabel='Add Topic',
          @click='showNewTopicDialog = true',
          :qty='topicsQty'
        )
      .col
        km-card(
          icon='fas fa-puzzle-piece',
          label='Actions',
          description='Tools that the Agent can leverage to process user requests',
          :qty='actionsQty',
          actionLabel='Review Actions',
          @click='$emit("change-tab", "actions")'
        )
      .col
        km-card(
          icon='fas fa-wand-magic-sparkles',
          label='Agent Prompt Templates',
          description='Prompt Templates instruct the Agent how to select and process Topics.',
          actionLabel='Review Prompt Templates',
          @click='$emit("change-tab", "prompts")'
        )

    agents-create-new-topic(:showNewDialog='showNewTopicDialog', @cancel='showNewTopicDialog = false', v-if='showNewTopicDialog')
</template>

<script>
import { ref } from 'vue'
export default {
  emits: ['change-tab'],
  setup() {
    return {
      showNewTopicDialog: ref(false),
    }
  },
  computed: {
    topicsQty() {
      return this.$store.getters.agentDetailVariant?.value?.topics?.length || 0
    },
    actionsQty() {
      return this.$store.getters.agentDetailVariant?.value?.topics?.flatMap((topic) => topic.actions).length || 0
    },
  },
  created() {},
  methods: {},
}
</script>
