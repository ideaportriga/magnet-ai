<template lang="pug">
.km-label-value(v-bind='$attrs')
  .row.items-center.q-gap-4.q-pb-4
    .km-title {{ value }}
    .km-description.text-text-weak {{ label }}
    q-icon.col-auto(name='o_info', color='secondary', v-if='tooltip')
      q-tooltip.bg-white.block-shadow.km-description(self='top middle', :offset='[-50, -50]')
        .text-secondary-text {{ tooltip }}
</template>
<script>
export default {
  props: {
    label: {
      type: String,
    },
    value: {
      type: String,
    },
    tooltip: {
      type: String,
    },
  },
}
</script>
