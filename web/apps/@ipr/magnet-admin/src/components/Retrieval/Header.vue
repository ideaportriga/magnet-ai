<template>
  <div class="flex-1 min-w-0 py-auto">
    <KmBreadcrumbNav :items="crumbs" />
  </div>
</template>

<script>
import { computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import KmBreadcrumbNav from '@ds/components/domain/KmBreadcrumbNav.vue'

export default {
  components: { KmBreadcrumbNav },
  setup() {
    const queries = useEntityQueries()
    const { data: listData } = queries.retrieval.useList()
    const items = computed(() => listData.value?.items ?? [])
    return { items }
  },
  computed: {
    activeRetrievalId() {
      return this.$route.params.id
    },
    activeRetrievalName() {
      return this.items.find((item) => item.id == this.activeRetrievalId)?.name ?? ''
    },
    crumbs() {
      return [{ label: this.activeRetrievalName }]
    },
  },
}
</script>
