<script setup lang="ts">
/**
 * `<km-input-flat>` — minimal contenteditable-like input used in inline-edit
 * cells. The legacy implementation is a `<input>` with no border/background;
 * this rebuild matches it 1:1 plus inline error message.
 */

import { ref, toRefs, useTemplateRef } from 'vue'
import useValidation from '@shared/composables/useValidation'

const props = withDefaults(
  defineProps<{
    modelValue?: string
    type?: string
    placeholder?: string
    disabled?: boolean
    readonly?: boolean
    autogrow?: boolean
    maxLength?: string | number
    autofocus?: boolean
    rules?: unknown
  }>(),
  {
    type: 'text',
    autogrow: false,
    autofocus: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
  input: [value: string]
  change: [value: string]
  focus: [event: FocusEvent]
  blur: [event: FocusEvent]
  clear: []
}>()

const { modelValue, rules } = toRefs(props)
const { errorMessage, validate, resetValidation } = useValidation(modelValue, rules)
const inputRef = useTemplateRef<HTMLInputElement>('input')
const focused = ref(false)

function onInput(event: Event) {
  const value = (event.target as HTMLInputElement).value
  // Emit update:modelValue on every keystroke so `:value="modelValue"` does
  // not snap back to the previous value mid-typing. Parents that only want
  // commit semantics keep listening to `@change`.
  emit('update:modelValue', value)
  emit('input', value)
}
function onChange(event: Event) {
  const value = (event.target as HTMLInputElement).value
  emit('change', value)
  emit('update:modelValue', value)
}
function onFocus(event: FocusEvent) {
  focused.value = true
  emit('focus', event)
}
function handleBlur(event: FocusEvent) {
  focused.value = false
  emit('blur', event)
}

defineExpose({ validate, resetValidation, focus: () => inputRef.value?.focus() })
</script>

<template>
  <span
    class="km-input-flat"
    :data-state="errorMessage ? 'error' : focused ? 'focused' : undefined"
  >
    <input
      ref="input"
      :type="type"
      :value="modelValue ?? ''"
      :placeholder="placeholder"
      :readonly="readonly"
      :disabled="disabled"
      :autofocus="autofocus"
      :maxlength="maxLength || undefined"
      class="km-input-flat__field"
      :title="(errorMessage as string) ?? ''"
      data-test="km-input-flat"
      @input="onInput"
      @change="onChange"
      @focus="onFocus"
      @blur="handleBlur"
    />
    <span v-if="errorMessage" class="km-input-flat__error">{{ errorMessage }}</span>
  </span>
</template>

<style>
.km-input-flat {
  display: inline-flex;
  flex-direction: column;
  gap: var(--ds-space-2xs);
  inline-size: 100%;
}

.km-input-flat__field {
  border: 0;
  background: transparent;
  font-size: var(--ds-font-size-body);
  color: var(--ds-color-black);
  padding: var(--ds-space-2xs) var(--ds-space-2xs);
  outline: none;
  border-radius: var(--ds-radius-sm);
  text-overflow: ellipsis;
}
.km-input-flat__field:focus-visible {
  background: var(--ds-color-light);
}
.km-input-flat[data-state='error'] .km-input-flat__field {
  background: var(--ds-color-error-bg);
  color: var(--ds-color-error);
}

.km-input-flat__error {
  font-size: var(--ds-font-size-xs);
  color: var(--ds-color-error-text);
}
</style>
