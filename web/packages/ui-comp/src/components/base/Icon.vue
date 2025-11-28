<template lang="pug">
svg.icon(:viewbox='`0 0 ${width} ${height}`', :width='width', :height='height', role='presentation')
  use(:href='`#icon-${name}`')
</template>
<!-- style=" border: 1px solid #C9CED2;" -->
<script>
export default {
  props: {
    name: {
      type: String,
      default: '',
    },
    width: {
      type: String,
      default: '24',
    },
    height: {
      type: String,
      default: '18',
    },
  },
  computed: {},
}
</script>
