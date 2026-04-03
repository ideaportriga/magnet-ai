<template lang="pug">
.col-auto.q-py-auto
  .km-body {{ activeRowName }}
</template>

<script>
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'

export default {
  setup() {
    const queries = useEntityQueries()
    const { data: listData } = queries.collections.useList()
    const items = computed(() => listData.value?.items ?? [])
    return { items }
  },
  computed: {
    activeRowId() {
      return this.$route.params.id
    },
    activeRowName() {
      return this.items.find((item) => item.id == this.activeRowId)?.name
    },
  },
}
</script>
