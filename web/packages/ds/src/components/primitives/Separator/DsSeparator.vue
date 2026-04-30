<script setup lang="ts">
/**
 * Separator — accessible divider. Use as a self-closing element.
 *
 *   <DsSeparator />                                // horizontal
 *   <DsSeparator orientation="vertical" />
 */

import { Separator } from 'reka-ui'

withDefaults(
  defineProps<{
    orientation?: 'horizontal' | 'vertical'
    /** Render as decorative-only (default) or semantic separator. */
    decorative?: boolean
  }>(),
  {
    orientation: 'horizontal',
    decorative: true,
  },
)
</script>

<template>
  <Separator
    :orientation="orientation"
    :decorative="decorative"
    class="ds-separator"
    :data-orientation="orientation"
    data-test="ds-separator"
  />
</template>

<style>
.ds-separator {
  background: var(--ds-color-border);
  flex: none;
}
.ds-separator[data-orientation='horizontal'] {
  inline-size: 100%;
  block-size: 1px;
}
.ds-separator[data-orientation='vertical'] {
  inline-size: 1px;
  block-size: 100%;
}
</style>
