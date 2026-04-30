<script setup lang="ts">
/**
 * PinInputSeparator — non-interactive separator between PinInput groups.
 * Default renders an inline minus icon.
 */
import type { PrimitiveProps } from 'reka-ui'
import { Primitive, useForwardProps } from 'reka-ui'

const props = defineProps<PrimitiveProps>()
const forwarded = useForwardProps(props)
</script>

<template>
  <Primitive
    v-bind="forwarded"
    class="ds-pin-input__separator"
    data-test="ds-pin-input-separator"
  >
    <slot>
      <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
        <path d="M3 7 L11 7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
      </svg>
    </slot>
  </Primitive>
</template>

<style>
.ds-pin-input__separator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--ds-color-text-grey);
  padding-inline: var(--ds-space-2xs);
}
</style>
