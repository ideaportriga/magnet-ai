<template>
  <div v-show="showPreview">
    <agents-drawer-preview />
  </div>
  <div v-if="showTopic">
    <agents-drawer-topic />
  </div>
  <div v-if="showAction">
    <agents-drawer-action />
  </div>
</template>
<script>
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
export default {
  setup() {
    const { activeTopic } = useAgentEntityDetail()
    return { activeTopic }
  },
  computed: {
    routeName() {
      return this.$route.name
    },
    showPreview() {
      // if route name AgentDetail and activeTopic?.topic is empty
      // if route name AgentTopicDetail and activeTopic?.action is empty
      return (this.routeName === 'AgentDetail' && !this.activeTopic?.topic) || (this.routeName === 'AgentTopicDetail' && !this.activeTopic?.action)
    },
    showTopic() {
      return this.routeName === 'AgentDetail' && this.activeTopic?.topic
    },
    showAction() {
      return this.routeName === 'AgentTopicDetail' && this.activeTopic?.action
    },
  },
}
</script>

<style scoped></style>
