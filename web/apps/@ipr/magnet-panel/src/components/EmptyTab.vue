<template lang="pug">
.bg-light.full-height.column.no-wrap
  .bg-light.q-pt-xl.justify-center.flex.text-secondary-text.km-title {{ text }}
</template>

<script>
export default {
  name: 'EmptyTab',
  props: {
    text: {
      type: String,
      default: 'There are no available tabs for this app',
    },
  },
}
</script>
