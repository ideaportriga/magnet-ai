<script setup lang="ts">
import type { ContextMenuContentEmits, ContextMenuContentProps } from 'reka-ui'
import { reactiveOmit } from '@vueuse/core'
import {
  ContextMenuContent,
  ContextMenuPortal,
  useForwardPropsEmits,
} from 'reka-ui'

defineOptions({ inheritAttrs: false })

const props = defineProps<ContextMenuContentProps>()
const emits = defineEmits<ContextMenuContentEmits>()

const delegatedProps = reactiveOmit(props, 'class' as never)
const forwarded = useForwardPropsEmits(delegatedProps, emits)
</script>

<template>
  <ContextMenuPortal>
    <ContextMenuContent
      class="ds-menu-content"
      data-test="ds-context-menu-content"
      v-bind="{ ...$attrs, ...forwarded }"
    >
      <slot />
    </ContextMenuContent>
  </ContextMenuPortal>
</template>

<style>
.ds-menu-content {
  z-index: var(--ds-z-popover);
  min-inline-size: 12rem;
  max-block-size: var(--reka-context-menu-content-available-height);
  padding: var(--ds-space-2xs);
  overflow-inline: hidden;
  overflow-block: auto;
  background: var(--ds-color-panel-main-bg, var(--ds-color-white));
  color: var(--ds-color-black);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  box-shadow: var(--ds-shadow-md);
  outline: none;
  animation: ds-menu-in var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-menu-content[data-state='closed'] {
  animation: ds-menu-out var(--ds-duration-instant) var(--ds-ease-in);
}

/* Shared menu item styles for context-menu / menubar / dropdown sub-content */
.ds-menu-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--ds-space-sm);
  padding-block: var(--ds-space-xs);
  padding-inline: var(--ds-space-sm);
  font-size: var(--ds-font-size-label);
  line-height: var(--ds-line-height-snug);
  color: var(--ds-color-black);
  border-radius: var(--ds-radius-sm);
  cursor: default;
  user-select: none;
  outline: none;
}
/* Force KmGlyph icons inside menu items to follow the item's color in the
   states where the item itself recolors — destructive (red) and highlighted
   (accent). In the default state the icon keeps whatever color the caller
   passed (typically the icon-grey token). */
.ds-menu-item[data-variant='destructive'],
.ds-menu-item[data-highlighted] {
  --km-glyph-color: currentColor;
}
.ds-menu-item[data-highlighted] {
  background: var(--ds-color-accent-bg, var(--ds-color-light));
  color: var(--ds-color-accent, var(--ds-color-black));
}
.ds-menu-item[data-disabled] {
  color: var(--ds-color-placeholder);
  pointer-events: none;
  opacity: 0.5;
}
.ds-menu-item[data-inset] {
  padding-inline-start: var(--ds-space-2xl);
}
.ds-menu-item[data-variant='destructive'] {
  color: var(--ds-color-error);
}
.ds-menu-item[data-variant='destructive'][data-highlighted] {
  background: var(--ds-color-error-bg);
  color: var(--ds-color-error-text, var(--ds-color-error));
}
.ds-menu-item[data-state='open'] {
  background: var(--ds-color-accent-bg, var(--ds-color-light));
  color: var(--ds-color-accent, var(--ds-color-black));
}
.ds-menu-item :where(svg) {
  flex-shrink: 0;
  pointer-events: none;
  inline-size: 1rem;
  block-size: 1rem;
}

.ds-menu-item-indicator {
  position: absolute;
  inset-inline-start: var(--ds-space-xs);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 0.875rem;
  block-size: 0.875rem;
  pointer-events: none;
}
.ds-menu-item--check,
.ds-menu-item--radio {
  padding-inline-start: var(--ds-space-2xl);
}

.ds-menu-label {
  padding-block: var(--ds-space-xs);
  padding-inline: var(--ds-space-sm);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-text-grey, var(--ds-color-black));
  user-select: none;
}
.ds-menu-label[data-inset] {
  padding-inline-start: var(--ds-space-2xl);
}

.ds-menu-separator {
  block-size: 1px;
  margin-block: var(--ds-space-2xs);
  margin-inline: calc(var(--ds-space-2xs) * -1);
  background: var(--ds-color-border);
}

.ds-menu-shortcut {
  margin-inline-start: auto;
  font-size: var(--ds-font-size-xs);
  letter-spacing: 0.1em;
  color: var(--ds-color-text-weak, var(--ds-color-text-grey));
}

.ds-menu-sub-trigger__chevron {
  margin-inline-start: auto;
  inline-size: 1rem;
  block-size: 1rem;
  transition: transform var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-menu-item[data-state='open'] .ds-menu-sub-trigger__chevron {
  /* sub-trigger chevron pointing right doesn't rotate; reserved for future */
}
</style>
