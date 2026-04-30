<script setup lang="ts">
import { useCarousel } from './useCarousel'

defineOptions({
  inheritAttrs: false,
})

const { carouselRef, orientation } = useCarousel()
</script>

<template>
  <div
    ref="carouselRef"
    class="ds-carousel__viewport"
    data-test="ds-carousel-content"
  >
    <div
      class="ds-carousel__track"
      :data-orientation="orientation"
      v-bind="$attrs"
    >
      <slot />
    </div>
  </div>
</template>

<style>
.ds-carousel__viewport {
  overflow: hidden;
}
.ds-carousel__track {
  display: flex;
}
.ds-carousel__track[data-orientation='horizontal'] {
  margin-inline-start: calc(-1 * var(--ds-space-lg));
}
.ds-carousel__track[data-orientation='vertical'] {
  flex-direction: column;
  margin-block-start: calc(-1 * var(--ds-space-lg));
}
</style>
