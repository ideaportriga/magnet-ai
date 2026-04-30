<script setup lang="ts">
/**
 * AspectRatio — preserves a ratio for embedded content (images, video, iframes).
 *
 *   <DsAspectRatio :ratio="16 / 9">
 *     <img src="..." alt="..." />
 *   </DsAspectRatio>
 */

import { AspectRatio, type AspectRatioProps } from 'reka-ui'

const props = defineProps<AspectRatioProps>()
</script>

<template>
  <AspectRatio
    v-slot="slotProps"
    v-bind="props"
    class="ds-aspect-ratio"
    data-test="ds-aspect-ratio"
  >
    <slot v-bind="slotProps" />
  </AspectRatio>
</template>

<style>
.ds-aspect-ratio {
  display: block;
  inline-size: 100%;
  overflow: hidden;
}
.ds-aspect-ratio > img,
.ds-aspect-ratio > video,
.ds-aspect-ratio > iframe {
  inline-size: 100%;
  block-size: 100%;
  object-fit: cover;
}
</style>
