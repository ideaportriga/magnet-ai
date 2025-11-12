<template lang="pug">
.col
  .km-button-text.text-capitalize {{ row?.source }}
  km-chip.text-text-grey.text-capitalize.q-my-4(:label='sourceName', color='in-progress', size='sm')
  //.km-description.text-capitalize {{ row?.channel ?? "-" }}
</template>
<script>
export default {
  props: ['row', 'name'],
  computed: {
    sourceName() {
      return this.row?.consumer_name
    }
  }
}
</script>
