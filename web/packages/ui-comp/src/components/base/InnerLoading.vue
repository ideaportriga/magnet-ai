<template lang="pug">
q-inner-loading(:showing='showing')
  q-spinner(color='primary', size='6em', :thickness='3')
</template>

<script>
export default {
  props: {
    showing: {
      type: Boolean,
      default: true,
    },
  },
}
</script>

<style scoped>
.km-loading-content {
  color: white;
  text-align: center;
}
</style>
