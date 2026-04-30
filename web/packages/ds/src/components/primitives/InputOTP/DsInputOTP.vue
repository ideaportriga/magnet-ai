<script setup lang="ts">
/**
 * Input OTP — `vue-input-otp` based one-time-password input.
 *
 *   <DsInputOTP :maxlength="6" v-slot="{ slots }">
 *     <DsInputOTPGroup>
 *       <DsInputOTPSlot v-for="(s, i) in slots" :key="i" :index="i" />
 *     </DsInputOTPGroup>
 *   </DsInputOTP>
 */

import type { OTPInputEmits, OTPInputProps } from 'vue-input-otp'
import { useForwardPropsEmits } from 'reka-ui'
import { OTPInput } from 'vue-input-otp'

const props = defineProps<OTPInputProps>()
const emits = defineEmits<OTPInputEmits>()

const forwarded = useForwardPropsEmits(props, emits)
</script>

<template>
  <OTPInput
    v-slot="slotProps"
    v-bind="forwarded"
    container-class="ds-input-otp"
    class="ds-input-otp__input"
    data-test="ds-input-otp"
  >
    <slot v-bind="slotProps" />
  </OTPInput>
</template>

<style>
.ds-input-otp {
  display: flex;
  align-items: center;
  gap: var(--ds-space-sm);
}
.ds-input-otp:has(input:disabled) {
  opacity: 0.5;
}
.ds-input-otp__input:disabled {
  cursor: not-allowed;
}
</style>
