<template>
  <div class="flex-1 min-w-0 py-auto">
    <KmBreadcrumbNav :items="crumbs" />
  </div>
</template>

<script>
import { useDeepResearchStore } from '@/stores/deepResearchStore'
import KmBreadcrumbNav from '@ds/components/domain/KmBreadcrumbNav.vue'

export default {
  components: { KmBreadcrumbNav },
  setup() {
    const drStore = useDeepResearchStore()
    return { drStore }
  },
  computed: {
    activeRowId() {
      return this.$route.params.id
    },
    activeRowDB() {
      return this.drStore.configs?.find((item) => item.id == this.activeRowId)
    },
    activeRowName() {
      return this.activeRowDB?.name ?? ''
    },
    crumbs() {
      return [{ label: this.activeRowName }]
    },
  },
}
</script>
