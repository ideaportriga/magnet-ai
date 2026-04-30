<template>
  <div>
    <div class="km-title text-lef ellipsis">{{ row?.name }}</div>
    <div class="km-field text-left ellipsis">{{ row?.description }}</div>
    <div class="km-field text-left ellipsis">{{ row?.system_name }}</div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: ['row'],

  setup() {
    return {}
  },
})
</script>
