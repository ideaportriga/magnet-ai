<script setup lang="ts">
/**
 * Dialog primitive — accessible modal built on Reka UI's Dialog.
 *
 * Public API stays semantic (no Quasar `flat`, `unelevated`, etc.):
 *
 *   <DsDialog v-model:open="show" size="md" :dismissible="true">
 *     <template #title>Edit user</template>
 *     <template #description>Update the user details below.</template>
 *     <UserForm />
 *     <template #footer>
 *       <button @click="show = false">Cancel</button>
 *       <button @click="save">Save</button>
 *     </template>
 *   </DsDialog>
 */

import {
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
  DialogTrigger,
  VisuallyHidden,
} from 'reka-ui'

export type DsDialogSize = 'sm' | 'md' | 'lg' | 'xl' | 'full'

withDefaults(
  defineProps<{
    /** Bound to the dialog's open state (use `v-model:open`). */
    open?: boolean
    /** Width preset; falls through to `--ds-dialog-width-*` tokens. */
    size?: DsDialogSize
    /** Whether clicking the overlay or pressing Esc dismisses the dialog. */
    dismissible?: boolean
    /** Hide the visible close button (the X in the corner). */
    hideClose?: boolean
    /** Visually hide the title (still announced to screen readers). */
    visuallyHiddenTitle?: boolean
  }>(),
  {
    open: false,
    size: 'md',
    dismissible: true,
    hideClose: false,
    visuallyHiddenTitle: false,
  },
)

defineEmits<{
  'update:open': [value: boolean]
}>()

defineSlots<{
  /** Optional trigger element (alternative to controlled v-model). */
  trigger?: () => unknown
  /** Required for accessibility — pass plain text or rich nodes. */
  title?: () => unknown
  /** Optional descriptive subtitle below the title. */
  description?: () => unknown
  /** Main body of the dialog. */
  default?: () => unknown
  /** Footer / actions area. */
  footer?: () => unknown
}>()
</script>

<template>
  <DialogRoot
    :open="open"
    @update:open="$emit('update:open', $event)"
  >
    <DialogTrigger v-if="$slots.trigger" as-child>
      <slot name="trigger" />
    </DialogTrigger>

    <DialogPortal>
      <DialogOverlay class="ds-dialog__overlay" data-test="ds-dialog-overlay" />

      <DialogContent
        class="ds-dialog"
        :data-size="size"
        data-test="ds-dialog"
        v-bind="$slots.description ? {} : { 'aria-describedby': undefined }"
        @pointer-down-outside="!dismissible && $event.preventDefault()"
        @escape-key-down="!dismissible && $event.preventDefault()"
      >
        <header v-if="$slots.title || $slots.description" class="ds-dialog__header stack" data-gap="2xs">
          <component
            :is="visuallyHiddenTitle ? VisuallyHidden : 'div'"
          >
            <DialogTitle as="h2" class="ds-dialog__title">
              <slot name="title" />
            </DialogTitle>
          </component>

          <DialogDescription v-if="$slots.description" class="ds-dialog__description">
            <slot name="file-text" />
          </DialogDescription>
        </header>

        <div class="ds-dialog__body">
          <slot />
        </div>

        <footer v-if="$slots.footer" class="ds-dialog__footer cluster gap-sm" data-justify="end">
          <slot name="footer" />
        </footer>

        <DialogClose
          v-if="!hideClose"
          class="ds-dialog__close"
          aria-label="Close dialog"
          data-test="ds-dialog-close"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
            <path
              d="M2 2 L12 12 M12 2 L2 12"
              stroke="currentColor"
              stroke-width="1.6"
              stroke-linecap="round"
            />
          </svg>
        </DialogClose>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>

<style>
.ds-dialog__overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 16, 26, 0.45);
  z-index: var(--ds-z-modal);
  animation: ds-fade-in var(--ds-duration-base) var(--ds-ease-out);
}
.ds-dialog__overlay[data-state='closed'] {
  animation: ds-fade-out var(--ds-duration-fast) var(--ds-ease-in);
}

.ds-dialog {
  position: fixed;
  inset-block-start: 50%;
  inset-inline-start: 50%;
  /* Sit one stacking layer above the overlay (same modal token, +1) so
   * clicks on dialog content reliably hit it instead of the underlying
   * overlay element — fixes Cypress "covered by overlay" actionability
   * errors on dialogs whose body is a plain Vue subtree. */
  z-index: calc(var(--ds-z-modal) + 1);
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-lg);
  inline-size: min(var(--ds-dialog-width-md), calc(100vi - 2 * var(--ds-space-lg)));
  max-block-size: calc(100vb - 2 * var(--ds-space-lg));
  padding: var(--ds-dialog-padding);
  background: var(--ds-color-panel-main-bg);
  color: var(--ds-color-black);
  border-radius: var(--ds-dialog-radius);
  box-shadow: var(--ds-shadow-xl);
  transform: translate(-50%, -50%);
  animation: ds-dialog-in var(--ds-duration-base) var(--ds-ease-out);
  overflow: hidden;
}
.ds-dialog[data-state='closed'] {
  animation: ds-dialog-out var(--ds-duration-fast) var(--ds-ease-in);
}

.ds-dialog[data-size='sm']   { inline-size: min(var(--ds-dialog-width-sm), calc(100vi - 2 * var(--ds-space-lg))); }
.ds-dialog[data-size='md']   { inline-size: min(var(--ds-dialog-width-md), calc(100vi - 2 * var(--ds-space-lg))); }
.ds-dialog[data-size='lg']   { inline-size: min(var(--ds-dialog-width-lg), calc(100vi - 2 * var(--ds-space-lg))); }
.ds-dialog[data-size='xl']   { inline-size: min(960px, calc(100vi - 2 * var(--ds-space-lg))); }
.ds-dialog[data-size='full'] { inline-size: calc(100vi - 2 * var(--ds-space-lg)); max-inline-size: none; }

.ds-dialog__title {
  font-size: var(--ds-font-size-h2);
  font-weight: var(--ds-font-weight-semibold);
  line-height: var(--ds-line-height-snug);
}
.ds-dialog__description {
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-text-grey);
}
.ds-dialog__body {
  flex: 1 1 auto;
  min-block-size: 0;
  overflow: auto;
}
.ds-dialog__footer {
  flex: none;
  padding-block-start: var(--ds-space-md);
}
.ds-dialog__close {
  position: absolute;
  inset-block-start: var(--ds-space-md);
  inset-inline-end: var(--ds-space-md);
  inline-size: 28px;
  block-size: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--ds-radius-sm);
  color: var(--ds-color-text-grey);
  background: transparent;
  cursor: pointer;
  border: 0;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-dialog__close:hover {
  background: var(--ds-color-light);
  color: var(--ds-color-black);
}

</style>
