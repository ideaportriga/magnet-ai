<template>
  <div class="flex-1 min-w-0 py-auto">
    <KmBreadcrumbNav :items="crumbs" />
  </div>
</template>

<script>
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import KmBreadcrumbNav from '@ds/components/domain/KmBreadcrumbNav.vue'

export default {
  components: { KmBreadcrumbNav },
  setup() {
    const { options: items } = useCatalogOptions('rag_tools')
    return { items }
  },
  computed: {
    activeRagId() {
      return this.$route.params.id
    },
    activeRagName() {
      return this.items.find((item) => item.id == this.activeRagId)?.name ?? ''
    },
    crumbs() {
      return [{ label: this.activeRagName }]
    },
  },
}
</script>
