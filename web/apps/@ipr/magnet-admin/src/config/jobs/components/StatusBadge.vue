<template lang="pug">
km-chip(:label='label', :color='color', :class='`text-${textColor}`', rounded)
</template>

<script>
export default {
  props: {
    row: {
      type: Object,
      default: () => ({}),
    },
  },
  computed: {
    label() {
      if (!this.row.status) return '-'
      return this.row.status.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
    },
    color() {
      if (this.row.status === 'error') return 'error-bg'
      if (this.row.status === 'completed') return 'like-bg'
      return 'in-progress'
    },
    textColor() {
      if (this.row.status === 'error') return 'error-text'
      if (this.row.status === 'completed') return 'like-text'
      return 'text-grey'
    },
  },
}
</script>
