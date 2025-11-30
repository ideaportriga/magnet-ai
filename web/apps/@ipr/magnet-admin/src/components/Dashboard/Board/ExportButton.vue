<template lang="pug">
q-btn-dropdown.km-export-dropdown(flat, color='secondary-text', label='Export', no-caps, icon='fas fa-file-export')
  q-list
    q-item(clickable, v-close-popup, @click='$emit("exportToCsv")')
      q-item-section
        q-item-label Export as CSV
    q-item(clickable, v-close-popup, @click='$emit("exportToJson")')
      q-item-section
        q-item-label Export as JSON
</template>
<script>
export default {
  emits: ['exportToCsv', 'exportToJson'],
}
</script>
<style lang="stylus">
.km-export-dropdown .fa-file-export {
  font-size: 16px !important
  color: var(--q-btn-flat-icon)
}
</style>
