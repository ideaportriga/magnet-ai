<template lang="pug">
.km-title.text-lef.ellipsis {{ row?.name }}
.km-field.text-left.ellipsis {{ row?.description }}
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    row: {
      type: Object,
      required: true,
    },
  },
})
</script>

<style scoped>
.km-title,
.km-field {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
