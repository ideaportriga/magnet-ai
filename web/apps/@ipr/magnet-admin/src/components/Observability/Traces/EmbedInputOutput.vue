<template>
  <template v-if="span?.input">
    <div class="flex-none ba-border border-radius-8">
      <div class="cluster bb-border p-sm bg-light km-body-sm">Text</div>
      <div class="cluster p-sm km-body-sm" style="min-block-size: 30px; white-space: pre-wrap">{{ span?.input }}</div>
    </div>
  </template>
</template>

<script>
import { m } from '@/paraglide/messages'
export default {
  props: {
    span: {
      type: Object,
      default: () => null,
    },
  },
}
</script>
