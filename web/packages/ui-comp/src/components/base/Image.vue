<template lang="pug">
img(:src='`${$appImagePath}${src}`', v-bind='$attrs')
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    src: {
      type: String,
      required: true,
    },
  },
})
</script>
