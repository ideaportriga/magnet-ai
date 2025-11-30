<template lang="pug">
q-dialog(:model-value='modal', @hide='$emit("update:modal", false)')
  q-card.bg-white.q-px-32.q-pb-32.q-pt-40(
    style='width: 400px; max-width: 400px; border-radius: 8px; --'
  )
    .row.right-flex(style='position: absolute; right: 16px; top: 13px')
      q-btn(icon='fas fa-times', text-color='blue-grey-3', flat, round, dense, v-close-popup)
    .column.q-gap-8
      .km-title Please help us improve the answers!
      .q-pb-24
        .km-paragraph Why were you not happy with the answer?

      q-option-group.filter-list-chipped(
        v-model="reason"
        :options="reasonsList"
        type="radio"
        color="primary"
      )

      .q-py-24
        .km-heading.q-px-8.q-px-2.q-mb-xs Comment
        km-input.search-prompt-input(
          rounded,
          outlined,
          autogrow,
          bg-color='background',
          placeholder='How could we improve the answer?',
          :model-value='comment',
          @update:modelValue='comment = $event'
        )
      .row.right-flex.q-gap-16
        km-btn(
          label='Send feedback',
          @click='submit()'
        )
</template>

<script lang="ts">
import { ref } from 'vue'

export default {
  props: ['modal'],
  emits: ['onSubmit', 'update:modal'],
  setup() {
    const comment = ref('')

    const reason = ref()
    const reasonsList = ref([
      { label: 'It isn’t relevant', value: 'not_relevant' },
      { label: 'It isn’t correct', value: 'inaccurate' },
      { label: 'It’s outdated', value: 'outdated' },
    ])
    return {
      reasonsList,
      reason,
      comment,
    }
  },
  computed: {},
  watch: {},
  created() {},
  mounted() {},
  methods: {
    submit() {
      this.$emit('onSubmit', { type: 'dislike', reason: this.reason, comment: this.comment })
      this.$emit('update:modal', false)
      this.comment = ''
      this.reason = []
    },
  },
}
</script>

<style lang="stylus"></style>
