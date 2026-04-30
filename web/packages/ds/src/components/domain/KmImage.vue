<script setup lang="ts">
/**
 * `<km-image>` — image with `$appImagePath` prefix awareness.
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
  <img :src="url" loading="lazy" data-test="km-image" />
</template>
