<script setup lang="ts">
/**
 * Confirmation dialog (replacement for Quasar's `Dialog.create({ ok, cancel })`
 * pattern). Built on Reka's `AlertDialog` so it cannot be dismissed by
 * clicking outside — the user must explicitly choose Confirm or Cancel.
 */

import {
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogOverlay,
  AlertDialogPortal,
  AlertDialogRoot,
  AlertDialogTitle,
  AlertDialogTrigger,
} from 'reka-ui'

withDefaults(
  defineProps<{
    open?: boolean
    title: string
    description?: string
    confirmLabel?: string
    cancelLabel?: string
    /** Visual emphasis for destructive actions (delete, remove). */
    tone?: 'neutral' | 'danger'
  }>(),
  {
    open: false,
    confirmLabel: 'Confirm',
    cancelLabel: 'Cancel',
    tone: 'neutral',
  },
)

defineEmits<{
  'update:open': [value: boolean]
  confirm: []
  cancel: []
}>()

defineSlots<{
  trigger?: () => unknown
  default?: () => unknown
}>()
</script>

<template>
  <AlertDialogRoot
    :open="open"
    @update:open="$emit('update:open', $event)"
  >
    <AlertDialogTrigger v-if="$slots.trigger" as-child>
      <slot name="trigger" />
    </AlertDialogTrigger>

    <AlertDialogPortal>
      <AlertDialogOverlay class="ds-alert-dialog__overlay" />

      <AlertDialogContent
        class="ds-alert-dialog"
        :data-tone="tone"
        data-test="ds-alert-dialog"
        v-bind="(description || $slots.default) ? {} : { 'aria-describedby': undefined }"
      >
        <AlertDialogTitle class="ds-alert-dialog__title">
          {{ title }}
        </AlertDialogTitle>

        <AlertDialogDescription v-if="description || $slots.default" class="ds-alert-dialog__description">
          <slot>{{ description }}</slot>
        </AlertDialogDescription>

        <footer class="ds-alert-dialog__footer cluster gap-sm" data-justify="between">
          <AlertDialogCancel
            class="ds-alert-dialog__action"
            data-variant="secondary"
            data-test="ds-alert-dialog-cancel"
            @click="$emit('cancel')"
          >
            {{ cancelLabel }}
          </AlertDialogCancel>

          <AlertDialogAction
            class="ds-alert-dialog__action"
            :data-variant="tone === 'danger' ? 'danger' : 'primary'"
            data-test="ds-alert-dialog-confirm"
            @click="$emit('confirm')"
          >
            {{ confirmLabel }}
          </AlertDialogAction>
        </footer>
      </AlertDialogContent>
    </AlertDialogPortal>
  </AlertDialogRoot>
</template>

<style>
.ds-alert-dialog__overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 16, 26, 0.45);
  z-index: var(--ds-z-modal);
  animation: ds-fade-in var(--ds-duration-base) var(--ds-ease-out);
}

.ds-alert-dialog {
  position: fixed;
  inset-block-start: 50%;
  inset-inline-start: 50%;
  /* See DsDialog: dialog content sits one layer above its overlay. */
  z-index: calc(var(--ds-z-modal) + 1);
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-md);
  inline-size: min(var(--ds-dialog-width-sm), calc(100vi - 2 * var(--ds-space-lg)));
  padding: var(--ds-dialog-padding);
  background: var(--ds-color-panel-main-bg);
  color: var(--ds-color-black);
  border-radius: var(--ds-dialog-radius);
  box-shadow: var(--ds-shadow-xl);
  transform: translate(-50%, -50%);
  animation: ds-dialog-in var(--ds-duration-base) var(--ds-ease-out);
}
.ds-alert-dialog__title {
  font-size: var(--ds-font-size-h2);
  font-weight: var(--ds-font-weight-semibold);
}
.ds-alert-dialog__description {
  font-size: var(--ds-font-size-body);
  color: var(--ds-color-text-grey);
}
.ds-alert-dialog__footer { margin-block-start: var(--ds-space-sm); }
.ds-alert-dialog__action {
  padding: var(--ds-space-xs) var(--ds-space-md);
  border-radius: var(--ds-radius-md);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  border: 1px solid transparent;
  cursor: pointer;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-alert-dialog__action[data-variant='primary'] {
  background: var(--ds-color-btn-primary-bg);
  color: var(--ds-color-btn-primary-text);
}
.ds-alert-dialog__action[data-variant='primary']:hover {
  background: var(--ds-color-btn-primary-hover-bg);
}
.ds-alert-dialog__action[data-variant='danger'] {
  background: var(--ds-color-error);
  color: var(--ds-color-static-white);
}
.ds-alert-dialog__action[data-variant='danger']:hover {
  background: var(--ds-color-danger-700);
}
.ds-alert-dialog__action[data-variant='secondary'] {
  background: transparent;
  color: var(--ds-color-secondary-text);
  border-color: var(--ds-color-border);
}
.ds-alert-dialog__action[data-variant='secondary']:hover {
  background: var(--ds-color-light);
}
</style>
