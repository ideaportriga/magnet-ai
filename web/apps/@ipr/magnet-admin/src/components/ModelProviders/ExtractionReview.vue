<template lang="pug">
.extraction-review.column.q-gap-16(data-test='extraction-review')
  .km-description.text-secondary-text(v-if='multiple', data-test='extraction-review-summary')
    | Found {{ found.length }} of {{ entries.length }} models in the text.

  q-banner.review-banner(v-else-if='notFound.length', rounded, data-test='extraction-review-not-found')
    template(#avatar)
      q-icon(name='o_warning', color='warning', size='20px')
    | The pasted text doesn't mention this model, so it will be created without extracted info. Go back to check the provider model name.

  q-card.review-model(
    v-for='{ target, result, selection } in found',
    :key='target.key',
    flat,
    bordered,
    :data-state='multiple && !selection.apply ? "skipped" : undefined',
    :data-test='`extraction-review-${target.key}`'
  )
    .review-model__head.row.items-center.justify-between.no-wrap.q-gap-8.q-pa-16
      .review-model__names.column
        span.review-model__name {{ nameOf(target) }}
        span.review-model__id(v-if='target.display_name') {{ target.ai_model }}
      .row.items-center.no-wrap.q-gap-16
        q-chip(dense, color='positive', text-color='white') {{ foundLabel(target, result) }}
        q-toggle(v-if='multiple', v-model='selection.apply', dense, label='Apply', data-test='extraction-review-apply')

    .review-model__skipped(v-if='multiple && !selection.apply') Skipped — this model stays unchanged.

    .review-model__groups(v-else)
      review-group-row(
        v-for='group in reviewGroups(target.type)',
        :key='group',
        v-model='selection.groups[group]',
        :title='GROUP_LABELS[group]',
        :available='hasGroup(result, group, target.type)',
        :data-test='`review-group-${group}`'
      )
        template(v-if='group === "pricing" && result.pricing_options.length > 1', #meta)
          | {{ result.pricing_options.length }} options — pick one

        .review-model__description(v-if='group === "description"') {{ result.description }}

        dl.review-caps(v-else-if='group === "configuration"')
          template(v-for='row in capabilityRows(target.key)', :key='row.key')
            dt.review-caps__label {{ row.label }}
            dd.review-caps__values.row.q-gap-4
              q-chip(v-for='item in row.items', :key='item', dense, :color='CHIP_COLORS[row.tone].color', :text-color='CHIP_COLORS[row.tone].text') {{ item }}

        pricing-options-table(
          v-else,
          v-model='selection.pricingOptionIndex',
          :options='result.pricing_options',
          :sources='sources',
          :disabled='!selection.groups.pricing'
        )

  q-card.review-missing(v-if='multiple && notFound.length', flat, bordered, data-test='extraction-review-not-found')
    .column.q-gap-8.q-pa-16
      .row.items-center.no-wrap.q-gap-4
        q-icon(name='o_warning', color='warning', size='18px')
        span.review-missing__title Not in the text ({{ notFound.length }}) — these models stay unchanged
      .row.q-gap-4
        q-chip(v-for='{ target } in notFound', :key='target.key', dense) {{ nameOf(target) }}
</template>

<script setup lang="ts">
/**
 * Review step of "fill from text" (#466): what the pasted texts said about
 * each model, and what to apply.
 *
 * One card per model found in the text. Its header names the model (and the
 * name the text used, when that differs); in bulk mode it also has the
 * switch that skips the model. Under it, one row per group — description,
 * capabilities, pricing — each with its own switch. A group the text didn't
 * cover keeps its row, marked "Not in the pasted text", so a pricing-only
 * paste reads as "nothing about capabilities" rather than as a missing
 * section. Pricing is a comparison table to pick one option from.
 *
 * Models the text doesn't mention are gathered at the end (bulk) or shown
 * as a notice (new model) — they get nothing applied.
 *
 * Presentational over the `useModelTextFill` state: it mutates the passed
 * selections in place and never calls the API.
 */
import { computed } from 'vue'

import {
  capabilityItems,
  hasGroup,
  isFound,
  isNameMatch,
  reviewGroups,
  type ExtractedModel,
  type FillGroup,
  type FillSelection,
  type FillTarget,
} from './modelTextFill'
import PricingOptionsTable from './PricingOptionsTable.vue'
import ReviewGroupRow from './ReviewGroupRow.vue'
import type { SourceBlock } from './sourceBlocks'

const props = defineProps<{
  entries: { target: FillTarget; result: ExtractedModel; selection: FillSelection }[]
  /** The pasted pages the result was read from; `source` N is `sources[N - 1]`. */
  sources?: SourceBlock[]
  /** Bulk mode: each model can be skipped. */
  multiple?: boolean
}>()

const found = computed(() => props.entries.filter(({ result }) => isFound(result)))
const notFound = computed(() => props.entries.filter(({ result }) => !isFound(result)))

type ChipTone = 'brand' | 'muted' | 'neutral'

interface CapabilityRow {
  key: string
  label: string
  items: string[]
  tone: ChipTone
}

const CHIP_COLORS: Record<ChipTone, { color: string; text: string }> = {
  brand: { color: 'primary', text: 'white' },
  muted: { color: 'grey-3', text: 'grey-7' },
  neutral: { color: 'grey-2', text: 'black' },
}

const FLAG_LABELS: Record<string, string> = {
  json_mode: 'JSON Mode',
  json_schema: 'Structured Output',
  tool_calling: 'Tool Calling',
  reasoning: 'Reasoning',
  supports_temperature: 'Temperature',
  supports_top_p: 'Top P',
  supports_max_tokens: 'Max tokens',
  diarization: 'Diarization',
  keyterms: 'Keyterms',
  reasoning_effort_options: 'Reasoning effort',
  vector_size: 'Vector size',
}

const GROUP_LABELS: Record<FillGroup, string> = {
  description: 'Description',
  configuration: 'Capabilities',
  pricing: 'Pricing',
}

/**
 * Capabilities as labelled rows of tags: what the model supports, what it
 * doesn't, then each capability with values (reasoning effort, vector size).
 */
const capabilities = computed(
  () =>
    new Map(
      found.value.map(({ target, result }) => {
        const { flags, values } = capabilityItems(result, target.type)
        const labelOf = (key: string) => FLAG_LABELS[key] ?? key
        const rows: CapabilityRow[] = [
          { key: 'supported', label: 'Supported', items: flags.filter((f) => f.on).map((f) => labelOf(f.key)), tone: 'brand' },
          { key: 'unsupported', label: 'Not supported', items: flags.filter((f) => !f.on).map((f) => labelOf(f.key)), tone: 'muted' },
          ...values.map(({ key, items }): CapabilityRow => ({ key, label: labelOf(key), items, tone: 'neutral' })),
        ]
        return [target.key, rows.filter((row) => row.items.length > 0)]
      })
    )
)

function capabilityRows(key: string): CapabilityRow[] {
  return capabilities.value.get(key) ?? []
}

function nameOf(target: FillTarget): string {
  return target.display_name || target.ai_model
}

function foundLabel(target: FillTarget, result: ExtractedModel): string {
  return isNameMatch(target, result.matched_name) ? 'Found' : `Found as ${result.matched_name ?? ''}`
}
</script>

<style scoped>
.review-model {
  overflow: hidden;
  border-radius: 8px;
  transition: background-color 0.15s ease-out;
}
.review-model[data-state='skipped'] {
  background-color: var(--q-background);
}
.review-model__head {
  border-block-end: 1px solid var(--q-border);
}
.review-model[data-state='skipped'] .review-model__head {
  border-block-end: 0;
}
.review-model__names {
  min-inline-size: 0;
}
.review-model__name {
  font-weight: 600;
  overflow-wrap: anywhere;
}
.review-model__id {
  font-family: monospace;
  font-size: 12px;
  color: var(--q-secondary-text);
  overflow-wrap: anywhere;
}
/* Continues the header, which drops its border when skipped. */
.review-model__skipped {
  padding: 0 16px 16px;
  font-size: 12px;
  color: var(--q-secondary-text);
}
.review-model__groups > * + * {
  border-block-start: 1px solid var(--q-border);
}
.review-model__description {
  line-height: 1.6;
  overflow-wrap: anywhere;
}

/* Label column, then the tags; labels line up across rows. */
.review-caps {
  display: grid;
  grid-template-columns: max-content minmax(0, 1fr);
  gap: 8px 24px;
  align-items: baseline;
  margin: 0;
}
.review-caps__label {
  font-size: 13px;
  color: var(--q-secondary-text);
}
.review-caps__values {
  margin: 0;
}
.review-caps__values .q-chip {
  margin: 0;
}

.review-banner {
  background: var(--q-warning-bg, #fff8e1);
}

.review-missing {
  border-radius: 8px;
}
.review-missing__title {
  font-weight: 500;
}
</style>
