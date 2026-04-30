<template>
  <div class="km-label-value" v-bind="$attrs">
    <div class="cluster pb-xs" data-gap="xs">
      <div class="km-title">{{ value }}</div>
      <div class="km-description text-text-weak">{{ label }}</div>
      <km-glyph v-if="tooltip" class="flex-none" name="info">
        <km-tooltip class="bg-white block-shadow km-description" self="top middle" :offset="[-50, -50]">
          <div class="text-secondary-text">{{ tooltip }}</div>
        </km-tooltip>
      </km-glyph>
    </div>
  </div>
</template>
<script>
import { m } from '@/paraglide/messages'
export default {
  props: {
    label: {
      type: String,
    },
    value: {
      type: String,
    },
    tooltip: {
      type: String,
    },
  },
}
</script>
