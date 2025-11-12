<template lang="pug">
q-radio(:model-value='row?.is_default', :val='true', @click.stop='onRadioClick')
</template>
<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: ['row', 'name'],

  methods: {
    onRadioClick() {
      this.$store.dispatch('modelConfig/setDefault', this.row)
    },
  },
})
</script>
