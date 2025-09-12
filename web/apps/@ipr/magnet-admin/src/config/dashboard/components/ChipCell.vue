<template lang="pug">
km-chip.q-my-4(v-if='label', :label='label', :color='color', round, :class='textColor')
</template>
<script>
export default {
  props: {
    row: {
      type: Object,
      required: true,
    },
    name: {
      type: String,
      required: true,
    },
    color: {
      type: String,
      default: 'in-progress',
    },
    textColor: {
      type: String,
      default: 'text-text-grey',
    },
  },
  computed: {
    label() {
      const keys = this.name.split('.')
      let value = this.row
      for (const key of keys) {
        if (!value) return ''
        value = value[key]
      }
      return value
    },
  },
}
</script>
