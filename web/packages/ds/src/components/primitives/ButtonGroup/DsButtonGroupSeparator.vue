<script setup lang="ts">
/**
 * ButtonGroupSeparator — visual divider between elements in a `DsButtonGroup`.
 */

import { Separator, type SeparatorProps } from 'reka-ui'

withDefaults(defineProps<SeparatorProps>(), {
  orientation: 'vertical',
  decorative: true,
})
</script>

<template>
  <Separator
    class="ds-button-group__separator"
    :orientation="orientation"
    :decorative="decorative"
    :data-orientation="orientation"
    data-test="ds-button-group-separator"
  />
</template>

<style>
.ds-button-group__separator {
  background: var(--ds-color-border);
  flex: none;
  align-self: stretch;
  margin: 0;
}
.ds-button-group__separator[data-orientation='vertical'] {
  inline-size: 1px;
  block-size: auto;
}
.ds-button-group__separator[data-orientation='horizontal'] {
  block-size: 1px;
  inline-size: auto;
}
</style>
