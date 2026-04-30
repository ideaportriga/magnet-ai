<script setup lang="ts">
/**
 * Input — text input. Replaces shadcn `<Input>` and Quasar `<q-input>` for
 * the simple single-line case. Visual states are driven by `aria-invalid`
 * and `[disabled]`; pair with a `<DsLabel>` for accessibility.
 *
 *   <DsLabel for="email">Email</DsLabel>
 *   <DsInput id="email" v-model="email" type="email" />
 */

import { useVModel } from '@vueuse/core'
import type { InputHTMLAttributes } from 'vue'

const props = defineProps<{
  modelValue?: string | number
  defaultValue?: string | number
  type?: InputHTMLAttributes['type']
  size?: 'sm' | 'md' | 'lg'
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
}>()

const model = useVModel(props, 'modelValue', emit, {
  passive: true,
  defaultValue: props.defaultValue,
})

import { useTemplateRef } from 'vue'

const inputEl = useTemplateRef<HTMLInputElement>('inputEl')

defineExpose({
  focus: (options?: FocusOptions) => inputEl.value?.focus(options),
  blur: () => inputEl.value?.blur(),
  select: () => inputEl.value?.select(),
  /** The native <input> element. */
  el: inputEl,
})
</script>

<template>
  <input
    ref="inputEl"
    v-model="model"
    class="ds-input"
    :type="type ?? 'text'"
    :data-size="size ?? 'md'"
    data-test="ds-input"
  >
</template>

<style>
.ds-input {
  display: block;
  inline-size: 100%;
  min-inline-size: 0;
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-body);
  line-height: var(--ds-line-height-tight);
  color: var(--ds-color-black);
  background: var(--ds-color-control-bg);
  border: 1px solid var(--ds-color-control-border);
  border-radius: var(--ds-radius-md);
  padding-inline: var(--ds-space-md);
  outline: none;
  transition:
    border-color var(--ds-duration-fast) var(--ds-ease-out),
    box-shadow var(--ds-duration-fast) var(--ds-ease-out);
}

.ds-input::placeholder { color: var(--ds-color-placeholder-fg); }

.ds-input:hover:not(:disabled, [aria-invalid='true'], [readonly]) {
  border-color: var(--ds-color-control-hover-border);
}

.ds-input:focus-visible {
  border-color: var(--ds-color-focus-border);
  box-shadow: 0 0 0 3px var(--ds-color-focus-ring);
}

.ds-input[aria-invalid='true'] {
  border-color: var(--ds-color-invalid-border);
}
.ds-input[aria-invalid='true']:focus-visible {
  box-shadow: 0 0 0 3px var(--ds-color-invalid-ring);
}

.ds-input[readonly] {
  background: var(--ds-color-readonly-bg);
  color: var(--ds-color-readonly-fg);
  border-color: var(--ds-color-readonly-border);
  cursor: default;
}

.ds-input:disabled {
  background: var(--ds-color-disabled-bg);
  color: var(--ds-color-disabled-fg);
  border-color: var(--ds-color-disabled-border);
  cursor: not-allowed;
}

.ds-input[data-size='sm'] {
  block-size: 32px;
  font-size: var(--ds-font-size-label);
  padding-inline: var(--ds-space-sm);
}
.ds-input[data-size='md'] { block-size: 36px; }
.ds-input[data-size='lg'] {
  block-size: 40px;
  font-size: var(--ds-font-size-body-lg);
}

/* file input affordances */
.ds-input[type='file'] {
  padding: var(--ds-space-xs) var(--ds-space-md);
}
.ds-input[type='file']::file-selector-button {
  margin-inline-end: var(--ds-space-md);
  padding: var(--ds-space-2xs) var(--ds-space-sm);
  font: inherit;
  border: 0;
  background: transparent;
  color: var(--ds-color-black);
  cursor: pointer;
}
</style>
