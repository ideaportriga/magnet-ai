<template>
  <span class="kg-inline-field" :class="{ 'kg-inline-field--interactive': interactive }">
    <slot />
    <km-tooltip v-if="tooltip" anchor="top middle" self="bottom middle">
      {{ tooltip }}
    </km-tooltip>
  </span>
</template>

<script setup lang="ts">
import { m } from '@/paraglide/messages'
interface Props {
  interactive?: boolean
  tooltip?: string
}

withDefaults(defineProps<Props>(), {
  interactive: false,
  tooltip: undefined,
})
</script>

<style scoped>
.kg-inline-field {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  max-inline-size: 320px;
  min-inline-size: 0;
  overflow: hidden;
  border-block-end: 1px dashed var(--ds-color-primary-transparent);
  padding: 0 4px 1px;
  color: var(--ds-color-primary);
  font-weight: 500;
  white-space: nowrap;
  transition: border-color 0.15s ease;
}

.kg-inline-field:hover {
  border-block-end-color: var(--ds-color-primary);
}

.kg-inline-field--interactive {
  cursor: pointer;
  user-select: none;
}

/* Reka injects tabindex on the popover trigger when used with as-child,
   so the inline field can receive keyboard focus. Surface that with a
   visible focus ring matching DS conventions. */
.kg-inline-field--interactive:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
  border-radius: 2px;
  border-block-end-color: var(--ds-color-primary);
}

.kg-inline-field :deep(.kg-inline-field__input) {
  min-inline-size: 0;
  max-inline-size: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  border: none;
  outline: none;
  background: transparent;
  font-size: inherit;
  font-weight: 500;
  color: var(--ds-color-primary);
  font-family: var(--ds-font-mono);
  padding: 0;
  text-align: center;
}

.kg-inline-field :deep(.kg-inline-field__input::placeholder) {
  color: var(--ds-color-primary-transparent);
  font-style: italic;
}
</style>
