<script setup lang="ts">
/**
 * Sonner — toast container backed by `vue-sonner`. Mount once near the app
 * root; trigger toasts via the `toast` helper from `vue-sonner`.
 *
 *   <DsSonner position="bottom-right" />
 */

import type { ToasterProps } from 'vue-sonner'
import { Toaster as Sonner } from 'vue-sonner'

const props = defineProps<ToasterProps>()
</script>

<template>
  <Sonner
    class="ds-sonner"
    data-test="ds-sonner"
    :style="{
      '--normal-bg': 'var(--ds-color-background)',
      '--normal-text': 'var(--ds-color-black)',
      '--normal-border': 'var(--ds-color-border)',
      '--success-bg': 'var(--ds-color-success-text)',
      '--success-text': 'var(--ds-color-white)',
      '--success-border': 'var(--ds-color-success)',
      '--error-bg': 'var(--ds-color-error-bg)',
      '--error-text': 'var(--ds-color-error-text)',
      '--error-border': 'var(--ds-color-error)',
      '--warning-bg': 'var(--ds-color-warning-bg)',
      '--warning-text': 'var(--ds-color-black)',
      '--warning-border': 'var(--ds-color-warning)',
      '--info-bg': 'var(--ds-color-primary-bg)',
      '--info-text': 'var(--ds-color-primary-text)',
      '--info-border': 'var(--ds-color-info)',
      '--border-radius': 'var(--ds-radius-md)',
      '--font-family': 'var(--ds-font-default)',
    }"
    v-bind="props"
  >
    <template #success-icon>
      <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
        <circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" stroke-width="1.5" />
        <path d="M5 8.5 L7 10.5 L11 6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </template>
    <template #info-icon>
      <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
        <circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" stroke-width="1.5" />
        <path d="M8 7 L8 11 M8 5 L8 5.01" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
      </svg>
    </template>
    <template #warning-icon>
      <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M8 1.5 L15 14 L1 14 Z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" />
        <path d="M8 6 L8 9.5 M8 11.5 L8 11.51" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
      </svg>
    </template>
    <template #error-icon>
      <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
        <polygon
          points="5,1 11,1 15,5 15,11 11,15 5,15 1,11 1,5"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linejoin="round"
        />
        <path d="M5.5 5.5 L10.5 10.5 M10.5 5.5 L5.5 10.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
      </svg>
    </template>
    <template #loading-icon>
      <span class="ds-sonner__spinner" aria-hidden="true" />
    </template>
    <template #close-icon>
      <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
        <path
          d="M2 2 L12 12 M12 2 L2 12"
          stroke="currentColor"
          stroke-width="1.6"
          stroke-linecap="round"
        />
      </svg>
    </template>
  </Sonner>
</template>

<style>
.ds-sonner {
  font-family: var(--ds-font-default);
}
.ds-sonner__spinner {
  display: inline-block;
  inline-size: 16px;
  block-size: 16px;
  border: 2px solid currentColor;
  border-block-end-color: transparent;
  border-radius: var(--ds-radius-full);
  animation: ds-spin 0.8s var(--ds-ease-linear) infinite;
}
</style>
