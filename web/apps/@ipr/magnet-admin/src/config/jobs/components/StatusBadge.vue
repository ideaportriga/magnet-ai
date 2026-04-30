<template>
  <km-chip :label="label" :tone="tone" rounded />
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
    tone() {
      if (this.row.status === 'error') return 'danger'
      if (this.row.status === 'completed') return 'success'
      return 'neutral'
    },
  },
}
</script>
