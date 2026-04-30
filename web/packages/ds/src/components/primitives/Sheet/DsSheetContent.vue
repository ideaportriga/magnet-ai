<script setup lang="ts">
/**
 * SheetContent — the visible panel that slides in from one of four sides.
 * Variant via `:side="…"` (top | right | bottom | left). Renders its own
 * portal + overlay + close button.
 */
import type { DialogContentEmits, DialogContentProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import {
  DialogClose,
  DialogContent,
  DialogPortal,
  useForwardPropsEmits,
} from 'reka-ui'
import DsSheetOverlay from './DsSheetOverlay.vue'

interface SheetContentProps extends DialogContentProps {
  side?: 'top' | 'right' | 'bottom' | 'left'
}

defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<SheetContentProps>(), {
  side: 'right',
})
const emits = defineEmits<DialogContentEmits>()

const delegatedProps = reactiveOmit(props, 'side')
const forwarded = useForwardPropsEmits(delegatedProps, emits)
</script>

<template>
  <DialogPortal>
    <DsSheetOverlay />
    <DialogContent
      :aria-describedby="undefined"
      v-bind="{ ...$attrs, ...forwarded }"
      class="ds-sheet"
      :data-side="side"
      data-test="ds-sheet"
    >
      <slot />

      <DialogClose
        class="ds-sheet__close"
        aria-label="Close sheet"
        data-test="ds-sheet-close-x"
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
</template>

<style>
.ds-sheet {
  position: fixed;
  z-index: var(--ds-z-modal);
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-md);
  background: var(--ds-color-background);
  color: var(--ds-color-black);
  box-shadow: var(--ds-shadow-xl);
  transition: transform var(--ds-duration-base) var(--ds-ease-in-out);
}

/* ---------- side: right (default) ---------- */
.ds-sheet[data-side='right'] {
  inset-block: 0;
  inset-inline-end: 0;
  block-size: 100%;
  inline-size: min(75vi, 24rem);
  border-inline-start: 1px solid var(--ds-color-border);
  animation: ds-slide-in-from-right var(--ds-duration-slow) var(--ds-ease-out);
}
.ds-sheet[data-side='right'][data-state='closed'] {
  animation: ds-slide-out-to-right var(--ds-duration-base) var(--ds-ease-in);
}

/* ---------- side: left ---------- */
.ds-sheet[data-side='left'] {
  inset-block: 0;
  inset-inline-start: 0;
  block-size: 100%;
  inline-size: min(75vi, 24rem);
  border-inline-end: 1px solid var(--ds-color-border);
  animation: ds-slide-in-from-left var(--ds-duration-slow) var(--ds-ease-out);
}
.ds-sheet[data-side='left'][data-state='closed'] {
  animation: ds-slide-out-to-left var(--ds-duration-base) var(--ds-ease-in);
}

/* ---------- side: top ---------- */
.ds-sheet[data-side='top'] {
  inset-inline: 0;
  inset-block-start: 0;
  inline-size: 100%;
  block-size: auto;
  border-block-end: 1px solid var(--ds-color-border);
  animation: ds-slide-in-from-top var(--ds-duration-slow) var(--ds-ease-out);
}
.ds-sheet[data-side='top'][data-state='closed'] {
  animation: ds-slide-out-to-top var(--ds-duration-base) var(--ds-ease-in);
}

/* ---------- side: bottom ---------- */
.ds-sheet[data-side='bottom'] {
  inset-inline: 0;
  inset-block-end: 0;
  inline-size: 100%;
  block-size: auto;
  border-block-start: 1px solid var(--ds-color-border);
  animation: ds-slide-in-from-bottom var(--ds-duration-slow) var(--ds-ease-out);
}
.ds-sheet[data-side='bottom'][data-state='closed'] {
  animation: ds-slide-out-to-bottom var(--ds-duration-base) var(--ds-ease-in);
}

.ds-sheet__close {
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
  opacity: 0.7;
  transition: opacity var(--ds-duration-fast) var(--ds-ease-out), background var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-sheet__close:hover {
  opacity: 1;
  background: var(--ds-color-light);
  color: var(--ds-color-black);
}
.ds-sheet__close:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}

</style>
