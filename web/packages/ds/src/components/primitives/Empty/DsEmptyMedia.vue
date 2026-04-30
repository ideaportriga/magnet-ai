<script setup lang="ts">
/**
 * EmptyMedia — illustration / icon slot at the top of the empty state.
 *
 * Variants:
 *   - `default` — transparent, image-style content
 *   - `icon`    — rounded square chip for an SVG icon
 */

export type DsEmptyMediaVariant = 'default' | 'icon'

withDefaults(
  defineProps<{
    variant?: DsEmptyMediaVariant
  }>(),
  {
    variant: 'default',
  },
)
</script>

<template>
  <div
    class="ds-empty__media"
    :data-variant="variant"
    data-test="ds-empty-media"
  >
    <slot />
  </div>
</template>

<style>
.ds-empty__media {
  display: flex;
  flex: none;
  align-items: center;
  justify-content: center;
  gap: var(--ds-space-sm);
  margin-block-end: var(--ds-space-xs);
  background: transparent;
}
.ds-empty__media > svg {
  pointer-events: none;
  flex: none;
}

.ds-empty__media[data-variant='icon'] {
  inline-size: 40px;
  block-size: 40px;
  background: var(--ds-color-light);
  color: var(--ds-color-black);
  border-radius: var(--ds-radius-lg);
}
.ds-empty__media[data-variant='icon'] > svg {
  inline-size: 24px;
  block-size: 24px;
}
</style>
