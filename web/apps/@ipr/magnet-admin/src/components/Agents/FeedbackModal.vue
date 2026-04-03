<template lang="pug">
q-dialog(:model-value='feedbackConfirmModal')
  q-card.bg-white.q-px-32.q-pb-32.q-pt-40(style='width: 400px; max-width: 400px; border-radius: 8px')
    .row.right-flex(style='position: absolute; right: 16px; top: 13px')
      q-btn(icon='fas fa-times', text-color='blue-grey-3', flat, round, dense, v-close-popup)
    .column.q-gap-8
      .col-12
        .km-title {{ m.feedback_thankYou() }}
      .col-12.q-pb-24
        .km-paragraph {{ m.feedback_willHelpImprove() }}
      .row.right-flex.q-gap-16
        km-btn(:label='m.common_close()', @click='$emit("update:feedbackConfirmModal", false)')
q-dialog(:model-value='feedbackModal')
  q-card.bg-white.q-px-32.q-pb-32.q-pt-40(
    style='width: 400px; max-width: 400px; border-radius: 8px; --'
  )
    .row.right-flex(style='position: absolute; right: 16px; top: 13px')
      q-btn(icon='fas fa-times', text-color='blue-grey-3', flat, round, dense, v-close-popup)
    .column.q-gap-8
      .km-title {{ m.feedback_pleaseHelp() }}
      .q-pb-24
        .km-paragraph {{ m.feedback_whyNotHappy() }}

      q-option-group.filter-list-chipped(
        v-model="reason"
        :options="reasonsList"
        type="checkbox"
        color="primary"
      )

      .q-py-24
        .km-heading.q-px-8.q-px-2.q-mb-xs {{ m.feedback_comment() }}
        km-input.search-prompt-input(
          rounded,
          outlined,
          autogrow,
          bg-color='background',
          :placeholder='m.placeholder_howToImproveAnswer()',
          :model-value='comment',
          @update:modelValue='comment = $event'
        )
      .row.right-flex.q-gap-16
        km-btn(
          :label='m.feedback_sendFeedback()',
          @click='$emit("submit", { reason, comment })'
        )
</template>

<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
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
      { label: m.feedback_notRelevant(), value: "It isn't relevant" },
      { label: m.feedback_notCorrect(), value: "It isn't correct" },
    ])
    const comment = ref('')
    return {
      m,
      reason,
      reasonsList,
      comment,
    }
  },
}
</script>
