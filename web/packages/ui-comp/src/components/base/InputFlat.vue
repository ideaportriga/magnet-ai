<template lang="pug">
input.flat-input.ellipsis.rounded-borders.q-px-6(
  ref='input',
  contenteditable,
  :value='modelValue',
  @input='$emit("input", $event.target.value)',
  @change='$emit("change", $event.target.value)',
  @focus='focus',
  @blur='blur',
  :readonly='readonly',
  :disable='disabled',
  :placeholder='placeholder',
  :class='{ error: errorMessage != undefined }'
)
</template>

<script>
import { useValidation, validationProps } from '@shared'
import { toRefs } from 'vue'

export default {
  props: {
    modelValue: String,
    type: {
      type: String,
      default: 'text',
    },
    placeholder: String,
    disabled: {
      type: Boolean,
      default: false,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
    // TBD
    autogrow: {
      type: Boolean,
      default: false,
    },
    maxLength: {
      type: String,
      default: '',
    },
    autofocus: {
      default: false,
      type: Boolean,
    },
    ...validationProps(),
  },
  emits: ['change', 'blur', 'clear', 'input', 'focus'],
  setup(props) {
    const { modelValue, rules } = toRefs(props)
    return {
      ...useValidation(modelValue, rules),
    }
  },
  computed: {},
  methods: {
    blur() {
      this.$emit('blur')
    },
    focus() {
      this.$emit('focus')
      this.resetValidation()
    },
  },
}
</script>

<style lang="stylus" scoped>
.flat-input {
  border: none;
  outline: none;
  background: var(--q-light-bg)

  &.error {
    background: var(--q-error-bg);
  }

  transition: 0.3s cubic-bezier(0.25, 0.8, 0.5, 1);

  &:focus {
    background: var(--q-control-active-bg);
  }

  &:hover:not(:focus) {
    background: var(--q-control-active-bg);
  }
}
</style>
