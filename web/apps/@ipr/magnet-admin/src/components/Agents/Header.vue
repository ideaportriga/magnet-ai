<template>
  <div class="flex-1 min-w-0 py-auto">
    <KmBreadcrumbNav :items="crumbs" />
  </div>
</template>

<script>
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import { m } from '@/paraglide/messages'
import KmBreadcrumbNav from '@ds/components/domain/KmBreadcrumbNav.vue'

export default {
  components: { KmBreadcrumbNav },
  props: ['activeRow'],
  setup() {
    useAgentEntityDetail()
    const { options: items } = useCatalogOptions('agents')

    return {
      m,
      items,
    }
  },
  computed: {
    activeRowId() {
      return this.$route.params.id
    },
    activeTopicId() {
      return this.$route.params?.topicId || ''
    },
    activeActionId() {
      return this.$route.params?.actionId || ''
    },
    activeAgent() {
      return this.items.find((item) => item.id == this.activeRowId)
    },
    activeTopic: {
      get() {
        return this.activeAgent?.variants
          ?.find((el) => this.activeAgent.active_variant === el?.variant)
          ?.value?.topics?.find((el) => el.system_name == this.activeTopicId)
      },
    },
    activeAction() {
      return this.activeTopic?.actions?.find((el) => el.system_name == this.activeActionId)
    },
    activeRowDB() {
      return this.activeAgent
    },
    activeRowName: {
      get() {
        return this.activeRowDB?.name
      },
      set(val) {
        this.openDetails(val.value)
      },
    },
    crumbs() {
      const trail = [{ label: this.activeRowName ?? '', to: this.activeRowId ? `/agents/${this.activeRowId}` : undefined }]
      if (this.activeTopicId) {
        trail.push({
          label: this.activeTopic?.name || m.entity_topic(),
          to: `/agents/${this.activeRowId}/topics/${this.activeTopicId}`,
        })
      }
      if (this.activeActionId) {
        trail.push({ label: this.activeAction?.name || m.entity_action() })
      }
      return trail
    },
  },
}
</script>
