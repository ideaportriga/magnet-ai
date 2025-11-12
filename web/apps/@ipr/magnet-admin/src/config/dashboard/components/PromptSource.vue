<template lang="pug">
.column
  .row.items-center.q-gap-8(v-if='prompt')
    .km-paragraph {{ prompt.display_name }}
    km-chip.text-secondary-text(:label='variant', color='in-progress', round)
  .row.items-center.q-gap-8(v-else)
    .km-paragraph -
</template>
<script>
export default {
  props: ['row', 'name'],
  computed: {
    prompt() {
      return this.row.prompt_template
    },
    variant() {
      if (!this.prompt) return ''
      return this.prompt.variant?.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
    },
  },
}
</script>
