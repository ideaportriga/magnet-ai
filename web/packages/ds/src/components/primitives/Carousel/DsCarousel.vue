<script setup lang="ts">
/**
 * Carousel — embla-carousel-vue based slider primitive.
 *
 *   <DsCarousel>
 *     <DsCarouselContent>
 *       <DsCarouselItem v-for="i in items" :key="i.id">...</DsCarouselItem>
 *     </DsCarouselContent>
 *     <DsCarouselPrevious />
 *     <DsCarouselNext />
 *   </DsCarousel>
 */

import type { CarouselEmits, CarouselProps } from './useCarousel'
import { useProvideCarousel } from './useCarousel'

const props = withDefaults(defineProps<CarouselProps>(), {
  orientation: 'horizontal',
})

const emits = defineEmits<CarouselEmits>()

const {
  canScrollNext,
  canScrollPrev,
  carouselApi,
  carouselRef,
  orientation,
  scrollNext,
  scrollPrev,
} = useProvideCarousel(props, emits)

defineExpose({
  canScrollNext,
  canScrollPrev,
  carouselApi,
  carouselRef,
  orientation,
  scrollNext,
  scrollPrev,
})

function onKeyDown(event: KeyboardEvent) {
  const prevKey = props.orientation === 'vertical' ? 'ArrowUp' : 'ArrowLeft'
  const nextKey = props.orientation === 'vertical' ? 'ArrowDown' : 'ArrowRight'

  if (event.key === prevKey) {
    event.preventDefault()
    scrollPrev()
    return
  }

  if (event.key === nextKey) {
    event.preventDefault()
    scrollNext()
  }
}
</script>

<template>
  <div
    class="ds-carousel"
    :data-orientation="orientation"
    data-test="ds-carousel"
    role="region"
    aria-roledescription="carousel"
    tabindex="0"
    @keydown="onKeyDown"
  >
    <slot
      :can-scroll-next="canScrollNext"
      :can-scroll-prev="canScrollPrev"
      :carousel-api="carouselApi"
      :carousel-ref="carouselRef"
      :orientation="orientation"
      :scroll-next="scrollNext"
      :scroll-prev="scrollPrev"
    />
  </div>
</template>

<style>
.ds-carousel {
  position: relative;
}
.ds-carousel:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}
</style>
