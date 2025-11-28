<template lang="pug">
.row
  .col-4(style='max-width: 300px')
    .km-heading-4.q-mb-sm {{ title }}
    .km-button-xs-text.text-secondary-text {{ subTitle }}
  .col.q-pl-lg
    slot
</template>

<script lnag="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  props: ['title', 'subTitle'],
  setup() {
    return {}
  },
  computed: {},
})
</script>
