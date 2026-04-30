<script setup lang="ts" generic="Type extends 'text' | 'number' = 'text'">
/**
 * PinInput — accessible OTP / PIN entry. Built on Reka UI's PinInput.
 */
import type { PinInputRootEmits, PinInputRootProps } from 'reka-ui'
import { PinInputRoot, useForwardPropsEmits } from 'reka-ui'

const props = withDefaults(defineProps<PinInputRootProps<Type>>(), {
  otp: true,
})
const emits = defineEmits<PinInputRootEmits<Type>>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <PinInputRoot
    v-bind="forwarded"
    :otp="props.otp"
    class="ds-pin-input"
    data-test="ds-pin-input"
  >
    <slot />
  </PinInputRoot>
</template>

<style>
.ds-pin-input {
  display: flex;
  align-items: center;
  gap: var(--ds-space-xs);
}
.ds-pin-input:has(:disabled),
.ds-pin-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
