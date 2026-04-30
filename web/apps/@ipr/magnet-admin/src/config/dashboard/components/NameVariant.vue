<template>
  <div class="flex-1">
    <div class="km-button-text">{{ row?.name }}</div>
    <km-chip class="text-text-grey text-capitalize my-xs" :label="variant" tone="neutral" size="sm" />
  </div>
</template>
<script>
export default {
  props: ['row', 'name'],
  computed: {
    variant() {
      if (!this.row?.variant) return 'N/A'
      return this.row.variant.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
    },
  },
}
</script>
