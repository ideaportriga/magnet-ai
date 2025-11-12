<template lang="pug">
.col
  .km-button-text {{ row?.name }}
  km-chip.text-text-grey.text-capitalize.q-my-4(:label='variant', color='in-progress', size='sm')
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
