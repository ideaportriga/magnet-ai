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

<script setup lang="ts">
import { ref } from 'vue'
import { copyToClipboard } from 'quasar'
import { notify } from '@shared/utils/notify'

const props = withDefaults(defineProps<{
  row?: Record<string, unknown>
  label?: string
}>(), {
  row: () => ({}),
  label: 'Copy',
})

const hover = ref(false)

function copy() {
  copyToClipboard(String(props.row.system_name || props.label || ''))
  notify.copied()
}
</script>

<style lang="stylus" scoped>
.km-cell-button
  transform: translateX(-32px)
  transition: .3s ease
  &:hover
    transform: translateX(0)
</style>
