<template lang="pug">
.km-title.text-lef.ellipsis {{ row?.name }}
.km-field.text-left.ellipsis {{ row?.description }}
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
