<template lang="pug">
q-tabs.bb-border.full-width(
  v-bind="$attrs"
  narrow-indicator dense align="left"
  active-color="primary" indicator-color="primary"
  active-bg-color="white" no-caps
  content-class="km-tabs"
)
  slot
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'KmTabs',
  inheritAttrs: false,
})
</script>
