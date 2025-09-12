<template lang="pug">
.background-image.absolute-full.full-width(:style='{ backgroundImage: `url(${$appImagePath}${src})`, zIndex: 0 }', v-bind='$attrs')
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
