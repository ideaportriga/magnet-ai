<template lang="pug">
span
  q-input.km-control.km-input.rounded-borders(
    ref='input',
    outlined,
    dense,
    :model-value='modelValue',
    @change='$emit("update:modelValue", $event)',
    @update:modelValue='$emit("input", $event)',
    @focus='onFocus',
    @blur='$emit("blur", $event)',
    :type='type',
    :rows='rows',
    :autofocus='autofocus',
    :placeholder='placeholder',
    :clearable='clearable',
    clear-icon='close',
    :readonly='readonly',
    :autogrow='autogrow',
    :disable='disabled',
    :class='{ "km-error-input": !!errorMessage }',
    @clear='$emit("update:modelValue", "")',
    @keydown='handleKeydown',
    :hide-bottom-space='hideBottomSpace',
    :suffix='suffix',
    :prefix='prefix'
  )
    template(v-slot:append)
      slot(name='append', :height='height')
      template(v-if='!!customClearAction && modelValue')
        q-icon.close-icon(name='close', @click='customClearAction', color='icon', size='24px')
    template(v-if='iconBefore', v-slot:prepend)
      template(v-if='iconBefore.startsWith("--theme")')
        km-icon.text-icon(:name='iconBefore.replace("--theme-", "")', @click='beforeIconAction', width='18px', height='18px')
      template(v-else)
        q-icon(:name='iconBefore', @click='beforeIconAction', color='icon')
  slot(name='menu')
  template(v-if='!!errorMessage')
    .km-small-chip.q-pa-4.q-pl-8.text-error-text {{ errorMessage }}
</template>

<script>
import { ref, toRefs } from 'vue'
import { useValidation, validationProps } from '@shared'

export default {
  props: {
    customClearAction: {
      default: false,
    },
    beforeIconAction: {
      default: () => {},
    },
    label: String,
    modelValue: String,
    iconBefore: String,
    type: {
      type: String,
      default: 'text',
    },
    borderRadius: {
      type: String,
      default: '4px',
    },
    rows: {
      default: 1,
    },
    placeholder: String,
    grayBg: Boolean,
    disabled: Boolean,
    required: Boolean,
    readonly: {
      type: Boolean,
      default: false,
    },
    autogrow: {
      type: Boolean,
      default: false,
    },
    maxLength: {
      type: String,
      default: '',
    },
    clearable: Boolean,
    showCount: {
      type: Boolean,
      default: false,
    },
    autofocus: {
      default: false,
      type: Boolean,
    },
    beforeIcon: {
      default: '',
    },
    height: {
      default: 'var(--input-height-default)',
    },
    maxHeight: {
      default: 'unset',
    },
    minHeight: {
      default: 'unsed',
    },
    hideBottomSpace: {
      type: Boolean,
      default: false,
    },
    suffix: {
      type: String,
    },
    prefix: {
      type: String,
    },
    ...validationProps(),
  },
  emits: ['update:modelValue', 'blur', 'clear', 'input', 'focus', 'enter'],
  setup(props) {
    const { modelValue, rules } = toRefs(props)
    return {
      input: ref(null),
      ...useValidation(modelValue, rules),
    }
  },
  computed: {
    check() {
      return !!this.customClear
    },
    fieldSize() {
      return this.autogrow || this.type === 'textarea' ? 'auto' : this.height
    },
  },
  methods: {
    handleKeydown(event) {
      if (event.key === 'Escape') {
        this.$emit('update:modelValue', '')
      }

      if (event.key === 'Enter' && !event.shiftKey && this.type !== 'textarea') {
        this.blur()
        this.$emit('enter', event)
        this.focus()
      }
    },
    onFocus($event) {
      this.$emit('focus', $event)
    },
    blur() {
      this.$refs?.input?.blur()
    },

    focus() {
      this.$refs?.input?.focus()
    },

    getCursorIndex() {
      return this.input?.nativeEl?.selectionEnd
    },
  },
}
</script>

<style lang="stylus" scoped>
.close-icon
  opacity: 0.5;

  &:hover
    opacity: 1;

.km-control
  --field-height: v-bind(fieldSize) !important
  --field-initial-height: v-bind(height) !important
  --field--border-radius: v-bind(borderRadius) !important
  --field-min-height: v-bind(minHeight)
  --field-max-height: v-bind(maxHeight)
.km-error-select
  border-color: var(--q-error-text) !important
</style>
