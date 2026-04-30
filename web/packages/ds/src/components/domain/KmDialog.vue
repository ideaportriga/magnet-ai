<script setup lang="ts">
/**
 * `<km-dialog>` — modal overlay rendered via `<DsDialog>`.
 *
 * Public API (preserved 1:1 for ~342 admin call-sites):
 *   modelValue (v-model), size, persistent, maximized, seamless, position,
 *   noBackdropDismiss, noEscDismiss
 *
 * Slots: `header`, `title`, `description`, `footer`, default.
 *
 * Emits: update:modelValue, cancel, hide.
 */

import { computed } from 'vue'
import DsDialog, { type DsDialogSize } from '../primitives/Dialog/DsDialog.vue'

type DialogPosition = 'standard' | 'top' | 'right' | 'bottom' | 'left'

const props = withDefaults(
  defineProps<{
    modelValue?: boolean
    size?: DsDialogSize
    persistent?: boolean
    maximized?: boolean
    seamless?: boolean
    position?: DialogPosition
    noBackdropDismiss?: boolean
    noEscDismiss?: boolean
  }>(),
  {
    modelValue: false,
    size: 'md',
    persistent: false,
    maximized: false,
    seamless: false,
    position: 'standard',
    noBackdropDismiss: false,
    noEscDismiss: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  cancel: []
  hide: []
}>()

defineSlots<{
  header?: () => unknown
  title?: () => unknown
  description?: () => unknown
  footer?: () => unknown
  default?: () => unknown
}>()

/**
 * `maximized` short-circuits to size="full"; otherwise we honour the legacy
 * `size` prop. `DsDialog` already supports `sm | md | lg | xl | full`.
 */
const dsSize = computed<DsDialogSize>(() => (props.maximized ? 'full' : props.size))

/**
 * Legacy `persistent`, `noBackdropDismiss`, `noEscDismiss` all map to "the
 * dialog cannot be dismissed by clicking outside or pressing Esc". DsDialog
 * exposes a single `dismissible` flag. Any of the three blocks dismissal.
 */
const dismissible = computed(
  () => !(props.persistent || props.noBackdropDismiss || props.noEscDismiss),
)

const open = computed({
  get: () => props.modelValue,
  set: (next: boolean) => {
    emit('update:modelValue', next)
    if (!next) {
      emit('hide')
      emit('cancel')
    }
  },
})
</script>

<template>
  <DsDialog
    v-model:open="open"
    :size="dsSize"
    :dismissible="dismissible"
    hide-close
    visually-hidden-title
    class="km-dialog"
    :class="[
      `km-dialog--position-${position}`,
      { 'km-dialog--seamless': seamless, 'km-dialog--maximized': maximized },
    ]"
    data-test="km-dialog"
  >
    <!-- DsDialog requires a title for a11y. If callers pass a `title` slot,
         forward it; otherwise render a hidden default placeholder. -->
    <template #title>
      <slot name="title">Dialog</slot>
    </template>

    <template v-if="$slots.description" #description>
      <slot name="file-text" />
    </template>

    <!-- Legacy markup typically embeds the header inside the body. Surface a
         `header` slot above the default for callers that want it explicit. -->
    <slot name="header" />
    <slot />

    <template v-if="$slots.footer" #footer>
      <slot name="footer" />
    </template>
  </DsDialog>
</template>

<style>
/* Legacy callers often embed their own card/header inside the default slot.
 * The DsDialog primitive adds vertical padding + a footer rule that we want
 * to soften so legacy markup keeps its own spacing. */
.km-dialog.ds-dialog {
  padding: 0;
  gap: 0;
  overflow: visible;
}
.km-dialog .ds-dialog__body {
  padding: 0;
  overflow: auto;
}

/* Seamless: no shadow / chrome — the slot content owns the surface. */
.km-dialog--seamless.ds-dialog {
  background: transparent;
  box-shadow: none;
  border-radius: 0;
}

/* Maximized: full-screen surface. */
.km-dialog--maximized.ds-dialog {
  inline-size: 100vi;
  block-size: 100vb;
  max-block-size: 100vb;
  border-radius: 0;
  inset: 0;
  transform: none;
  inset-block-start: 0;
  inset-inline-start: 0;
}

/* Edge-anchored positions (drawer-style). */
.km-dialog--position-top.ds-dialog {
  inset-block-start: 0;
  transform: translate(-50%, 0);
}
.km-dialog--position-bottom.ds-dialog {
  inset-block: auto 0;
  transform: translate(-50%, 0);
}
.km-dialog--position-left.ds-dialog {
  inset-block-start: 0;
  inset-inline-start: 0;
  block-size: 100vb;
  max-block-size: 100vb;
  transform: none;
  border-radius: 0;
}
.km-dialog--position-right.ds-dialog {
  inset-block-start: 0;
  inset-inline: auto 0;
  block-size: 100vb;
  max-block-size: 100vb;
  transform: none;
  border-radius: 0;
}
</style>
