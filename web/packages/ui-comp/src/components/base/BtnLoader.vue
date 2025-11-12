<template lang="pug">
km-btn.km-btn-loader(flat, @click='$emit("click", $event)')
  template(v-if='loading')
    q-spinner.text-primary(size='14px')
  template(v-else)
    q-icon.col-auto.km-btn-loader-icon(name='fas fa-sync', size='14px')
  .col.text-left.ellipsis.km-button-text.q-pl-sm {{ title }}
</template>
<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    loading: {
      type: Boolean,
      required: true,
    },
    title: {
      type: String,
      required: true,
    },
  },
  emits: ['click'],
})
</script>
<style lang="stylus" scoped>
.km-btn-loader:hover
    .km-btn-loader-icon
        color: var(--q-btn-flat-hover-icon) !important
</style>
