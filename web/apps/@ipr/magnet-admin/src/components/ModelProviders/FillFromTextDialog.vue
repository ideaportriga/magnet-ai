<template lang="pug">
q-dialog(v-model='open', persistent)
  q-card.fill-dialog.column.no-wrap
    q-card-section.row.items-center.q-pb-none
      .km-heading-7 {{ step === 'review' ? 'Review Model Info' : 'Update Models From Docs' }}
      q-space
      q-btn(icon='close', flat, round, dense, :disable='applying', @click='open = false')

    q-card-section.fill-dialog__body.scroll
      .column.q-gap-16(v-show='step === "paste"', data-test='fill-from-text-paste')
        .column.q-gap-4
          span.fill-dialog__section-title Selected models
          .row.q-gap-4
            q-chip.q-ma-none(v-for='row in models', :key='row.id', dense) {{ row.display_name || row.ai_model || '' }}
        .km-description.text-secondary-text
          | Paste docs or pricing pages that describe the selected models. Each model is matched by name, and you review the results before anything is saved.
        model-source-blocks(v-model='fill.blocks.value')

      .column.q-gap-16(v-if='step === "review"', data-test='fill-from-text-review')
        .km-description.text-secondary-text Choose what to apply to each model. Models that are not in the text stay unchanged.
        extraction-review(multiple, :entries='fill.entries.value', :sources='fill.resultSources.value')

    q-card-actions.q-pa-md(align='right')
      km-btn(v-if='step === "review"', flat, label='Back', data-test='back-btn', :disable='applying', @click='step = "paste"')
      km-btn(v-else, flat, label='Cancel', data-test='cancel-btn', @click='open = false')
      km-btn(
        :label='step === "review" ? `Apply (${patchCount})` : "Apply"',
        data-test='fill-from-text-apply',
        :disable='step === "paste" ? !fill.hasText.value || fill.overLimit.value : patchCount === 0',
        :loading='applying || fill.isExtracting.value',
        @click='onApply'
      )
</template>

<script setup lang="ts">
/**
 * Bulk "Update From Docs" for the models selected in the list (#466).
 *
 * Two steps in one dialog: paste the docs / pricing pages, then Apply reads
 * them and switches to the review, where each model found in the text gets
 * its own pricing pick. Apply there PATCHes only the models with something
 * picked — one request per model, like bulk delete, so a failure on one row
 * doesn't hide the rows that were updated.
 */
import { computed, ref } from 'vue'
import { useStore } from 'vuex'

import ExtractionReview from './ExtractionReview.vue'
import ModelSourceBlocks from './ModelSourceBlocks.vue'
import type { FillTarget } from './modelTextFill'
import { useModelNotify } from './notifyModels'
import { useModelTextFill } from './useModelTextFill'

interface ModelRow {
  id: string
  ai_model?: string | null
  display_name?: string | null
  type?: string | null
  configs?: Record<string, unknown> | null
}

const props = defineProps<{
  modelValue: boolean
  models: ModelRow[]
  provider?: string | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', open: boolean): void
  (e: 'applied', updatedIds: string[]): void
}>()

const store = useStore()
const notify = useModelNotify()

const step = ref<'paste' | 'review'>('paste')
const applying = ref(false)

const open = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const targets = computed<FillTarget[]>(() =>
  props.models.map((row) => ({
    key: row.id,
    ai_model: row.ai_model ?? '',
    display_name: row.display_name ?? null,
    type: row.type ?? null,
    configs: row.configs ?? null,
  }))
)

const fill = useModelTextFill(
  targets,
  computed(() => props.provider ?? null)
)

const patchCount = computed(() => Object.keys(fill.patches.value).length)

async function onApply() {
  if (step.value === 'paste') {
    if (await fill.extract()) step.value = 'review'
    return
  }
  if (patchCount.value === 0) return
  applying.value = true
  const updated: string[] = []
  let failed = 0
  try {
    for (const [id, data] of Object.entries(fill.patches.value)) {
      // `chroma/update` reports failure as `false` and refetches the list on success.
      const ok = await store.dispatch('chroma/update', { payload: { id, data: JSON.stringify(data) }, entity: 'model' })
      if (ok) updated.push(id)
      else failed++
    }
  } finally {
    applying.value = false
  }
  if (updated.length > 0) notify('success', `${updated.length} model(s) updated.`)
  if (failed > 0) notify('warning', `Failed to update ${failed} model(s).`)
  emit('applied', updated)
  open.value = false
}
</script>

<style scoped>
.fill-dialog {
  inline-size: 900px;
  max-inline-size: 90vw;
  max-block-size: 85vh;
}
.fill-dialog__body {
  flex: 1;
  min-block-size: 0;
}
.fill-dialog__section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--q-secondary-text);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
</style>
