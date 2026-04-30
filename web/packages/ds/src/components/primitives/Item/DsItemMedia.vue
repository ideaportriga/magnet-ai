<script setup lang="ts">
/**
 * ItemMedia — leading slot for icons, images, or avatars in a `DsItem`.
 *
 * Variants:
 *   - `default` — bare content
 *   - `icon`    — bordered chip sized for an SVG
 *   - `image`   — rounded image container
 */

export type DsItemMediaVariant = 'default' | 'icon' | 'image'

withDefaults(
  defineProps<{
    variant?: DsItemMediaVariant
  }>(),
  {
    variant: 'default',
  },
)
</script>

<template>
  <div
    class="ds-item__media"
    :data-variant="variant"
    data-test="ds-item-media"
  >
    <slot />
  </div>
</template>

<style>
.ds-item__media {
  display: flex;
  flex: none;
  align-items: center;
  justify-content: center;
  gap: var(--ds-space-sm);
  background: transparent;
}
.ds-item__media > svg {
  pointer-events: none;
}

.ds-item__media[data-variant='icon'] {
  inline-size: 32px;
  block-size: 32px;
  background: var(--ds-color-light);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-sm);
}
.ds-item__media[data-variant='icon'] > svg {
  inline-size: 16px;
  block-size: 16px;
}

.ds-item__media[data-variant='image'] {
  inline-size: 40px;
  block-size: 40px;
  border-radius: var(--ds-radius-sm);
  overflow: hidden;
}
.ds-item__media[data-variant='image'] > img {
  inline-size: 100%;
  block-size: 100%;
  object-fit: cover;
}
</style>
