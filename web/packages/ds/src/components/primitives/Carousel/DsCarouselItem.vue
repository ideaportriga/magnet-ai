<script setup lang="ts">
import { useCarousel } from './useCarousel'

const { orientation } = useCarousel()
</script>

<template>
  <div
    class="ds-carousel__item"
    :data-orientation="orientation"
    data-test="ds-carousel-item"
    role="group"
    aria-roledescription="slide"
  >
    <slot />
  </div>
</template>

<style>
.ds-carousel__item {
  min-inline-size: 0;
  flex: 0 0 100%;
}
.ds-carousel__item[data-orientation='horizontal'] {
  padding-inline-start: var(--ds-space-lg);
}
.ds-carousel__item[data-orientation='vertical'] {
  padding-block-start: var(--ds-space-lg);
}
</style>
