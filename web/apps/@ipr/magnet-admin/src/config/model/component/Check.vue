<template>
  <km-glyph v-if="row?.[name]" name="check" />
</template>
<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: ['row', 'name'],
})
</script>
