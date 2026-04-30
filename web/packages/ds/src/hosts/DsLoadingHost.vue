<script setup lang="ts">
/**
 * Global loading overlay. Pure CSS spinner — keeps the bundle minimal.
 * Mount once near the application root.
 */

import { computed } from 'vue'
import { loadingState } from './loadingStore'

const visible = computed(() => loadingState.pending > 0)
</script>

<template>
  <Transition name="ds-loading">
    <div
      v-if="visible"
      class="ds-loading"
      role="status"
      aria-live="polite"
      data-test="ds-loading"
    >
      <div class="ds-loading__panel" :data-has-message="!!loadingState.message || undefined">
        <div class="ds-loading__spinner" aria-hidden="true" />
        <p v-if="loadingState.message" class="ds-loading__message">{{ loadingState.message }}</p>
      </div>
    </div>
  </Transition>
</template>

<style>
.ds-loading {
  position: fixed;
  inset: 0;
  z-index: var(--ds-z-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--ds-color-overlay-loading);
  backdrop-filter: blur(var(--ds-loader-overlay-blur)) saturate(var(--ds-loader-overlay-saturation));
}

.ds-loading__panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--ds-space-md);
  padding: var(--ds-space-lg) var(--ds-space-2xl);
  background: transparent;
  border: 0;
  border-radius: var(--ds-loader-overlay-radius);
  box-shadow: none;
  min-inline-size: 12rem;
}

.ds-loading__spinner {
  inline-size: var(--ds-loader-overlay-spinner-size);
  block-size: var(--ds-loader-overlay-spinner-size);
  border: 3px solid var(--ds-color-border);
  border-block-start-color: var(--ds-color-primary);
  border-radius: 50%;
  animation: ds-spin var(--ds-loader-speed) var(--ds-ease-linear) infinite;
}

.ds-loading__message {
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-text-grey);
  margin: 0;
}

.ds-loading-enter-active,
.ds-loading-leave-active {
  transition: opacity 180ms var(--ds-ease-out);
}
.ds-loading-enter-from,
.ds-loading-leave-to {
  opacity: 0;
}

.ds-loading-enter-active .ds-loading__panel,
.ds-loading-leave-active .ds-loading__panel {
  transition: opacity 180ms var(--ds-ease-out), transform 180ms var(--ds-ease-out);
}

.ds-loading-enter-from .ds-loading__panel,
.ds-loading-leave-to .ds-loading__panel {
  opacity: 0;
  transform: translateY(4px) scale(0.98);
}

</style>
