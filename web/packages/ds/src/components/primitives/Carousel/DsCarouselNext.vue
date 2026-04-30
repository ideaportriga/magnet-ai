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

const { orientation, canScrollNext, scrollNext } = useCarousel()
</script>

<template>
  <DsButton
    class="ds-carousel__next"
    :data-orientation="orientation"
    data-test="ds-carousel-next"
    :variant="variant"
    :size="size"
    :disabled="!canScrollNext"
    @click="scrollNext"
  >
    <slot>
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        aria-hidden="true"
      >
        <path
          d="M6 3 L11 8 L6 13"
          stroke="currentColor"
          stroke-width="1.6"
          fill="none"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
      <span class="ds-carousel__sr">Next slide</span>
    </slot>
  </DsButton>
</template>

<style>
.ds-carousel__next {
  position: absolute;
  border-radius: var(--ds-radius-full);
}
.ds-carousel__next[data-orientation='horizontal'] {
  inset-block-start: 50%;
  inset-inline-end: calc(-1 * var(--ds-space-3xl));
  transform: translateY(-50%);
}
.ds-carousel__next[data-orientation='vertical'] {
  inset-block-end: calc(-1 * var(--ds-space-3xl));
  inset-inline-start: 50%;
  transform: translateX(-50%) rotate(90deg);
}
</style>
