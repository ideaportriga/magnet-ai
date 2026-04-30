<template>
  <div>
    <div class="km-title text-lef ellipsis">{{ row?.name }}</div>
    <div class="km-field text-left ellipsis">{{ row?.description }}</div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    row: {
      type: Object,
      required: true,
    },
    name: String,
  },
})
</script>

<style scoped>
.km-title,
.km-field {
  max-inline-size: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
