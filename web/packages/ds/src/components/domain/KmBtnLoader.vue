<script setup lang="ts">
/**
 * `<km-btn-loader>` — button + inline spinner. The legacy component looks
 * the same as a regular Btn but the `loading` prop is sticky; the button is
 * disabled while loading is true.
 */

import KmBtn from './KmBtn.vue'
import type { KmBtnTone } from './KmBtn.vue'

withDefaults(
  defineProps<{
    label?: string
    loading?: boolean
    disable?: boolean
    icon?: string
    svgIcon?: string
    tone?: KmBtnTone
  }>(),
  {
    loading: false,
    disable: false,
  },
)

defineEmits<{ click: [Event] }>()
</script>

<template>
  <KmBtn
    :label="label"
    :loading="loading"
    :disable="disable || loading"
    :icon="icon"
    :svg-icon="svgIcon"
    :tone="tone"
    data-test="km-btn-loader"
    @click="$emit('click', $event)"
  />
</template>
