<template lang="pug">
.col-auto.q-py-auto.row.items-center.no-wrap.q-gap-8
  template(v-if='activeTabName')
    .km-body.text-primary.km-breadcrumb-link(@click='navigateToApp') {{ activeRagName }}
    q-icon.text-secondary-text.km-breadcrumb-sep(name='chevron_right', size='18px')
    .km-body {{ activeTabName }}
  template(v-else)
    .km-body {{ activeRagName }}
</template>

<script>
import { computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { useAiAppDetailStore } from '@/stores/entityDetailStores'

export default {
  setup() {
    const queries = useEntityQueries()
    const aiAppStore = useAiAppDetailStore()
    const { data: listData } = queries.ai_apps.useList()
    const items = computed(() => listData.value?.items ?? [])
    return { items, aiAppStore }
  },
  computed: {
    activeRagId() {
      return this.$route.params.id
    },
    activeAIAppDB() {
      return this.items.find((item) => item.id == this.activeRagId)
    },
    activeRagName() {
      return this.activeAIAppDB?.name
    },
    activeTabName() {
      if (!this.$route.params?.tab) return ''
      const tab = this.aiAppStore.entity?.tabs?.find((t) => t.system_name === this.$route.params.tab)
      return tab?.name || this.$route.params.tab
    },
  },
  methods: {
    navigateToApp() {
      if (this.activeRagId) this.$router?.push(`/ai-apps/${this.activeRagId}`)
    },
  },
}
</script>
