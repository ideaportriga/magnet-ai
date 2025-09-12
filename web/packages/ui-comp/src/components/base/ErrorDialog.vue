<template lang="pug">
q-dialog(position='top', v-model='value', persistent, square, @hide='clearError')
  .q-mt-none.bg-red.text-white(style='width: 640px; border-radius: 0px 0px 8px 8px !important')
    .row.bg-red.q-px-md.q-py-sm.items-center(style='height: 48px')
      q-icon.q-mr-sm(name='error_outline', size='28px')
      .col
        .km-heading-6 Error
      q-btn(icon='close', flat, round, dense, v-close-popup)
    .column.q-px-lg.q-py-sm
      .q-my-xs.km-body(v-if='!text && !technicalError') Unknown Error
      .q-my-xs.km-body(v-if='text') {{ errorMessage?.text }}
      .q-mt-sm.q-mb-xs.km-chip(v-if='technicalError') {{ errorMessage?.technicalError }}
      //- .q-my-xs(v-if="showDisclaimer")
      .q-mt-md.q-mb-sm.self-end
        div
          q-btn(color='white', v-close-popup, flat) Ok
</template>

<script>
import { ref } from 'vue'
export default {
  setup() {
    return {
      value: ref(true),
    }
  },
  computed: {
    errorMessage() {
      return this.$store.getters.errorMessage ?? {}
    },
    technicalError() {
      return this.errorMessage?.technicalError ?? ''
    },
    text() {
      return this.errorMessage?.text ?? ''
    },
  },
  methods: {
    close() {
      // this.value = false
      // this.$nextTick()
    },
    clearError() {
      this.$store.commit('set', { errorMessage: {} })
    },
  },
}
</script>

<style lang="stylus" scoped></style>
