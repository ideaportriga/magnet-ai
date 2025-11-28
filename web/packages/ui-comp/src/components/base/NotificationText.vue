<template lang="pug">
q-tooltip.notification.bg-light.row.items-center.text-primary-text.block-shadow(
  v-if='tooltip',
  anchor='top middle',
  self='top middle',
  :offset='[40, 44]'
)
  .col-auto.q-mr-sm
    q-icon(name='o_info', size='20px', color='secondary')
  .col.km-paragraph {{ notification }}

.notification-text.bg-light.row.items-center.text-secondary.q-py-xs(v-else) 
  .col-auto.q-mx-sm
    q-icon.q-my-auto(name='o_info', size='24px', color='secondary')
  .col.km-paragraph
    slot(name='default', v-if='$slots.default')
    | {{ notification }}
</template>

<script>
export default {
  name: 'NotificationText',
  props: {
    notification: {
      type: String,
      default: '',
    },
    tooltip: {
      type: Boolean,
      default: false,
    },
  },
  data() {},
  watch: {},
  methods: {},
}
</script>

<style scoped>
.notification-text {
  color: var(--q-secondary-text) !important;
  height: auto;
  width: 100%;
}
</style>
