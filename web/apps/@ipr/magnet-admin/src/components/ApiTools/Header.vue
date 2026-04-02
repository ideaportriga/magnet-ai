<template lang="pug">
.col-auto.q-py-auto
  .km-body {{ selectedTool?.name }}
</template>

<script>
import { useEntityDetail } from '@/composables/useEntityDetail'

export default {
  setup() {
    const { draft } = useEntityDetail('api_tools')
    return { draft }
  },
  computed: {
    selectedTool() {
      return this.draft
    },
  },
}
</script>
