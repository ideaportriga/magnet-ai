<template lang="pug">
template(v-if='span?.input')
  .col-auto.ba-border.border-radius-8
    .row.bb-border.q-pa-sm.bg-light(style='font-size: 13px') Text
    .row.q-pa-sm(style='min-height: 30px; font-size: 13px; white-space: pre-wrap') {{ span?.input }}
</template>

<script>
export default {
  props: {
    span: {
      type: Object,
      default: () => null,
    },
  },
}
</script>
