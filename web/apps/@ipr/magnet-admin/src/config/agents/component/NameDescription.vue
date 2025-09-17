<template lang="pug">
.km-title.text-lef.ellipsis {{ row?.name }}
.km-field.text-left.ellipsis.description-1 {{ row?.description }}
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

<style lang="stylus" scoped>
.description-1
  white-space: normal
  overflow: hidden
  text-overflow: ellipsis
  text-wrap: auto !important
  display: -webkit-box
  -webkit-line-clamp: 1
  -webkit-box-orient: vertical
</style>
