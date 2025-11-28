<template lang="pug">
q-slider(
  :model-value='modelValue',
  @update:modelValue='$emit("update:modelValue", $event)',
  :min='min',
  :max='max',
  :step='step',
  inner-track-color='border',
  selection-color='control-hover-border',
  thumb-color='white',
  track-size='10px',
  thumb-size='22px',
  dense
)
</template>
<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    modelValue: {},
    min: {
      default: 0,
    },
    max: {
      default: 1,
    },
    step: {
      default: 0.01,
    },
  },
  emits: ['update:modelValue'],
})
</script>
