<template lang="pug">
.km-title.text-lef.ellipsis {{ row?.name }}
.km-field.text-left.ellipsis {{ row?.description }}
.km-field.text-left.ellipsis {{ row?.system_name }}
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: ['row'],

  setup() {
    return {}
  },
})
</script>
