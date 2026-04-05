<template lang="pug">
q-btn-dropdown.km-export-dropdown(flat, color='secondary-text', :label='m.common_export()', no-caps, icon='fas fa-file-export')
  q-list
    q-item(clickable, v-close-popup, @click='$emit("exportToCsv")')
      q-item-section
        q-item-label Export as CSV
    q-item(clickable, v-close-popup, @click='$emit("exportToJson")')
      q-item-section
        q-item-label Export as JSON
</template>
<script>
import { m } from '@/paraglide/messages'
export default {
  emits: ['exportToCsv', 'exportToJson'],
  setup() {
    return { m }
  },
}
</script>
<style lang="stylus">
.km-export-dropdown .fa-file-export {
  font-size: var(--km-font-size-body-lg) !important
  color: var(--q-btn-flat-icon)
}
</style>
