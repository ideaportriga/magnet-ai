<script setup lang="ts">
/**
 * `<km-inner-loading>` — drop-in for the legacy `<km-inner-loading>` wrapper.
 * Renders an absolutely positioned overlay with a spinner; expects the
 * parent element to be `position: relative`.
 *
 * Visual identity matches `DsLoadingHost`: the same frosted-glass overlay,
 * blur strength, and 32px ring spinner so a route-level loader and a
 * container-level loader feel like one motif. The legacy `size` and `color`
 * props remain for back-compat but per-call-site overrides should become
 * rare — the spinner reads its size and colour from DS tokens by default.
 */

import { resolveDsColor } from '../../utils/resolveDsColor'

withDefaults(
  defineProps<{
    showing?: boolean
    /** Spinner size (CSS length). Defaults to the DS overlay spinner size. */
    size?: string
    /** Spinner colour token or CSS colour. Defaults to brand primary. */
    color?: string
  }>(),
  {
    showing: true,
    size: '',
    color: '',
  },
)
</script>

<template>
  <Transition name="km-inner-loading">
    <div
      v-if="showing"
      class="km-inner-loading"
      role="status"
      aria-live="polite"
      data-test="km-inner-loading"
    >
      <span
        class="km-inner-loading__spinner"
        :style="{
          inlineSize: size || undefined,
          blockSize: size || undefined,
          borderTopColor: color ? resolveDsColor(color) : undefined,
        }"
      />
      <slot />
    </div>
  </Transition>
</template>

<style>
.km-inner-loading {
  position: absolute;
  inset: 0;
  z-index: var(--ds-z-overlay);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--ds-space-sm);
  background: var(--ds-color-overlay-loading);
  backdrop-filter: blur(var(--ds-loader-overlay-blur)) saturate(var(--ds-loader-overlay-saturation));
}
.km-inner-loading__spinner {
  display: inline-block;
  inline-size: var(--ds-loader-overlay-spinner-size);
  block-size: var(--ds-loader-overlay-spinner-size);
  border: 3px solid var(--ds-color-border);
  border-block-start-color: var(--ds-color-primary);
  border-radius: 50%;
  animation: ds-spin var(--ds-loader-speed) var(--ds-ease-linear) infinite;
}

.km-inner-loading-enter-active,
.km-inner-loading-leave-active {
  transition: opacity var(--ds-duration-fast) var(--ds-ease-out);
}
.km-inner-loading-enter-from,
.km-inner-loading-leave-to {
  opacity: 0;
}

</style>
