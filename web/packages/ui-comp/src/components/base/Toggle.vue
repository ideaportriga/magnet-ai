<template lang="pug">
span
  q-toggle(
    :model-value='modelValue',
    @update:modelValue='$emit("update:modelValue", $event)',
    :color='color',
    :size='size',
    :disable='disable',
    v-bind='$attrs'
  )
  template(v-if='errorMessage')
    .km-small-chip.q-pa-4.q-mt-2.text-error-text.no-wrap {{ errorMessage }}
</template>

<script>
import { toRefs } from 'vue'
import { useValidation, validationProps } from '@shared'

export default {
  props: {
    modelValue: {
      type: Boolean,
      default: false,
    },
    color: {
      type: String,
      default: 'primary',
    },
    size: {
      type: String,
      default: 'sm',
    },
    disable: {
      type: Boolean,
      default: false,
    },
    ...validationProps(),
  },
  emits: ['update:modelValue'],
  setup(props) {
    const { modelValue, rules } = toRefs(props)
    return {
      ...useValidation(modelValue, rules),
    }
  },
}
</script>
