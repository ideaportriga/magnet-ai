<script setup lang="ts">
import DsButton, { type DsButtonSize, type DsButtonVariant } from '../Button/DsButton.vue'
import { useCarousel } from './useCarousel'

withDefaults(
  defineProps<{
    variant?: DsButtonVariant
    size?: DsButtonSize
  }>(),
  {
    variant: 'outline',
    size: 'icon-sm',
  },
)

const { orientation, canScrollPrev, scrollPrev } = useCarousel()
</script>

<template>
  <DsButton
    class="ds-carousel__prev"
    :data-orientation="orientation"
    data-test="ds-carousel-previous"
    :variant="variant"
    :size="size"
    :disabled="!canScrollPrev"
    @click="scrollPrev"
  >
    <slot>
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        aria-hidden="true"
      >
        <path
          d="M10 3 L5 8 L10 13"
          stroke="currentColor"
          stroke-width="1.6"
          fill="none"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
      <span class="ds-carousel__sr">Previous slide</span>
    </slot>
  </DsButton>
</template>

<style>
.ds-carousel__prev {
  position: absolute;
  border-radius: var(--ds-radius-full);
}
.ds-carousel__prev[data-orientation='horizontal'] {
  inset-block-start: 50%;
  inset-inline-start: calc(-1 * var(--ds-space-3xl));
  transform: translateY(-50%);
}
.ds-carousel__prev[data-orientation='vertical'] {
  inset-block-start: calc(-1 * var(--ds-space-3xl));
  inset-inline-start: 50%;
  transform: translateX(-50%) rotate(90deg);
}
.ds-carousel__sr {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
}
</style>
