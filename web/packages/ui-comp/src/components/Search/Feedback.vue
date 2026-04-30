<script setup lang="ts">
/**
 * "Why was this answer bad?" feedback dialog. Rewritten on `@ds`.
 */

import { computed, ref } from 'vue'
import { DsDialog, DsRadioGroup } from '@ds/primitives'
import KmBtn from '@ds/components/domain/KmBtn.vue'
import KmInput from '@ds/components/domain/KmInput.vue'

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

const modal = defineModel<boolean>('modal')
const props = defineProps<{
  t?: Record<string, string>
}>()

const emit = defineEmits<{
  onSubmit: [payload: { type: 'dislike'; reason: string; comment: string }]
}>()

const reason = ref('')
const comment = ref('')

const mergedT = computed(() => ({ ...DEFAULT_T, ...(props.t ?? {}) }))

const reasonsList = computed(() => [
  { value: 'not_relevant', label: mergedT.value.reasonNotRelevant },
  { value: 'inaccurate', label: mergedT.value.reasonNotCorrect },
  { value: 'outdated', label: mergedT.value.reasonOutdated },
])

function submit() {
  emit('onSubmit', { type: 'dislike', reason: reason.value, comment: comment.value })
  modal.value = false
  comment.value = ''
  reason.value = ''
}
</script>

<template>
  <DsDialog v-model:open="modal" size="sm">
    <template #title>{{ mergedT.title }}</template>

    <div class="search-feedback stack" data-gap="lg">
      <p class="search-feedback__subtitle">{{ mergedT.subtitle }}</p>

      <DsRadioGroup v-model="reason" :options="reasonsList" />

      <div class="stack" data-gap="2xs">
        <span class="search-feedback__label">{{ mergedT.commentLabel }}</span>
        <KmInput v-model="comment" autogrow rounded :placeholder="mergedT.commentPlaceholder" />
      </div>
    </div>

    <template #footer>
      <KmBtn :label="mergedT.sendFeedback" @click="submit" />
    </template>
  </DsDialog>
</template>

<style scoped>
.search-feedback__subtitle { font-size: var(--ds-font-size-body); margin: 0; }
.search-feedback__label {
  font-size: var(--ds-font-size-caption);
  font-weight: var(--ds-font-weight-medium);
  color: var(--ds-color-label);
}
</style>
