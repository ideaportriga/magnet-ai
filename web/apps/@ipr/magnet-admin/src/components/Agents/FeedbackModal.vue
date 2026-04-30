<template>
  <km-dialog :model-value="feedbackConfirmModal">
    <km-card class="bg-white px-3xl pb-3xl pt-4xl feedback-modal__card">
      <div class="cluster feedback-modal__close" data-justify="end">
        <km-btn icon="close" flat round dense @click="$emit(&quot;update:feedbackConfirmModal&quot;, false)" />
      </div>
      <div class="stack" data-gap="sm">
        <div>
          <div class="km-title">{{ m.feedback_thankYou() }}</div>
        </div>
        <div class="pb-2xl">
          <div class="km-paragraph">{{ m.feedback_willHelpImprove() }}</div>
        </div>
        <div class="cluster" data-gap="lg" data-justify="end">
          <km-btn :label="m.common_close()" @click="$emit(&quot;update:feedbackConfirmModal&quot;, false)" />
        </div>
      </div>
    </km-card>
  </km-dialog>
  <km-dialog :model-value="feedbackModal">
    <km-card class="bg-white px-3xl pb-3xl pt-4xl feedback-modal__card">
      <div class="cluster feedback-modal__close" data-justify="end">
        <km-btn icon="close" flat round dense @click="$emit(&quot;update:feedbackModal&quot;, false)" />
      </div>
      <div class="stack" data-gap="sm">
        <div class="km-title">{{ m.feedback_pleaseHelp() }}</div>
        <div class="pb-2xl">
          <div class="km-paragraph">{{ m.feedback_whyNotHappy() }}</div>
        </div>
        <km-option-group v-model="reason" class="filter-list-chipped" :options="reasonsList" type="checkbox" />
        <div class="py-2xl">
          <div class="km-heading px-sm px-2xs mb-xs">{{ m.feedback_comment() }}</div>
          <km-input class="search-prompt-input" rounded outlined autogrow :placeholder="m.placeholder_howToImproveAnswer()" :model-value="comment" @update:model-value="comment = $event" />
        </div>
        <div class="cluster" data-gap="lg" data-justify="end">
          <km-btn :label="m.feedback_sendFeedback()" @click="$emit(&quot;submit&quot;, { reason, comment })" />
        </div>
      </div>
    </km-card>
  </km-dialog>
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

<style scoped>
.feedback-modal__card {
  inline-size: 400px;
  max-inline-size: 400px;
  border-radius: var(--ds-radius-lg);
}
.feedback-modal__close {
  position: absolute;
  inset-inline-end: var(--ds-space-lg);
  inset-block-start: var(--ds-space-md);
}
</style>
