<template lang="pug">
q-dialog(:model-value='feedbackConfirmModal')
  q-card.bg-white.q-px-32.q-pb-32.q-pt-40(style='width: 400px; max-width: 400px; border-radius: 8px')
    .row.right-flex(style='position: absolute; right: 16px; top: 13px')
      q-btn(icon='fas fa-times', text-color='blue-grey-3', flat, round, dense, v-close-popup)
    .column.q-gap-8
      .col-12
        .km-title Thank you!
      .col-12.q-pb-24
        .km-paragraph Your feedback will help us generate better answers.
      .row.right-flex.q-gap-16
        km-btn(label='Close', @click='$emit("update:feedbackConfirmModal", false)')
q-dialog(:model-value='feedbackModal')
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
        type="checkbox"
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
          @click='$emit("submit", { reason, comment })'
        )
</template>

<script>
import { ref } from 'vue'
export default {
  props: {
    feedbackModal: {
      type: Boolean,
      default: false,
    },
    feedbackConfirmModal: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['update:feedbackModal', 'update:feedbackConfirmModal', 'submit'],
  setup() {
    const reason = ref([])
    const reasonsList = ref([
      { label: 'It isn’t relevant', value: 'It isn’t relevant' },
      { label: 'It isn’t correct', value: 'It isn’t correct' },
    ])
    const comment = ref('')
    return {
      reason,
      reasonsList,
      comment,
    }
  },
}
</script>
