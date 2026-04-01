<template lang="pug">
.col-auto.q-py-auto
  .km-body {{ activeRetrievalName }}
</template>

<script>
import { computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'

export default {
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
      return this.items.find((item) => item.id == this.activeRetrievalId)?.name
    },
  },
}
</script>
