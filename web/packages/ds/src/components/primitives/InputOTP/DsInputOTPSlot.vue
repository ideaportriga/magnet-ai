<script setup lang="ts">
import { computed } from 'vue'
import { useVueOTPContext } from 'vue-input-otp'

const props = defineProps<{ index: number }>()

const context = useVueOTPContext()

const slot = computed(() => context?.value.slots[props.index])
</script>

<template>
  <div
    class="ds-input-otp__slot"
    :data-active="slot?.isActive ? 'true' : 'false'"
    data-test="ds-input-otp-slot"
  >
    {{ slot?.char }}
    <div v-if="slot?.hasFakeCaret" class="ds-input-otp__caret-wrap">
      <div class="ds-input-otp__caret" />
    </div>
  </div>
</template>

<style>
.ds-input-otp__slot {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 36px;
  block-size: 36px;
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
  background: var(--ds-color-control-bg);
  border-block: 1px solid var(--ds-color-control-border);
  border-inline-end: 1px solid var(--ds-color-control-border);
  outline: none;
  transition: var(--ds-transition-colors), var(--ds-transition-shadow);
}
.ds-input-otp__slot:first-child {
  border-inline-start: 1px solid var(--ds-color-control-border);
  border-start-start-radius: var(--ds-radius-md);
  border-end-start-radius: var(--ds-radius-md);
}
.ds-input-otp__slot:last-child {
  border-start-end-radius: var(--ds-radius-md);
  border-end-end-radius: var(--ds-radius-md);
}
.ds-input-otp__slot[data-active='true'] {
  z-index: 1;
  border-color: var(--ds-color-primary);
  box-shadow: 0 0 0 3px var(--ds-color-primary-transparent);
}

.ds-input-otp__caret-wrap {
  pointer-events: none;
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ds-input-otp__caret {
  inline-size: 1px;
  block-size: 16px;
  background: var(--ds-color-black);
  animation: ds-input-otp-caret-blink 1s infinite;
}

@keyframes ds-input-otp-caret-blink {
  0%, 50%   { opacity: 1; }
  50.01%, 100% { opacity: 0; }
}
</style>
