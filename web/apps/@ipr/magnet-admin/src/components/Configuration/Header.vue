<template lang="pug">
.col-auto.q-py-auto
  .km-body {{ activeRagName }}
</template>

<script>
import { useCatalogOptions } from '@/queries/useCatalogOptions'

export default {
  setup() {
    const { options: items } = useCatalogOptions('rag_tools')
    return { items }
  },
  computed: {
    activeRagId() {
      return this.$route.params.id
    },
    activeRagName() {
      return this.items.find((item) => item.id == this.activeRagId)?.name
    },
  },
}
</script>
