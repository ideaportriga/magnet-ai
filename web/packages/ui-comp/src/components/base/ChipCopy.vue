<template lang="pug">
.row
  km-btn.col-auto.km-cell-button.ellipsis(
    style='max-width: 200px',
    @click.stop='copy',
    hoverColor='primary',
    labelClass='km-title',
    flat,
    iconSize='16px',
    hoverBg='primary-bg',
    icon='far fa-copy',
    :iconColor='hover ? "icon" : "btn-simple-bg"',
    :label='row.system_name || label',
    @mouseenter='hover = true',
    @mouseleave='hover = false',
    simple
  )
</template>

<script>
import { ref } from 'vue'
import { copyToClipboard } from 'quasar'
export default {
  props: {
    row: {
      type: Object,
      default: () => ({}),
    },
    label: {
      type: String,
      default: 'Copy',
    },
  },
  setup() {
    return {
      hover: ref(false),
    }
  },
  methods: {
    copy() {
      copyToClipboard(this.row.system_name || this.label || '')
      this.$q.notify({
        position: 'top',
        message: 'System name has been copied to clipboard',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
    },
  },
}
</script>

<style lang="stylus" scoped>
.km-cell-button
  transform: translateX(-32px)
  transition: .3s ease
  &:hover
    transform: translateX(0)
</style>
