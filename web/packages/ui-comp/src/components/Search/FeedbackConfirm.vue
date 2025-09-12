<template lang="pug">
q-dialog(:model-value='modal', @hide='$emit("update:modal", false)')
  q-card.bg-white.q-px-32.q-pb-32.q-pt-40(style='width: 400px; max-width: 400px; border-radius: 8px')
    .row.right-flex(style='position: absolute; right: 16px; top: 13px')
      q-btn(icon='fas fa-times', text-color='blue-grey-3', flat, round, dense, v-close-popup)
    .column.q-gap-8
      .col-12
        .km-title Thank you!
      .col-12.q-pb-24
        .km-paragraph Your feedback will help us generate better answers.
      .row.right-flex.q-gap-16
        km-btn(label='Close', @click='$emit("update:modal", false)')
</template>

<script lang="ts">
export default {
  props: ['modal'],
  emits: ['update:modal'],
  setup() {
    return {}
  },
  computed: {},
  watch: {},
  created() {},
  mounted() {},
  methods: {},
}
</script>

<style lang="stylus"></style>
