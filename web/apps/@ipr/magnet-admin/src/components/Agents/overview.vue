<template lang="pug">
div
  .column.items-center.full-height.full-width.q-gap-16.overflow-auto
    .row.km-heading-4 {{ m.agents_configureYourAgent() }}
    .row.km-paragraph {{ m.agents_agentEssentialParts() }}

    .row.q-gap-16.full-width.items-center
      .col
        km-card(
          icon='fas fa-tag',
          :label='m.common_topics()',
          :description='m.agents_topicsDescription()',
          :actionLabel='m.agents_addTopic()',
          @click='showNewTopicDialog = true',
          :qty='topicsQty'
        )
      .col
        km-card(
          icon='fas fa-puzzle-piece',
          :label='m.entity_action()',
          :description='m.agents_actionsDescription()',
          :qty='actionsQty',
          :actionLabel='m.agents_reviewActions()',
          @click='$emit("change-tab", "actions")'
        )
      .col
        km-card(
          icon='fas fa-wand-magic-sparkles',
          :label='m.agents_agentPromptTemplates()',
          :description='m.agents_agentPromptTemplatesDesc()',
          :actionLabel='m.agents_reviewPromptTemplates()',
          @click='$emit("change-tab", "prompts")'
        )

    agents-create-new-topic(:showNewDialog='showNewTopicDialog', @cancel='showNewTopicDialog = false', v-if='showNewTopicDialog')
</template>

<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
export default {
  emits: ['change-tab'],
  setup() {
    const { activeVariant } = useAgentEntityDetail()
    return {
      m,
      activeVariant,
      showNewTopicDialog: ref(false),
    }
  },
  computed: {
    topicsQty() {
      return this.activeVariant?.value?.topics?.length || 0
    },
    actionsQty() {
      return this.activeVariant?.value?.topics?.flatMap((topic) => topic.actions).length || 0
    },
  },
}
</script>
