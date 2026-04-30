<script setup lang="ts">
/**
 * NativeSelect — thin wrapper around the native `<select>` element with a
 * trailing chevron. Use this when you need the platform-native dropdown
 * (mobile pickers, accessibility constraints) instead of the custom
 * `DsSelect`.
 *
 *   <DsNativeSelect v-model="role">
 *     <option value="admin">Admin</option>
 *     <option value="member">Member</option>
 *   </DsNativeSelect>
 */

import { reactiveOmit, useVModel } from '@vueuse/core'
import type { AcceptableValue } from 'reka-ui'

defineOptions({ inheritAttrs: false })

const props = defineProps<{
  modelValue?: AcceptableValue | AcceptableValue[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: AcceptableValue]
}>()

const modelValue = useVModel(props, 'modelValue', emit, {
  passive: true,
  defaultValue: '',
})

const delegatedProps = reactiveOmit(props, 'modelValue')
</script>

<template>
  <div class="ds-native-select" data-test="ds-native-select">
    <select
      v-bind="{ ...$attrs, ...delegatedProps }"
      v-model="modelValue"
      class="ds-native-select__control"
      data-test="ds-native-select-control"
    >
      <slot />
    </select>
    <svg
      class="ds-native-select__icon"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M6 9l6 6 6-6"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
  </div>
</template>

<style>
.ds-native-select {
  position: relative;
  display: inline-block;
  inline-size: fit-content;
}
.ds-native-select:has(.ds-native-select__control:disabled) {
  opacity: 0.5;
}

.ds-native-select__control {
  appearance: none;
  inline-size: 100%;
  min-inline-size: 0;
  block-size: 36px;
  padding-inline: var(--ds-space-md);
  padding-inline-end: calc(var(--ds-space-md) + 20px);
  background: var(--ds-color-control-bg);
  color: var(--ds-color-black);
  border: 1px solid var(--ds-color-control-border);
  border-radius: var(--ds-radius-md);
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  outline: none;
  box-shadow: var(--ds-shadow-sm);
  transition:
    border-color var(--ds-duration-fast) var(--ds-ease-out),
    box-shadow var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-native-select__control::placeholder {
  color: var(--ds-color-placeholder);
}
.ds-native-select__control:hover:not(:disabled, [aria-invalid='true']) {
  border-color: var(--ds-color-control-hover-border);
}
.ds-native-select__control:focus-visible {
  border-color: var(--ds-color-primary);
  box-shadow: 0 0 0 3px var(--ds-color-primary-transparent);
}
.ds-native-select__control:disabled {
  pointer-events: none;
  cursor: not-allowed;
}
.ds-native-select__control[aria-invalid='true'] {
  border-color: var(--ds-color-error);
}
.ds-native-select__control[aria-invalid='true']:focus-visible {
  box-shadow: 0 0 0 3px var(--ds-color-error-bg);
}

.ds-native-select__icon {
  position: absolute;
  inset-block-start: 50%;
  inset-inline-end: var(--ds-space-md);
  transform: translateY(-50%);
  pointer-events: none;
  user-select: none;
  color: var(--ds-color-text-grey);
  opacity: 0.6;
}
</style>
