<template lang="pug">
.km-title.text-lef.ellipsis {{ row?.name }}
.km-field.text-left.ellipsis.description {{ row?.description }}
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
<style lang="stylus">
.description
    white-space: normal
    overflow: hidden
    text-overflow: ellipsis
    display: -webkit-box
    -webkit-line-clamp: 3
    -webkit-box-orient: vertical
</style>
