<script setup lang="ts">
/**
 * InputGroupButton — compact button optimised for use inside a
 * `DsInputGroupAddon`. Defaults to a ghost variant and `xs` height.
 */

import DsButton, {
  type DsButtonVariant,
} from '../Button/DsButton.vue'

export type DsInputGroupButtonSize = 'xs' | 'sm' | 'icon-xs' | 'icon-sm'

withDefaults(
  defineProps<{
    variant?: DsButtonVariant
    size?: DsInputGroupButtonSize
  }>(),
  {
    variant: 'ghost',
    size: 'xs',
  },
)
</script>

<template>
  <DsButton
    class="ds-input-group__button"
    :variant="variant"
    :data-size="size"
    data-test="ds-input-group-button"
  >
    <slot />
  </DsButton>
</template>

<style>
.ds-input-group__button {
  box-shadow: none;
  font-size: var(--ds-font-size-label);
  gap: var(--ds-space-xs);
}

.ds-input-group__button[data-size='xs'] {
  block-size: 24px;
  inline-size: auto;
  padding-inline: var(--ds-space-sm);
  border-radius: var(--ds-radius-sm);
  gap: var(--ds-space-2xs);
}
.ds-input-group__button[data-size='xs'] > svg {
  inline-size: 14px;
  block-size: 14px;
}

.ds-input-group__button[data-size='sm'] {
  block-size: 32px;
  inline-size: auto;
  padding-inline: var(--ds-space-sm);
  border-radius: var(--ds-radius-md);
  gap: var(--ds-space-xs);
}

.ds-input-group__button[data-size='icon-xs'] {
  inline-size: 24px;
  block-size: 24px;
  padding: 0;
  border-radius: var(--ds-radius-sm);
}
.ds-input-group__button[data-size='icon-sm'] {
  inline-size: 32px;
  block-size: 32px;
  padding: 0;
  border-radius: var(--ds-radius-md);
}
</style>
