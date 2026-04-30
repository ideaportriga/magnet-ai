<template>
  <div
    class="bg-light full-height stack"
    data-gap="0"
  >
    <div class="bg-light pt-xl justify-center flex text-secondary-text km-title">
      {{ displayText }}
    </div>
  </div>
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
