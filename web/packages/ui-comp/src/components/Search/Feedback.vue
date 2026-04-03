<template lang="pug">
q-dialog(:model-value='modal', @hide='$emit("update:modal", false)')
  q-card.bg-white.q-px-32.q-pb-32.q-pt-40(
    style='width: 400px; max-width: 400px; border-radius: 8px; --'
  )
    .row.right-flex(style='position: absolute; right: 16px; top: 13px')
      q-btn(icon='fas fa-times', text-color='blue-grey-3', flat, round, dense, v-close-popup)
    .column.q-gap-8
      .km-title {{ mergedT.title }}
      .q-pb-24
        .km-paragraph {{ mergedT.subtitle }}

      q-option-group.filter-list-chipped(
        v-model="reason"
        :options="reasonsList"
        type="radio"
        color="primary"
      )

      .q-py-24
        .km-heading.q-px-8.q-px-2.q-mb-xs {{ mergedT.commentLabel }}
        km-input.search-prompt-input(
          rounded,
          outlined,
          autogrow,
          bg-color='background',
          :placeholder='mergedT.commentPlaceholder',
          :model-value='comment',
          @update:modelValue='comment = $event'
        )
      .row.right-flex.q-gap-16
        km-btn(
          :label='mergedT.sendFeedback',
          @click='submit()'
        )
</template>

<script lang="ts">
import { ref } from 'vue'

const DEFAULT_T = {
  title: 'Please help us improve the answers!',
  subtitle: 'Why were you not happy with the answer?',
  commentLabel: 'Comment',
  commentPlaceholder: 'How could we improve the answer?',
  sendFeedback: 'Send feedback',
  reasonNotRelevant: "It isn't relevant",
  reasonNotCorrect: "It isn't correct",
  reasonOutdated: "It's outdated",
}

export default {
  props: {
    modal: {},
    t: {
      type: Object,
      default: () => ({}),
    },
  },
  emits: ['onSubmit', 'update:modal'],
  setup() {
    const comment = ref('')

    const reason = ref()
    return {
      reason,
      comment,
    }
  },
  computed: {
    mergedT() {
      return { ...DEFAULT_T, ...this.t }
    },
    reasonsList() {
      return [
        { label: this.mergedT.reasonNotRelevant, value: 'not_relevant' },
        { label: this.mergedT.reasonNotCorrect, value: 'inaccurate' },
        { label: this.mergedT.reasonOutdated, value: 'outdated' },
      ]
    },
  },
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
