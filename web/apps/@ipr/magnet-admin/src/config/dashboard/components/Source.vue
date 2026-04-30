<template>
  <div class="flex-1">
    <div class="km-button-text text-capitalize">{{ row?.source }}</div>
    <km-chip class="text-text-grey text-capitalize my-xs" :label="sourceName" tone="neutral" size="sm" />
    <!--.km-description.text-capitalize {{ row?.channel ?? "-" }}-->
  </div>
</template>
<script>
export default {
  props: ['row', 'name'],
  computed: {
    sourceName() {
      return this.row?.consumer_name
    },
  },
}
</script>
