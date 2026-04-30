<script setup lang="ts">
/**
 * TagsInputClear — clears all tags from a TagsInput. Reka UI doesn't ship
 * a dedicated "clear" primitive, so we use the inject() escape hatch on
 * TagsInputRoot to set the model value back to []. Defaults to a small "x"
 * icon when no slot content is provided.
 */
import { Primitive, injectTagsInputRootContext } from 'reka-ui'

const ctx = injectTagsInputRootContext()

function onClear(event: MouseEvent) {
  event.preventDefault()
  if (!ctx || ctx.disabled.value) return
  // Remove tags one by one from the end so the underlying root emits
  // the regular `update:modelValue` / `removeTag` events instead of us
  // mutating the ref directly.
  for (let i = ctx.modelValue.value.length - 1; i >= 0; i--) {
    ctx.onRemoveValue(i)
  }
}
</script>

<template>
  <Primitive
    as="button"
    type="button"
    class="ds-tags-input__clear"
    data-test="ds-tags-input-clear"
    aria-label="Clear all tags"
    :data-disabled="ctx?.disabled?.value ? '' : undefined"
    @click="onClear"
  >
    <slot>
      <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
        <path
          d="M2 2 L12 12 M12 2 L2 12"
          stroke="currentColor"
          stroke-width="1.6"
          stroke-linecap="round"
        />
      </svg>
    </slot>
  </Primitive>
</template>

<style>
.ds-tags-input__clear {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 20px;
  block-size: 20px;
  margin-inline-start: auto;
  padding: 0;
  background: transparent;
  color: var(--ds-color-text-grey);
  border: 0;
  border-radius: var(--ds-radius-sm);
  cursor: pointer;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-tags-input__clear:hover {
  background: var(--ds-color-control-hover-bg);
  color: var(--ds-color-black);
}
.ds-tags-input__clear[data-disabled] {
  opacity: 0.5;
  pointer-events: none;
  cursor: not-allowed;
}
</style>
