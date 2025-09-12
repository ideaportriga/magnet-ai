<template lang="pug">
q-tooltip.km-tooltip(:delay='100', :offset='[0, 6]', anchor='top middle', self='bottom middle', transition-show='jump-up', dense, :class='[classes.bg]')
  .km-chip(:class='[classes.text]') {{ label }}
</template>
<script>
export default {
  props: {
    color: {
      type: String,
      default: 'tooltip-text',
    },
    background: {
      type: String,
      default: 'tooltip-bg',
    },
    label: {
      type: String,
      default: '',
    },
  },
  computed: {
    classes() {
      return {
        bg: `bg-${this.background}`,
        text: `text-${this.color}`,
      }
    },
  },
}
</script>
