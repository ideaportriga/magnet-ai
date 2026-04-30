<script setup lang="ts">
/**
 * InputGroupAddon — leading / trailing slot inside a `DsInputGroup`. Click
 * focuses the sibling input automatically (unless the click landed on a
 * button).
 */

export type DsInputGroupAddonAlign =
  | 'inline-start'
  | 'inline-end'
  | 'block-start'
  | 'block-end'

withDefaults(
  defineProps<{
    align?: DsInputGroupAddonAlign
  }>(),
  {
    align: 'inline-start',
  },
)

function handleAddonClick(e: MouseEvent) {
  const currentTarget = e.currentTarget as HTMLElement | null
  const target = e.target as HTMLElement | null
  if (target && target.closest('button')) return
  currentTarget?.parentElement?.querySelector('input')?.focus()
}
</script>

<template>
  <div
    role="group"
    class="ds-input-group__addon"
    :data-align="align"
    data-test="ds-input-group-addon"
    @click="handleAddonClick"
  >
    <slot />
  </div>
</template>

<style>
.ds-input-group__addon {
  display: flex;
  block-size: auto;
  align-items: center;
  justify-content: center;
  gap: var(--ds-space-sm);
  cursor: text;
  user-select: none;
  padding-block: var(--ds-space-xs);
  color: var(--ds-color-text-grey);
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
}
.ds-input-group__addon > svg {
  inline-size: 16px;
  block-size: 16px;
  flex: none;
}
.ds-input-group[aria-disabled='true'] .ds-input-group__addon,
.ds-input-group:has([data-disabled='true']) .ds-input-group__addon {
  opacity: 0.5;
}

.ds-input-group__addon[data-align='inline-start'] {
  order: -1;
  padding-inline-start: var(--ds-space-md);
}
.ds-input-group__addon[data-align='inline-end'] {
  order: 1;
  padding-inline-end: var(--ds-space-md);
}
.ds-input-group__addon[data-align='block-start'] {
  order: -1;
  inline-size: 100%;
  justify-content: flex-start;
  padding-inline: var(--ds-space-md);
  padding-block-start: var(--ds-space-md);
}
.ds-input-group__addon[data-align='block-end'] {
  order: 1;
  inline-size: 100%;
  justify-content: flex-start;
  padding-inline: var(--ds-space-md);
  padding-block-end: var(--ds-space-md);
}
</style>
