<template lang="pug">
.col-auto.q-py-auto
  .km-body {{ activeRagName }}
</template>

<script>
import { computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'

export default {
  setup() {
    const queries = useEntityQueries()
    const { data: listData } = queries.rag_tools.useList()
    const items = computed(() => listData.value?.items ?? [])
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
