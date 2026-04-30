<template>
  <div>
    <div class="stack items-center full-height full-width overflow-auto" data-gap="lg">
      <div class="cluster km-heading-4">{{ m.agents_configureYourAgent() }}</div>
      <div class="cluster km-paragraph">{{ m.agents_agentEssentialParts() }}</div>
      <div class="cluster full-width" data-gap="lg">
        <div class="flex-1">
          <km-card icon="tag" :label="m.common_topics()" :description="m.agents_topicsDescription()" :action-label="m.agents_addTopic()" :qty="topicsQty" @click="showNewTopicDialog = true" />
        </div>
        <div class="flex-1">
          <km-card icon="puzzle" :label="m.entity_action()" :description="m.agents_actionsDescription()" :qty="actionsQty" :action-label="m.agents_reviewActions()" @click="$emit(&quot;change-tab&quot;, &quot;actions&quot;)" />
        </div>
        <div class="flex-1">
          <km-card icon="magic" :label="m.agents_agentPromptTemplates()" :description="m.agents_agentPromptTemplatesDesc()" :action-label="m.agents_reviewPromptTemplates()" @click="$emit(&quot;change-tab&quot;, &quot;prompts&quot;)" />
        </div>
      </div>
      <agents-create-new-topic v-if="showNewTopicDialog" :show-new-dialog="showNewTopicDialog" @cancel="showNewTopicDialog = false" />
    </div>
  </div>
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
