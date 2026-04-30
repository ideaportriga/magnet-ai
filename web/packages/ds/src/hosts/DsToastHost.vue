<script setup lang="ts">
/**
 * Singleton component that renders the toast queue.
 *
 * Mount it once near the application root:
 *
 *   <template>
 *     <RouterView />
 *     <DsToastHost />
 *   </template>
 */

import {
  ToastProvider,
  ToastRoot,
  ToastViewport,
  ToastTitle,
  ToastDescription,
  ToastAction,
  ToastClose,
} from 'reka-ui'
import { dismissToast, toastQueue, type ToastTone } from './toastStore'

const TONE_LABELS: Record<ToastTone, string> = {
  success: 'Success',
  error: 'Error',
  warning: 'Warning',
  info: 'Info',
  copied: 'Copied',
  confirm: 'Confirm',
  neutral: 'Notice',
}

defineProps<{
  /** Viewport CSS position. */
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center'
}>()

function handleOpenChange(id: string, open: boolean) {
  if (!open) dismissToast(id)
}
</script>

<template>
  <ToastProvider :swipe-direction="'right'">
    <ToastRoot
      v-for="item in toastQueue.items"
      :key="item.id"
      :open="true"
      :duration="item.duration"
      :type="item.tone === 'confirm' ? 'foreground' : 'background'"
      class="ds-toast"
      :data-tone="item.tone"
      data-test="ds-toast"
      @update:open="handleOpenChange(item.id, $event)"
    >
      <div class="ds-toast__body cluster gap-sm" data-align="start">
        <span class="ds-toast__indicator" :data-tone="item.tone" aria-hidden="true" />
        <div class="ds-toast__content stack" data-gap="2xs">
          <ToastTitle class="ds-toast__title">{{ TONE_LABELS[item.tone] }}</ToastTitle>
          <ToastDescription class="ds-toast__message">{{ item.message }}</ToastDescription>
          <p v-if="item.description" class="ds-toast__description">{{ item.description }}</p>
        </div>
        <ToastClose
          class="ds-toast__close"
          aria-label="Close"
          data-test="ds-toast-close"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
            <path
              d="M2 2 L12 12 M12 2 L2 12"
              stroke="currentColor"
              stroke-width="1.6"
              stroke-linecap="round"
            />
          </svg>
        </ToastClose>
      </div>

      <div
        v-if="item.actions && item.actions.length"
        class="ds-toast__actions cluster gap-sm"
        data-justify="end"
      >
        <ToastAction
          v-for="action in item.actions"
          :key="action.label"
          :alt-text="action.label"
          class="ds-toast__action"
          :data-variant="action.variant ?? 'secondary'"
          @click="action.onClick"
        >
          {{ action.label }}
        </ToastAction>
      </div>
    </ToastRoot>

    <ToastViewport
      class="ds-toast-viewport"
      :data-position="position ?? 'bottom-right'"
      data-test="ds-toast-viewport"
    />
  </ToastProvider>
</template>

<style>
.ds-toast-viewport {
  position: fixed;
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-sm);
  padding: var(--ds-space-lg);
  margin: 0;
  list-style: "";
  outline: none;
  z-index: var(--ds-z-toast);
  max-inline-size: 100vi;
  pointer-events: none;
}
.ds-toast-viewport[data-position='top-right']    { inset: 0 0 auto auto; }
.ds-toast-viewport[data-position='top-left']     { inset: 0 auto auto 0; }
.ds-toast-viewport[data-position='bottom-right'] { inset: auto 0 0 auto; }
.ds-toast-viewport[data-position='bottom-left']  { inset: auto auto 0 0; }
.ds-toast-viewport[data-position='top-center']   { inset: 0 50% auto auto; transform: translateX(50%); }
.ds-toast-viewport[data-position='bottom-center']{ inset: auto 50% 0 auto; transform: translateX(50%); }

.ds-toast {
  pointer-events: auto;
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-sm);
  inline-size: min(20rem, calc(100vi - 2 * var(--ds-space-lg)));
  padding: var(--ds-space-md) var(--ds-space-lg);
  background: var(--ds-color-panel-main-bg);
  color: var(--ds-color-black);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-lg);
  box-shadow: var(--ds-shadow-md);
  font-size: var(--ds-font-size-body);
  line-height: var(--ds-line-height-snug);
  animation: ds-toast-in var(--ds-duration-base) var(--ds-ease-out);
}

.ds-toast[data-state='closed'] {
  animation: ds-toast-out var(--ds-duration-fast) var(--ds-ease-in) forwards;
}

.ds-toast__indicator {
  inline-size: 4px;
  align-self: stretch;
  border-radius: var(--ds-radius-full);
  background: var(--ds-color-secondary);
}
.ds-toast__indicator[data-tone='success'] { background: var(--ds-color-success-text); }
.ds-toast__indicator[data-tone='error']   { background: var(--ds-color-error); }
.ds-toast__indicator[data-tone='warning'] { background: var(--ds-color-warning-secondary); }
.ds-toast__indicator[data-tone='info']    { background: var(--ds-color-info); }
.ds-toast__indicator[data-tone='copied']  { background: var(--ds-color-secondary); }
.ds-toast__indicator[data-tone='confirm'] { background: var(--ds-color-error); }
.ds-toast__indicator[data-tone='neutral'] { background: var(--ds-color-secondary); }

.ds-toast__content { flex: 1 1 auto; min-inline-size: 0; }
.ds-toast__title {
  font-size: var(--ds-font-size-caption);
  font-weight: var(--ds-font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--ds-color-text-grey);
}
.ds-toast__message { color: var(--ds-color-black); }
.ds-toast__description {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-text-grey);
}

.ds-toast__close {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 24px;
  block-size: 24px;
  border-radius: var(--ds-radius-sm);
  color: var(--ds-color-text-grey);
  background: transparent;
  border: 0;
  cursor: pointer;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-toast__close:hover {
  background: var(--ds-color-light);
  color: var(--ds-color-black);
}

.ds-toast__actions {
  margin-block-start: var(--ds-space-2xs);
}
.ds-toast__action {
  padding: var(--ds-space-xs) var(--ds-space-md);
  border-radius: var(--ds-radius-md);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  cursor: pointer;
  border: 1px solid transparent;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-toast__action[data-variant='primary'] {
  background: var(--ds-color-btn-primary-bg);
  color: var(--ds-color-btn-primary-text);
}
.ds-toast__action[data-variant='primary']:hover {
  background: var(--ds-color-btn-primary-hover-bg);
}
.ds-toast__action[data-variant='secondary'] {
  background: transparent;
  color: var(--ds-color-secondary-text);
  border-color: var(--ds-color-border);
}
.ds-toast__action[data-variant='secondary']:hover {
  background: var(--ds-color-light);
}

@keyframes ds-toast-in {
  from { opacity: 0; transform: translateX(120%); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes ds-toast-out {
  from { opacity: 1; transform: translateX(0); }
  to   { opacity: 0; transform: translateX(120%); }
}

.ds-toast-viewport[data-position$='left'] .ds-toast {
  animation-name: ds-toast-in-left;
}
.ds-toast-viewport[data-position$='left'] .ds-toast[data-state='closed'] {
  animation-name: ds-toast-out-left;
}
@keyframes ds-toast-in-left {
  from { opacity: 0; transform: translateX(-120%); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes ds-toast-out-left {
  from { opacity: 1; transform: translateX(0); }
  to   { opacity: 0; transform: translateX(-120%); }
}
</style>
