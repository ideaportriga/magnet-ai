<template lang="pug">
.km-drawer-resize-handle(@mousedown="$emit('mousedown', $event)")
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'KmDrawerResizeHandle',
  emits: ['mousedown'],
})
</script>
