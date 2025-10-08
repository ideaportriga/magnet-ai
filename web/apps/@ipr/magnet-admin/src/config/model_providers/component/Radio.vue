<template lang="pug">
q-radio(:model-value='row?.is_default', :val='true', @click.stop='showDialog = true') 

km-popup-confirm(
  :visible='showDialog',
  confirmButtonLabel='OK, change default',
  notificationIcon='fas fa-circle-info',
  cancelButtonLabel='Cancel',
  @cancel='showDialog = false',
  @confirm='onRadioClick'
)
  .row.item-center.justify-center.km-heading-7 You are about to change default model
  .row.text-center.justify-center This will affect newly created Prompt Templates and any existing
  .row.text-center.justify-center Prompt Templates that have no model selected.
</template>
<script>
import { defineComponent, ref } from 'vue'

export default defineComponent({
  props: ['row', 'name'],
  data() {
    return {
      showDialog: ref(false),
    }
  },

  methods: {
    onRadioClick() {
      this.$store.dispatch('modelConfig/setDefault', this.row)
      this.showDialog = false
    },
  },
})
</script>
