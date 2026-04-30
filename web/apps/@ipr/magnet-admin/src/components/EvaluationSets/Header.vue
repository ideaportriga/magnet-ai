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
    const { data: listData } = queries.evaluation_sets.useList()
    const items = computed(() => listData.value?.items ?? [])
    return { items }
  },
  computed: {
    activeRowId() {
      return this.$route.params.id
    },
    activeRowName() {
      return this.items.find((item) => item.id == this.activeRowId)?.name ?? ''
    },
    crumbs() {
      return [{ label: this.activeRowName }]
    },
  },
}
</script>
