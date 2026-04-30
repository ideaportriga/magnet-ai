<script setup lang="ts">
/**
 * CommandInput — search field driving the Command's filter state. Auto-focused
 * on mount, with an inline magnifying-glass icon.
 */
import type { ListboxFilterProps } from 'reka-ui'
import { ListboxFilter, useForwardProps } from 'reka-ui'
import { useCommandContext } from './context'

defineOptions({ inheritAttrs: false })

const props = defineProps<ListboxFilterProps>()
const forwardedProps = useForwardProps(props)

const { filterState } = useCommandContext()
</script>

<template>
  <div class="ds-command__input-wrapper" data-test="ds-command-input-wrapper">
    <svg
      class="ds-command__input-icon"
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
    <ListboxFilter
      v-bind="{ ...forwardedProps, ...$attrs }"
      v-model="filterState.search"
      auto-focus
      class="ds-command__input"
      data-test="ds-command-input"
    />
  </div>
</template>

<style>
.ds-command__input-wrapper {
  display: flex;
  align-items: center;
  gap: var(--ds-space-xs);
  block-size: 36px;
  padding-inline: var(--ds-space-sm);
  border-block-end: 1px solid var(--ds-color-border);
}
.ds-command__input-icon {
  flex: none;
  color: var(--ds-color-text-grey);
  opacity: 0.6;
}
.ds-command__input {
  display: flex;
  inline-size: 100%;
  block-size: 40px;
  padding-block: var(--ds-space-sm);
  background: transparent;
  border: 0;
  outline: none;
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
  border-radius: var(--ds-radius-md);
}
.ds-command__input::placeholder {
  color: var(--ds-color-placeholder);
}
.ds-command__input:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}
</style>
