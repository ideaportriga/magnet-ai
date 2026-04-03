<template lang="pug">
template(v-if='span?.input')
  .col-auto.ba-border.border-radius-8
    .row.bb-border.q-pa-sm.bg-light.km-body-sm Text
    .row.q-pa-sm.km-body-sm(style='min-height: 30px; white-space: pre-wrap') {{ span?.input }}
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
