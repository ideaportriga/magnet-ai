<script setup lang="ts">
/**
 * Thank-you confirmation dialog after the user submits feedback. Rewritten
 * on `@ds`.
 */

import { computed } from 'vue'
import { DsDialog } from '@ds/primitives'
import KmBtn from '@ds/components/domain/KmBtn.vue'

const DEFAULT_T = {
  title: 'Thank you!',
  description: 'Your feedback will help us generate better answers.',
  close: 'Close',
}

const modal = defineModel<boolean>('modal')
const props = defineProps<{ t?: Record<string, string> }>()
const mergedT = computed(() => ({ ...DEFAULT_T, ...(props.t ?? {}) }))
</script>

<template>
  <DsDialog v-model:open="modal" size="sm">
    <template #title>{{ mergedT.title }}</template>
    <p class="search-feedback-confirm__text">{{ mergedT.description }}</p>
    <template #footer>
      <KmBtn :label="mergedT.close" @click="modal = false" />
    </template>
  </DsDialog>
</template>

<style scoped>
.search-feedback-confirm__text { font-size: var(--ds-font-size-body); margin: 0; }
</style>
