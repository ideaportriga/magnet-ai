<script setup lang="ts">
/**
 * Item — flexible row used in lists, menus, settings panels, etc. Compose
 * with `DsItemMedia`, `DsItemContent`, `DsItemTitle`, `DsItemDescription`,
 * `DsItemActions`, `DsItemHeader`, `DsItemFooter`.
 *
 *   <DsItem variant="outline" size="default">
 *     <DsItemMedia variant="icon"><Icon /></DsItemMedia>
 *     <DsItemContent>
 *       <DsItemTitle>Title</DsItemTitle>
 *       <DsItemDescription>Body copy.</DsItemDescription>
 *     </DsItemContent>
 *     <DsItemActions><DsButton size="sm">Edit</DsButton></DsItemActions>
 *   </DsItem>
 */

import { Primitive, type PrimitiveProps } from 'reka-ui'

export type DsItemVariant = 'default' | 'outline' | 'muted'
export type DsItemSize = 'default' | 'sm'

withDefaults(
  defineProps<
    PrimitiveProps & {
      variant?: DsItemVariant
      size?: DsItemSize
    }
  >(),
  {
    as: 'div',
    variant: 'default',
    size: 'default',
  },
)
</script>

<template>
  <Primitive
    class="ds-item"
    :as="as"
    :as-child="asChild"
    :data-variant="variant"
    :data-size="size"
    data-test="ds-item"
  >
    <slot />
  </Primitive>
</template>

<style>
.ds-item {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  border: 1px solid transparent;
  border-radius: var(--ds-radius-md);
  font-family: var(--ds-font-default);
  font-size: var(--ds-font-size-label);
  color: var(--ds-color-black);
  outline: none;
  transition:
    background-color var(--ds-duration-fast) var(--ds-ease-out),
    border-color var(--ds-duration-fast) var(--ds-ease-out);
}
.ds-item:focus-visible {
  border-color: var(--ds-color-primary);
  box-shadow: 0 0 0 3px var(--ds-color-primary-transparent);
}

a.ds-item:hover {
  background: var(--ds-color-accent-bg);
}

/* sizes */
.ds-item[data-size='default'] {
  padding: var(--ds-space-lg);
  gap: var(--ds-space-lg);
}
.ds-item[data-size='sm'] {
  padding-block: var(--ds-space-md);
  padding-inline: var(--ds-space-lg);
  gap: var(--ds-space-md);
}

/* variants */
.ds-item[data-variant='default'] {
  background: transparent;
}
.ds-item[data-variant='outline'] {
  border-color: var(--ds-color-border);
}
.ds-item[data-variant='muted'] {
  background: var(--ds-color-light);
}
</style>
