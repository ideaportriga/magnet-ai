<script setup lang="ts">
/**
 * ComboboxInput — search field driving the Combobox filter. Wrapped with an
 * inline magnifying-glass icon and a divider, mirroring CommandInput.
 */
import type { ComboboxInputEmits, ComboboxInputProps } from 'reka-ui'
import { ComboboxInput, useForwardPropsEmits } from 'reka-ui'

defineOptions({ inheritAttrs: false })

const props = defineProps<ComboboxInputProps>()
const emits = defineEmits<ComboboxInputEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <div class="ds-combobox__input-wrapper" data-test="ds-combobox-input-wrapper">
    <svg
      class="ds-combobox__input-icon"
      width="16"
      height="16"
      viewBox="0 0 16 16"
      aria-hidden="true"
    >
      <circle
        cx="7"
        cy="7"
        r="4.25"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
      />
      <path
        d="M10.5 10.5 L13.5 13.5"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
      />
    </svg>
    <ComboboxInput
      v-bind="{ ...$attrs, ...forwarded }"
      class="ds-combobox__input"
      data-test="ds-combobox-input"
    >
      <slot />
    </ComboboxInput>
  </div>
</template>

<style>
.ds-combobox__input-wrapper {
  display: flex;
  align-items: center;
  gap: var(--ds-space-xs);
  block-size: 36px;
  padding-inline: var(--ds-space-sm);
  border-block-end: 1px solid var(--ds-color-border);
}
.ds-combobox__input-icon {
  flex: none;
  color: var(--ds-color-text-grey);
  opacity: 0.6;
}
.ds-combobox__input {
  display: flex;
  inline-size: 100%;
  block-size: 40px;
  padding-block: var(--ds-space-sm);
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
  background: transparent;
  border: 0;
  outline: none;
  border-radius: var(--ds-radius-md);
}
.ds-combobox__input::placeholder {
  color: var(--ds-color-placeholder);
}
.ds-combobox__input:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}
</style>
