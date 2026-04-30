<script setup lang="ts">
/**
 * Dropdown menu primitive built on Reka UI's DropdownMenu. Supports the most
 * common shape — a trigger element plus a flat list of action items.
 *
 *   <DsDropdownMenu :items="[{ label: 'Edit', onSelect: edit }, ...]">
 *     <template #trigger><button>Actions</button></template>
 *   </DsDropdownMenu>
 *
 * For rich layouts (sub-menus, group headings, dividers) consume the Reka
 * primitives directly — this is intentionally a thin convenience wrapper.
 */

import {
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuRoot,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from 'reka-ui'

export interface DsDropdownMenuItem {
  label?: string
  /** When `true`, renders as a separator instead of an actionable item. */
  separator?: boolean
  /** Disable interaction on this item (still rendered for context). */
  disabled?: boolean
  /** Visual emphasis: 'danger' for destructive actions. */
  tone?: 'neutral' | 'primary' | 'danger'
  /** Optional leading icon component (slot-content for now). */
  icon?: string
  /** Click handler — receives the item the user activated. */
  onSelect?: (item: DsDropdownMenuItem) => void
}

withDefaults(
  defineProps<{
    items: DsDropdownMenuItem[]
    /** Position of the menu relative to the trigger. */
    placement?: 'bottom' | 'top' | 'left' | 'right'
    /** Alignment along the trigger axis. */
    align?: 'start' | 'center' | 'end'
    sideOffset?: number
  }>(),
  {
    placement: 'bottom',
    align: 'start',
    sideOffset: 4,
  },
)

defineSlots<{
  trigger?: () => unknown
}>()
</script>

<template>
  <DropdownMenuRoot>
    <DropdownMenuTrigger as-child>
      <slot name="trigger" />
    </DropdownMenuTrigger>

    <DropdownMenuPortal>
      <DropdownMenuContent
        class="ds-menu"
        :side="placement"
        :align="align"
        :side-offset="sideOffset"
        data-test="ds-menu"
      >
        <template v-for="(item, idx) in items" :key="idx">
          <DropdownMenuSeparator v-if="item.separator" class="ds-menu__separator" />

          <DropdownMenuItem
            v-else
            class="ds-menu__item"
            :data-tone="item.tone ?? 'neutral'"
            :disabled="item.disabled"
            data-test="ds-menu-item"
            @select="item.onSelect?.(item)"
          >
            {{ item.label }}
          </DropdownMenuItem>
        </template>
      </DropdownMenuContent>
    </DropdownMenuPortal>
  </DropdownMenuRoot>
</template>

<style>
.ds-menu {
  z-index: var(--ds-z-popover);
  min-inline-size: 12rem;
  padding: var(--ds-space-2xs);
  background: var(--ds-color-panel-main-bg);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  box-shadow: var(--ds-shadow-md);
  animation: ds-menu-in var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-menu[data-state='closed'] {
  animation: ds-menu-out var(--ds-duration-instant) var(--ds-ease-in);
}

.ds-menu__item {
  display: flex;
  align-items: center;
  gap: var(--ds-space-sm);
  padding: var(--ds-space-xs) var(--ds-space-sm);
  font-size: var(--ds-font-size-label);
  border-radius: var(--ds-radius-sm);
  color: var(--ds-color-black);
  cursor: pointer;
  user-select: none;
  outline: none;
}
.ds-menu__item[data-highlighted] {
  background: var(--ds-color-light);
}
.ds-menu__item[data-disabled] {
  color: var(--ds-color-placeholder);
  pointer-events: none;
}
.ds-menu__item[data-tone='primary']  { color: var(--ds-color-primary); }
.ds-menu__item[data-tone='primary'][data-highlighted]  { background: var(--ds-color-primary-bg); }
.ds-menu__item[data-tone='danger']  { color: var(--ds-color-error); }
.ds-menu__item[data-tone='danger'][data-highlighted]  { background: var(--ds-color-error-bg); }

.ds-menu__separator {
  block-size: 1px;
  margin: var(--ds-space-2xs) 0;
  background: var(--ds-color-border);
}

</style>
