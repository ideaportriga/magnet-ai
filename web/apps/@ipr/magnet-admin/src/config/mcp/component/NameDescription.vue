<template>
  <div>
    <div class="km-title text-lef ellipsis">{{ row?.name }}</div>
    <div class="km-field text-left ellipsis description">{{ row?.description }}</div>
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
<style>
.description {
  white-space: normal;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}
</style>
