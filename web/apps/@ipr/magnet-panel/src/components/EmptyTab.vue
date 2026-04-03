<template lang="pug">
.bg-light.full-height.column.no-wrap
  .bg-light.q-pt-xl.justify-center.flex.text-secondary-text.km-title {{ displayText }}
</template>

<script>
import { m } from '@/paraglide/messages'

export default {
  name: 'EmptyTab',
  props: {
    text: {
      type: String,
      default: undefined,
    },
  },
  computed: {
    displayText() {
      return this.text ?? m.panel_noAvailableTabs()
    },
  },
}
</script>
