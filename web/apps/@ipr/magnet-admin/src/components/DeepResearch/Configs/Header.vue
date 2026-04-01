<template lang="pug">
.col-auto.q-py-auto
  .km-body {{ activeRowName }}
</template>

<script>
import { useDeepResearchStore } from '@/stores/deepResearchStore'

export default {
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
      return this.activeRowDB?.name
    },
  },
}
</script>
