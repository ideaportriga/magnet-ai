<script setup lang="ts">
/**
 * `<km-background>` — full-bleed background image. The legacy component
 * resolved the URL relative to `$appImagePath`. We respect that contract by
 * reading the global property when available; otherwise the `src` is used
 * as-is (already an absolute URL).
 */

import { computed, getCurrentInstance } from 'vue'

const props = defineProps<{ src: string }>()

const appImagePath = computed<string>(() => {
  const proxy = getCurrentInstance()?.appContext.config.globalProperties as { $appImagePath?: string }
  return proxy?.$appImagePath ?? ''
})

const url = computed(() => {
  if (/^(https?:|data:|\/)/.test(props.src)) return props.src
  return `${appImagePath.value}${props.src}`
})
</script>

<template>
  <div
    class="km-background"
    :style="{ backgroundImage: `url(${url})` }"
    aria-hidden="true"
    data-test="km-background"
  />
</template>

<style>
.km-background {
  position: absolute;
  inset: 0;
  inline-size: 100%;
  block-size: 100%;
  background-position: center;
  background-size: cover;
  background-repeat: no-repeat;
  z-index: var(--ds-z-base);
  pointer-events: none;
}
</style>
