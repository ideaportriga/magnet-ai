<template>
  <div>
    <div class="km-title text-lef ellipsis">{{ row?.name }}</div>
    <div class="km-field text-left ellipsis description-1">{{ row?.description }}</div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: ['row', 'name'],

  setup() {
    return {}
  },
})
</script>

<style scoped>
.description-1 {
  white-space: normal;
  overflow: hidden;
  text-overflow: ellipsis;
  text-wrap: auto !important;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}
</style>
