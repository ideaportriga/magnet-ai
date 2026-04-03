<template lang="pug">
q-dialog(:model-value='modal', @hide='$emit("update:modal", false)')
  q-card.bg-white.q-px-32.q-pb-32.q-pt-40(style='width: 400px; max-width: 400px; border-radius: 8px')
    .row.right-flex(style='position: absolute; right: 16px; top: 13px')
      q-btn(icon='fas fa-times', text-color='blue-grey-3', flat, round, dense, v-close-popup)
    .column.q-gap-8
      .col-12
        .km-title {{ mergedT.title }}
      .col-12.q-pb-24
        .km-paragraph {{ mergedT.description }}
      .row.right-flex.q-gap-16
        km-btn(:label='mergedT.close', @click='$emit("update:modal", false)')
</template>

<script lang="ts">
const DEFAULT_T = {
  title: 'Thank you!',
  description: 'Your feedback will help us generate better answers.',
  close: 'Close',
}

export default {
  props: {
    modal: {},
    t: {
      type: Object,
      default: () => ({}),
    },
  },
  emits: ['update:modal'],
  setup() {
    return {}
  },
  computed: {
    mergedT() {
      return { ...DEFAULT_T, ...this.t }
    },
  },
  watch: {},
  created() {},
  mounted() {},
  methods: {},
}
</script>

<style lang="stylus"></style>
