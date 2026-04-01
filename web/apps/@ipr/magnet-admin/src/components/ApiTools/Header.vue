<template lang="pug">
.col-auto.q-py-auto
  .km-body {{ selectedTool?.name }}
</template>

<script>
import { useApiToolDetailStore } from '@/stores/entityDetailStores'

export default {
  setup() {
    const apiToolStore = useApiToolDetailStore()
    return { apiToolStore }
  },
  computed: {
    selectedTool() {
      return this.apiToolStore.entity
    },
  },
}
</script>
